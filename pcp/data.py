"""Versioned structure preparation. Targets are separate from the inference object."""
from __future__ import annotations
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from Bio import Align
from Bio.PDB import MMCIFParser, PDBParser
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.SeqUtils import seq1
from scipy.spatial import cKDTree
from .io import atomic_json, download, sha256, manifest

PREPROCESS_VERSION = "residue-v2"
AA = "ACDEFGHIKLMNPQRSTVWYX"


@dataclass(frozen=True)
class ApoInput:
    x: np.ndarray
    coords: np.ndarray
    edges: np.ndarray
    edge_attr: np.ndarray
    residue_ids: np.ndarray
    sequence: str


def parse_structure(path, chain_id, min_residues=8):
    parser = MMCIFParser(QUIET=True) if str(path).endswith(".cif") else PDBParser(QUIET=True)
    model = parser.get_structure("protein", str(path))[0]
    positions = {}
    if str(path).endswith(".cif"):
        cif = MMCIF2Dict(str(path))
        for ch, num, ins, pos in zip(cif["_atom_site.auth_asym_id"], cif["_atom_site.auth_seq_id"],
                                     cif["_atom_site.pdbx_PDB_ins_code"], cif["_atom_site.label_seq_id"]):
            if ch == chain_id and pos not in (".", "?"):
                positions[f"{ch}_{num}{'' if ins in ('.','?') else ins}"] = int(pos)
    if chain_id not in model:
        raise ValueError(f"missing author chain {chain_id}")
    residues = []
    for r in model[chain_id]:
        if r.id[0] != " " or "CA" not in r:
            continue  # Explicit single standard-polymer-chain protocol.
        atoms = {}
        for a in r:
            if a.is_disordered():
                # deterministic highest occupancy, lexical altloc tie break
                a = sorted(a.disordered_get_list(), key=lambda q: (-(q.occupancy or 0), q.altloc))[0]
            atoms[a.name] = np.asarray(a.coord, dtype=np.float32)
        letter = seq1(r.resname, undef_code="X")
        rid = f"{chain_id}_{r.id[1]}{r.id[2].strip()}"
        if positions and rid not in positions:
            raise ValueError(f"no polymer sequence position for {rid}")
        residues.append({"id": rid, "seqpos": positions.get(rid, r.id[1]),
                         "aa": letter, "atoms": atoms})
    if len(residues) < min_residues:
        raise ValueError(f"fewer than {min_residues} resolved CA residues")
    return residues, model


def apo_features(residues):
    ca = np.stack([r["atoms"]["CA"] for r in residues])
    n = len(ca)
    seqpos = np.array([r.get("seqpos", i) for i,r in enumerate(residues)])
    tree = cKDTree(ca)
    pairs = set(tree.query_pairs(12.0))
    # Capped spatial neighbors within 16 A plus local sequence edges.
    distances, neighbors = tree.query(ca, k=min(17, n), distance_upper_bound=16.0)
    for i in range(n):
        for j in neighbors[i]:
            if j < n and i != j:
                pairs.add(tuple(sorted((i, int(j)))))
        for j in range(i + 1, min(i + 3, n)):
            if abs(seqpos[j]-seqpos[i]) <= 2:
                pairs.add((i, j))
    # Radius edges are capped per node to bound density in large assemblies.
    candidates = sorted(pairs, key=lambda ij: (float(np.linalg.norm(ca[ij[0]] - ca[ij[1]])), ij))
    degree = np.zeros(n, int)
    kept = []
    for i, j in candidates:
        if abs(seqpos[j]-seqpos[i]) <= 2 or (degree[i] < 48 and degree[j] < 48):
            kept.append((i, j)); degree[i] += 1; degree[j] += 1
    edges = np.asarray(sorted(kept), dtype=np.int64).T
    i, j = edges
    dist = np.linalg.norm(ca[i] - ca[j], axis=1)
    separation = np.abs(seqpos[j]-seqpos[i])
    edge_attr = np.stack([dist / 16, np.exp(-dist / 8),
                          np.minimum(separation, 100) / 100, (separation <= 2).astype(float)], axis=1).astype(np.float32)
    identity = np.eye(len(AA), dtype=np.float32)[[AA.index(r["aa"] if r["aa"] in AA else "X") for r in residues]]
    counts = np.stack([np.array([len(v) - 1 for v in tree.query_ball_point(ca, rad)]) / 50 for rad in (6, 10, 14)], axis=1)
    # Rotation/translation invariant local CA bend plus backbone lengths and masks.
    geom = np.zeros((n, 7), np.float32)
    left, right = ca[:-2] - ca[1:-1], ca[2:] - ca[1:-1]
    geom[1:-1, 0] = np.sum(left * right, axis=1) / np.maximum(np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1), 1e-6)
    geom[1:-1, 0] *= ((seqpos[1:-1]-seqpos[:-2] == 1) & (seqpos[2:]-seqpos[1:-1] == 1))
    for k, r in enumerate(residues):
        for col, atom in enumerate(("N", "C", "O")):
            if atom in r["atoms"]:
                geom[k, 1 + col] = np.linalg.norm(r["atoms"][atom] - ca[k]) / 4
                geom[k, 4 + col] = 1
    return ApoInput(np.concatenate([identity, counts, geom], axis=1).astype(np.float32),
                    ca, edges, edge_attr, np.array([r["id"] for r in residues]),
                    "".join(r["aa"] for r in residues))


