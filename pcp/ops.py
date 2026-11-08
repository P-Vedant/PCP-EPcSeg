import json
import time
from pathlib import Path
import numpy as np
import torch
from .data import apo_features, parse_structure, load_records, PREPROCESS_VERSION
from .ablations import apply_controls
from .io import atomic_json, hardware, sha256, manifest
from .model import RegionalPocket, loss_fn
from .train import tensors, evaluate


def profile(index, out):
    records = sorted(load_records(index), key=lambda rz: len(rz[1]["x"]))
    results = []
    torch.set_num_threads(4)
    for ix in sorted(set([0, len(records)//2, len(records)-1])):
        r,z = records[ix]
        model = RegionalPocket().cuda()
        opt = torch.optim.AdamW(model.parameters())
        inputs, target = tensors(z, "cuda", 0, 1)
        weights = (torch.tensor(1., device="cuda"), torch.ones(2, device="cuda"))
        def step():
            opt.zero_grad(set_to_none=True)
            loss = loss_fn(model(inputs), target, inputs["edges"], weights, model.mode)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5, error_if_nonfinite=True)
            opt.step()
        for _ in range(5): step()
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
        start = time.perf_counter()
        for _ in range(20): step()
        torch.cuda.synchronize()
        results.append({"id":r["id"], "residues":len(z["x"]), "edges":z["edges"].shape[1],
                        "seconds_per_step":(time.perf_counter()-start)/20,
                        "peak_allocated_bytes":torch.cuda.max_memory_allocated(),
                        "peak_reserved_bytes":torch.cuda.max_memory_reserved(),
                        "parameters":sum(p.numel() for p in model.parameters())})
        del model, opt, inputs, target
        torch.cuda.empty_cache()
    result = {"hardware":hardware(), "warmup":5, "measured_steps":20, "microbatch":1, "precision":"float32", "results":results,
              "caveat":"Measured local 5070 Laptop only; RTX 3070 execution unverified"}
    atomic_json(out, result); manifest("profile", path=out, sha256=sha256(out))
    return result


def load_model(checkpoint, device):
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model = RegionalPocket(**state["config"]["model"]).to(device)
    model.load_state_dict(state["model"]); model.eval()
    return model, state


def infer(structure, chain, sequence_file, checkpoint, out, device):
    preprocess_start = time.perf_counter()
    model, state = load_model(checkpoint, device)
    if state["config"].get("shuffle_if") or state["config"].get("energy_values") == "zero":
        raise ValueError("diagnostic shuffled/missingness-only checkpoints are not deployment models")
    residues, _ = parse_structure(structure, chain)
    apo = apo_features(residues)
    sequence = "".join(line.strip() for line in Path(sequence_file).read_text().splitlines() if not line.startswith(">"))
    # Require the resolved chain sequence exactly; full-sequence mapping is a separate preparation step.
    if sequence != apo.sequence:
        raise ValueError("FASTA must match the resolved selected chain; map missing positions explicitly first")
    z = {"x":apo.x,"edges":apo.edges,"edge_attr":apo.edge_attr}
    feature_provenance = {}
    if model.use_if or model.use_energy:
        import hashlib
        key=hashlib.sha256((sha256(structure)+chain+sha256(sequence_file)+PREPROCESS_VERSION).encode()).hexdigest()
        cache=Path("cache/inference")/key
        cache.mkdir(parents=True,exist_ok=True)
        source=cache/"apo-only.npz"
        if not source.exists():
            with open(str(source)+".tmp","wb") as f:
                np.savez_compressed(f,**z,coords=apo.coords,residue_ids=apo.residue_ids,sequence=apo.sequence)
            import os
            os.replace(str(source)+".tmp",source)
        if model.use_if:
            from .features import extract_mpnn
            input_index=cache/"apo-only.json"
            atomic_json(input_index,{"records":[{"id":"apo-inference","apo_id":Path(structure).stem,
                        "apo_path":str(Path(structure).resolve()),"path":str(source),"sha256":sha256(source),"shard":0}]})
            feature_index=extract_mpnn(input_index,cache/"mpnn",device=device)
            record=json.loads(feature_index.read_text())["records"][0]
            if "if_provenance" not in record:
                raise RuntimeError("apo-only ProteinMPNN extraction failed; inspect feature-progress.json")
            with np.load(record["path"],allow_pickle=False) as f:
                z.update(if_features=f["if_features"],if_mask=f["if_mask"])
            feature_provenance["mpnn"]=record["if_provenance"]
        if model.use_energy:
            from .energy import score_context
            from . import energy as energy_module
            import openmm
            path=cache/f"energy-{sha256(energy_module.__file__)[:12]}-{openmm.__version__}.json"
            result=json.loads(path.read_text()) if path.exists() else score_context(structure,path,True)
            values=np.zeros((len(apo.x),3),np.float32); mask=np.zeros((len(apo.x),1),np.float32)
            if result["openmm"]["valid"]:
                force=result["openmm"]["residue_mean_force"]
                for i,rid in enumerate(apo.residue_ids):
                    if str(rid) in force:
                        values[i]=[np.log1p(result["clash_counts"].get(str(rid),0)),np.log1p(force[str(rid)]),0]
                        mask[i]=1
            z.update(energy=values,energy_mask=mask)
            feature_provenance["energy"]={"path":str(path),"sha256":sha256(path),"valid":result["openmm"]["valid"]}
    inputs, _ = tensors(z, device, state["mean"], state["std"])
    preprocess_seconds = time.perf_counter()-preprocess_start
    start = time.perf_counter()
    with torch.no_grad(): pred = model(inputs)
    if device.startswith("cuda"): torch.cuda.synchronize()
    model_seconds = time.perf_counter()-start
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, scores=pred["pocket_logits"].sigmoid().cpu().numpy(),
                        contacts=pred["contact_logits"].sigmoid().cpu().numpy(),
                        regions=pred["regions"].cpu().numpy(), residue_ids=apo.residue_ids,
                        edges=apo.edges, coords=apo.coords)
    atomic_json(out+".json", {"structure_sha256":sha256(structure), "sequence_sha256":sha256(sequence_file),
                              "checkpoint_sha256":sha256(checkpoint), "chain":chain,
                              "preprocessing_seconds":preprocess_seconds,"model_forward_seconds":model_seconds,
                              "cached_feature_provenance":feature_provenance,
                              "input_protocol":"single resolved chain; apo only; no holo/ligand/targets"})


def evaluate_checkpoint(index, checkpoint, out, split):
    metadata = json.loads(Path(index).read_text())
    if split == "test":
        raise ValueError("Locked test evaluation is disabled until exposure/family audit and frozen configuration approval are recorded")
    model, state = load_model(checkpoint, "cpu")
    if sha256(index) != state["index_sha256"]:
        raise ValueError("checkpoint data index differs")
    rows = [(r,z) for r,z in apply_controls(load_records(index),state["config"]) if r["split"]==split]
    result = evaluate(model, rows, "cpu", state["mean"], state["std"], Path(out).parent/"eval-predictions")
    atomic_json(out, result)
