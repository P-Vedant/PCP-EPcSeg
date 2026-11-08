"""Frozen whole-context inverse-folding features, atomically cached by provenance."""
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path
import numpy as np
import torch
from Bio.PDB import MMCIFParser
from .data import AA, parse_structure
from .io import sha256, atomic_json, manifest

MPNN_REVISION = "8907e6671bfbfc92303b5f79c4b5e6ce47cdef57"


def extract_mpnn(index_path, output, external="external/ProteinMPNN", device="cuda", shard=None):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    index = json.loads(Path(index_path).read_text())
    ext = Path(external)
    checkpoint = ext/"vanilla_model_weights/v_48_020.pt"
    spec = importlib.util.spec_from_file_location("official_protein_mpnn", ext/"protein_mpnn_utils.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    model = module.ProteinMPNN(num_letters=21, node_features=128, edge_features=128,
                              hidden_dim=128, num_encoder_layers=3, num_decoder_layers=3,
                              k_neighbors=state["num_edges"], augment_eps=0.0).to(device)
    model.load_state_dict(state["model_state_dict"]); model.eval(); model.requires_grad_(False)
    torch.set_num_threads(4)
    processed, failures, updated = [], [], []
    settings = {"revision":MPNN_REVISION, "checkpoint_sha256":sha256(checkpoint),
                "code_sha256":sha256(ext/"protein_mpnn_utils.py"), "noise":0.0,
                "mode":"unconditional_probs", "context":"all resolved standard polymer chains; no cropping",
                "feature_order":"native_nll,entropy,21 AA probabilities in ACDEFGHIKLMNPQRSTVWYX order"}
    start = time.monotonic()
    for record in index["records"]:
        if shard is not None and record["shard"] != shard:
            updated.append(record); continue
        r = dict(record)
        try:
            path = Path("data/raw")/f"{r['apo_id']}.cif"
            provenance = {"apo_sha256":sha256(path), "prepared_sha256":r["sha256"], "settings":settings}
            key = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
            target = out/f"{r['id']}-{key[:12]}.npz"
            with np.load(r["path"], allow_pickle=False) as z:
                arrays = {k:z[k] for k in z.files}
            if not target.exists():
                structure = MMCIFParser(QUIET=True).get_structure("apo", path)[0]
                residues, encodings, positions = [], [], []
                for c, chain in enumerate(structure, 1):
                    if not any(q.id[0]==" " and "CA" in q for q in chain): continue
                    chain_res, _ = parse_structure(path, chain.id, min_residues=1)
                    residues.extend(chain_res)
                    encodings.extend([c]*len(chain_res))
                    positions.extend([q["seqpos"]+100*c for q in chain_res])
                n = len(residues)
                if n > 5000: raise ValueError("whole-context length >5000; extraction memory cap")
                x = np.zeros((1,n,4,3),np.float32); mask = np.zeros((1,n),np.float32)
                for i,q in enumerate(residues):
                    if all(a in q["atoms"] for a in ("N","CA","C","O")):
                        x[0,i] = np.stack([q["atoms"][a] for a in ("N","CA","C","O")]); mask[0,i]=1
                with torch.no_grad():
                    lp = model.unconditional_probs(torch.tensor(x,device=device), torch.tensor(mask,device=device),
                                                   torch.tensor([positions],device=device),torch.tensor([encodings],device=device))[0].cpu().numpy()
                lookup = {q["id"]:i for i,q in enumerate(residues)}
                indices = [lookup[str(rid)] for rid in arrays["residue_ids"]]
                native = [AA.index(residues[i]["aa"] if residues[i]["aa"] in AA else "X") for i in indices]
                selected = lp[indices]; prob = np.exp(selected)
                features = np.column_stack([-selected[np.arange(len(indices)),native], -(prob*selected).sum(1), prob]).astype(np.float32)
                valid = mask[0,indices,None]
                if not np.isfinite(features).all(): raise FloatingPointError("nonfinite MPNN features")
                arrays["if_features"] = features * valid; arrays["if_mask"] = valid
                with open(str(target)+".tmp","wb") as f: np.savez_compressed(f,**arrays)
                os.replace(str(target)+".tmp",target)
                atomic_json(str(target)+".json",provenance|{"context_residues":n,"valid_residues":int(valid.sum())})
            r.update(path=target.as_posix(), sha256=sha256(target), cache_key=key,
                     if_provenance=provenance)
            processed.append(r["id"])
            print(f"ProteinMPNN {r['id']}",flush=True)
        except Exception as exc:
            failures.append({"id":r["id"],"error":str(exc)})
            print(f"ProteinMPNN failed {r['id']}: {exc}",flush=True)
        updated.append(r)
        atomic_json(out/"feature-progress.json",{"processed":processed,"failures":failures})
    index["records"]=updated
    index["if_extraction"]={"settings":settings,"processed":processed,"failures":failures,"shard":shard,"seconds":time.monotonic()-start}
    target_index=out/(f"index-shard-{shard}.json" if shard is not None else "index.json")
    atomic_json(target_index,index)
    manifest("mpnn_complete",index=str(target_index),index_sha256=sha256(target_index),**index["if_extraction"])
    return target_index