def contact_targets(apo_res, holo_res, apo):
    aseq, hseq = apo.sequence, "".join(r["aa"] for r in holo_res)
    aligner = Align.PairwiseAligner(mode="global", match_score=2, mismatch_score=-1,
                                   open_gap_score=-5, extend_gap_score=-0.5)
    alignment = aligner.align(aseq, hseq)[0]
    mapping = {}
    for (a0, a1), (h0, h1) in zip(*alignment.aligned):
        for a, h in zip(range(a0, a1), range(h0, h1)):
            if aseq[a] == hseq[h] and aseq[a] != "X":
                mapping[a] = h
    def cb(r):
        return r["atoms"].get("CA" if r["aa"] == "G" else "CB")
    valid = np.array([i in mapping and cb(r) is not None and cb(holo_res[mapping[i]]) is not None for i, r in enumerate(apo_res)])
    acb = np.stack([cb(r) if cb(r) is not None else r["atoms"]["CA"] for r in apo_res])
    hcb = np.stack([cb(holo_res[mapping[i]]) if valid[i] else acb[i] for i in range(len(apo_res))])
    i, j = apo.edges
    ap = np.array([r.get("seqpos", k) for k,r in enumerate(apo_res)])
    hp = np.array([holo_res[mapping[k]].get("seqpos", mapping[k]) if k in mapping else -100000 for k in range(len(apo_res))])
    mask = valid[i] & valid[j] & (np.abs(ap[j]-ap[i]) > 2) & (np.abs(hp[j]-hp[i]) > 2)
    ac = np.linalg.norm(acb[i] - acb[j], axis=1) < 8
    hc = np.linalg.norm(hcb[i] - hcb[j], axis=1) < 8
    labels = np.stack([~ac & hc, ac & ~hc], axis=1).astype(np.float32)
    labels[~mask] = 0
    # Count all resolved formed contacts, including those absent from apo candidates.
    all_holo = cKDTree(hcb).query_pairs(8)
    formed = {(u, v) for u, v in all_holo if valid[u] and valid[v] and abs(ap[v]-ap[u]) > 2 and abs(hp[v]-hp[u]) > 2 and np.linalg.norm(acb[u]-acb[v]) >= 8}
    covered = len(formed & set(map(tuple, apo.edges.T)))
    return labels, mask, {"mapped_residues": int(valid.sum()), "formed_total": len(formed),
                          "formed_covered": covered, "mapping": {str(k): v for k, v in mapping.items()}}


def fetch_metadata(root):
    root = Path(root)
    for name, url in {"dataset.json": "https://osf.io/download/ta2ju/", "folds.json": "https://osf.io/download/5s93p/"}.items():
        download(url, root / "raw" / name)
    return (json.loads((root/"raw/dataset.json").read_text()), json.loads((root/"raw/folds.json").read_text()))


