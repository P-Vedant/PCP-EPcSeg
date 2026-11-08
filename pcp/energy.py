"""Context-preserving descriptors; failures are explicit and never delete cofactors."""
import json
import time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .io import sha256, atomic_json


def score_context(structure, output, use_openmm=False):
    from Bio.PDB import MMCIFParser, PDBParser
    parser=MMCIFParser(QUIET=True) if str(structure).endswith(".cif") else PDBParser(QUIET=True)
    model=parser.get_structure("apo",structure)[0]
    atoms=[a for a in model.get_atoms() if a.element not in ("H","D")]
    coords=np.array([a.coord for a in atoms])
    ids=[f"{a.get_parent().get_parent().id}_{a.get_parent().id[1]}{a.get_parent().id[2].strip()}" for a in atoms]
    counts={rid:0 for rid in ids}
    # A bounded geometric overlap proxy; excludes same/adjacent polymer residues.
    for i,j in cKDTree(coords).query_pairs(2.0):
        ri,rj=atoms[i].get_parent(),atoms[j].get_parent()
        if ids[i]==ids[j]: continue
        if ri.get_parent().id==rj.get_parent().id and abs(ri.id[1]-rj.id[1])<=1: continue
        counts[ids[i]]+=1; counts[ids[j]]+=1
    result={"structure_sha256":sha256(structure),"context":"whole first model, all chains/cofactors retained",
            "clash_proxy":"heavy atom distance <2 A, excluding same/adjacent residues; not a force-field energy",
            "clash_counts":counts,"openmm":{"valid":False,"failure":"not_requested"}}
    if use_openmm:
        start=time.monotonic()
        try:
            import openmm
            from openmm import app,unit
            raw=app.PDBxFile(str(structure)) if str(structure).endswith(".cif") else app.PDBFile(str(structure))
            ff=app.ForceField("amber14-all.xml","implicit/obc2.xml")
            mod=app.Modeller(raw.topology,raw.positions)
            removed_waters=sum(r.name in ("HOH","WAT") for r in mod.topology.residues())
            # Explicit solvent policy: crystallographic waters are replaced by OBC2.
            # Protein chains, ions, cofactors and nonwater ligands are never removed.
            mod.deleteWater()
            result["solvent_policy"]={"model":"OBC2 implicit", "removed_crystallographic_waters":removed_waters,
                                      "limitation":"specific bound-water interactions are omitted"}
            # No cofactor/metal deletion or missing-heavy-atom guessing to force success.
            mod.addHydrogens(ff,pH=7.0)
            system=ff.createSystem(mod.topology,nonbondedMethod=app.NoCutoff,constraints=app.HBonds)
            integrator=openmm.VerletIntegrator(.001*unit.picoseconds)
            context=openmm.Context(system,integrator,openmm.Platform.getPlatformByName("CPU"),{"Threads":"4"})
            context.setPositions(mod.positions)
            state=context.getState(getEnergy=True,getForces=True)
            forces=np.asarray(state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer))
            pooled={}
            for atom,force in zip(mod.topology.atoms(),forces):
                rid=f"{atom.residue.chain.id}_{atom.residue.id}{atom.residue.insertionCode}"
                pooled.setdefault(rid,[]).append(float(np.linalg.norm(force)))
            potential=float(state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
            if not np.isfinite(potential) or not np.isfinite(forces).all(): raise FloatingPointError("nonfinite energy/force")
            result["openmm"]={"valid":True,"version":openmm.__version__,"force_field":"amber14-all + implicit/obc2",
                              "pH":7.0,"units":{"potential":"kJ/mol","force":"kJ/mol/nm"},"potential":potential,
                              "residue_mean_force":{k:float(np.mean(v)) for k,v in pooled.items()},
                              "preparation":"replace crystal waters with implicit solvent; add hydrogens; no minimization/heavy-atom repair; standard termini",
                              "warning":"forces are strain proxies, not local energies; no population inference"}
            del context,integrator
        except Exception as exc:
            result["openmm"]={"valid":False,"failure":str(exc)}
        result["openmm"]["seconds"]=time.monotonic()-start
    atomic_json(output,result)
    return result


def extract_energy(index_path,output):
    import hashlib
    import os
    from .io import manifest
    out=Path(output); out.mkdir(parents=True,exist_ok=True)
    index=json.loads(Path(index_path).read_text()); records=[]; coverage=[]
    for original in index["records"]:
        r=dict(original)
        structure=Path("data/raw")/f"{r['apo_id']}.cif"
        settings={"adapter_sha256":sha256(__file__),"structure_sha256":sha256(structure),
                  "prepared_sha256":r["sha256"],"force_field":"amber14-all/implicit-obc2","pH":7.0,"remove_water":True}
        key=hashlib.sha256(json.dumps(settings,sort_keys=True).encode()).hexdigest()
        result_path=out/f"{r['id']}-{key[:12]}.energy.json"
        result=json.loads(result_path.read_text()) if result_path.exists() else score_context(structure,result_path,True)
        with np.load(r["path"],allow_pickle=False) as z: arrays={k:z[k] for k in z.files}
        values=np.zeros((len(arrays["x"]),3),np.float32); mask=np.zeros((len(values),1),np.float32)
        if result["openmm"]["valid"]:
            forces=result["openmm"]["residue_mean_force"]
            for i,rid in enumerate(arrays["residue_ids"]):
                if str(rid) in forces:
                    # Fixed physical transforms, not label-derived or fitted on test.
                    values[i]=[np.log1p(result["clash_counts"].get(str(rid),0)), np.log1p(forces[str(rid)]), 0]
                    mask[i]=1
        arrays.update(energy=values,energy_mask=mask)
        path=out/f"{r['id']}-{key[:12]}.npz"
        with open(str(path)+".tmp","wb") as f: np.savez_compressed(f,**arrays)
        os.replace(str(path)+".tmp",path)
        r.update(path=path.as_posix(),sha256=sha256(path),cache_key=key,energy_provenance=settings)
        records.append(r)
        coverage.append({"id":r["id"],"split":r["split"],"uniprot":r["uniprot"],"positives":r["positives"],
                         "length":r["length"],"valid_residues":int(mask.sum()),"valid":result["openmm"]["valid"],
                         "failure":result["openmm"].get("failure")})
        atomic_json(out/"coverage.json",coverage)
        print(f"energy {r['id']} valid={result['openmm']['valid']}",flush=True)
    index["records"]=records; index["energy_coverage"]=coverage
    atomic_json(out/"index.json",index)
    manifest("energy_complete",index=str(out/"index.json"),index_sha256=sha256(out/"index.json"),valid_proteins=sum(r["valid"] for r in coverage),total=len(coverage))
    return out/"index.json"