def prepare(root="data", limit=24):
    root = Path(root)
    dataset, folds = fetch_metadata(root)
    fold_sets = {k: set(v) for k, v in folds.items()}
    for k, a in fold_sets.items():
        for l, b in fold_sets.items():
            if k != l and a & b:
                raise ValueError(f"official folds overlap: {k}, {l}")
    # Validation is an official TRAINING fold, never official test.
    train_ids = sorted(set().union(*(v for k, v in fold_sets.items() if k not in ("test", "train-0"))))[:limit]
    val_ids = sorted(fold_sets["train-0"])[:max(4, limit // 3)]
    out = root / f"prepared-{limit}"
    out.mkdir(parents=True, exist_ok=True)
    records, failures = [], []
    for split, ids in (("train", train_ids), ("val", val_ids)):
        for pdb_id in ids:
            # One main pair per apo, deterministic choice before outcome inspection.
            entries = [p for p in dataset[pdb_id] if p.get("is_main_holo_structure")]
            entries = sorted(entries or dataset[pdb_id], key=lambda p: (p["apo_chain"], p["holo_pdb_id"], p["holo_chain"], str(p["ligand_index"])))
            p = entries[0]
            pid = pdb_id + p["apo_chain"]
            try:
                apath = download(f"https://files.rcsb.org/download/{pdb_id}.cif", root / "raw" / f"{pdb_id}.cif")
                hpath = download(f"https://files.rcsb.org/download/{p['holo_pdb_id']}.cif", root / "raw" / f"{p['holo_pdb_id']}.cif")
                ar, _ = parse_structure(apath, p["apo_chain"])
                hr, hm = parse_structure(hpath, p["holo_chain"])
                if len(ar) > 1500:
                    raise ValueError("debug length cap 1500; excluded explicitly")
                # Verify the curated ligand, never use all HETATM/protein atoms as ligand.
                ligand = [r for r in hm[p["ligand_chain"]] if r.id[0] != " " and r.resname == p["ligand"] and f"{r.id[1]}{r.id[2].strip()}" == str(p["ligand_index"])]
                if len(ligand) != 1:
                    raise ValueError("curated ligand identity not uniquely resolved")
                apo = apo_features(ar)
                # Union official annotations on selected apo chain for pocket targets.
                positives = set().union(*(set(q["apo_pocket_selection"]) for q in dataset[pdb_id] if q["apo_chain"] == p["apo_chain"]))
                y = np.array([r in positives for r in apo.residue_ids], dtype=np.float32)
                if y.sum() == 0:
                    raise ValueError("no mapped official positives")
                contacts, cmask, audit = contact_targets(ar, hr, apo)
                if audit["mapped_residues"] / len(ar) < 0.8:
                    raise ValueError("under 80% matching resolved contact positions")
                key_info = {"apo_sha": sha256(apath), "holo_sha": sha256(hpath), "version": PREPROCESS_VERSION,
                            "pair": p, "labels": sorted(positives), "if_checkpoint": None, "if_settings": None}
                key = hashlib.sha256(json.dumps(key_info, sort_keys=True).encode()).hexdigest()
                path = out / f"{pid}-{key[:12]}.npz"
                with open(str(path) + ".tmp", "wb") as f:
                    np.savez_compressed(f, x=apo.x, coords=apo.coords, edges=apo.edges, edge_attr=apo.edge_attr,
                                        residue_ids=apo.residue_ids, sequence=apo.sequence, y=y,
                                        contact_y=contacts, contact_mask=cmask)
                os.replace(str(path) + ".tmp", path)
                record = {"id": pid, "apo_id": pdb_id, "split": split, "path": path.as_posix(),
                          "sha256": sha256(path), "cache_key": key, "sequence": apo.sequence,
                          "uniprot": p["uniprot_id"], "length": len(y), "positives": int(y.sum()),
                          "shard": int(hashlib.sha256(pid.lower().encode()).hexdigest()[:8], 16) % 32,
                          "source": key_info, "contact_audit": audit,
                          "unmapped_positive_ids": sorted(positives - set(apo.residue_ids))}
                records.append(record)
                print(f"prepared {split} {pid} N={len(y)} positives={int(y.sum())}", flush=True)
            except Exception as exc:
                failures.append({"id": pid, "split": split, "error": str(exc)})
                print(f"excluded {pid}: {exc}", flush=True)
            atomic_json(out / "index.partial.json", {"records": records, "failures": failures})
    train_uniprot = {r["uniprot"] for r in records if r["split"] == "train"}
    overlap = [r["id"] for r in records if r["split"] == "val" and r["uniprot"] in train_uniprot]
    index = {"protocol": "development subset; official train-0 validation; other train folds training",
             "official_folds_sha256": sha256(root/"raw/folds.json"), "dataset_sha256": sha256(root/"raw/dataset.json"),
             "locked_test_enabled": False, "family_audit": "pending sequence clustering/CATH and prior-exposure IDs",
             "uniprot_overlap": overlap, "records": records, "failures": failures}
    atomic_json(out/"index.json", index)
    atomic_json("SPLITS.json", {k: v for k, v in index.items() if k not in ("records", "failures")} | {
        "train": [r["id"] for r in records if r["split"] == "train"],
        "val": [r["id"] for r in records if r["split"] == "val"], "test": []})
    manifest("prepare_complete", index=str(out/"index.json"), index_sha256=sha256(out/"index.json"),
             successful=len(records), excluded=len(failures))
    return out / "index.json"


def load_records(index_path):
    index = json.loads(Path(index_path).read_text())
    if index["uniprot_overlap"]:
        raise ValueError("training/validation UniProt overlap; audit before fitting")
    result = []
    for r in index["records"]:
        if sha256(r["path"]) != r["sha256"]:
            raise ValueError(f"changed prepared shard: {r['path']}")
        with np.load(r["path"], allow_pickle=False) as z:
            result.append((r, {k: z[k] for k in z.files}))
    return result
