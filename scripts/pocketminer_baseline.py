"""Official frozen PocketMiner checkpoint, with explicit mmCIF residue mapping.

Run in .venv-pocketminer (TensorFlow 2.15.1/Keras2). No training or test access.
Input tensors follow author process_strucs: N,CA,C,O in nanometers, author AA order.
Adaptation: selected author chain and incomplete-backbone masks instead of MDTraj
reshape, which cannot preserve our mmCIF residue mapping on incomplete structures.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
root=Path(__file__).resolve().parents[1]
os.chdir(root)
os.environ["CUDA_VISIBLE_DEVICES"]="-1"
os.environ["TF_CPP_MIN_LOG_LEVEL"]="2"
os.environ["TF_NUM_INTRAOP_THREADS"]="4"
os.environ["TF_NUM_INTEROP_THREADS"]="2"
sys.path.insert(0,str(root))
sys.path.insert(0,str(root/"external/PocketMiner/src"))
import numpy as np
import tensorflow as tf
from models import MQAModel
from pcp.data import parse_structure
from pcp.metrics import evaluate_predictions
from pcp.io import atomic_json,sha256,manifest,revision

parser=argparse.ArgumentParser()
parser.add_argument("--index",default="data/prepared-24/index.json")
parser.add_argument("--out",default="runs/dev24-pocketminer")
parser.add_argument("--cohort",default="dev24")
args=parser.parse_args()
out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
index=json.loads(Path(args.index).read_text())
lookup={a:i for i,a in enumerate("ARNDCQEGHILKMFPSTWYV")}
model=MQAModel(node_features=(8,50),edge_features=(1,32),hidden_dim=(16,100),num_layers=4,dropout=.1)
checkpoint="external/PocketMiner/models/pocketminer"
loaded=False; rows=[]; failures=[]; matched={}; start=time.perf_counter()
provenance={"official_revision":"187062df3c94127e991669768009141a08fd5d8b","adapter_commit":revision(),
            "tensorflow":tf.__version__,"index_sha256":sha256(args.index),
            "weights_sha256":sha256(checkpoint+".data-00000-of-00001"),
            "preprocessing":"selected author chain, N/CA/C/O in nm; unknown/incomplete backbone masked; no target data",
            "official_model_weights_unchanged":True,"license":"MIT (retained in external/PocketMiner/LICENSE)",
            "caveat":"pretraining overlap unknown; adapted preprocessing, not a claim of exact published benchmark reproduction"}
atomic_json(out/"provenance.json",provenance)
for record in index["records"]:
    if record["split"]!="val": continue
    try:
        residues,_=parse_structure(Path("data/raw")/f"{record['apo_id']}.cif",record["source"]["pair"]["apo_chain"])
        with np.load(record["path"],allow_pickle=False) as z:
            ids=z["residue_ids"]; y=z["y"]
        if list(ids)!=[r["id"] for r in residues]: raise ValueError("residue mapping mismatch")
        n=len(residues); x=np.zeros((1,n,4,3),np.float32); seq=np.zeros((1,n),np.int32); mask=np.zeros((1,n),np.float32)
        for i,r in enumerate(residues):
            if r["aa"] in lookup and all(k in r["atoms"] for k in ("N","CA","C","O")):
                x[0,i]=np.stack([r["atoms"][k] for k in ("N","CA","C","O")])*.1
                seq[0,i]=lookup[r["aa"]]; mask[0,i]=1
        if not loaded:
            model(x,seq,mask,train=False,res_level=True)
            # Author util.save_checkpoint uses .write(), so pair it with .read().
            # Unlike restore(), read() does not require a synthetic save_counter.
            status=tf.train.Checkpoint(model=model).read(checkpoint)
            status.assert_existing_objects_matched()
            status.expect_partial()  # Only checkpoint optimizer slots are intentionally unused.
            loaded=True
        t=time.perf_counter(); scores=np.asarray(model(x,seq,mask,train=False,res_level=True)).reshape(-1)
        infer_seconds=time.perf_counter()-t
        valid=mask[0].astype(bool)
        if not np.isfinite(scores[valid]).all(): raise FloatingPointError("nonfinite predictions")
        np.savez_compressed(out/f"{record['id']}.npz",scores=scores,mask=valid,residue_ids=ids,y=y)
        rows.append({"id":record["id"],"y":y[valid],"scores":scores[valid]})
        # Compare every completed development method on exactly the same mask/rows.
        for name,path in {
            "forest":Path(f"runs/{args.cohort}-baseline-s17")/f"forest-{record['id']}.npz",
            "regional":Path(f"runs/{args.cohort}-regional-s17/predictions")/f"{record['id']}.npz",
            "if-regional":Path(f"runs/{args.cohort}-if-regional-s17/predictions")/f"{record['id']}.npz"}.items():
            if path.exists():
                with np.load(path,allow_pickle=False) as z: p=z["scores"]
                matched.setdefault(name,[]).append({"id":record["id"],"y":y[valid],"scores":p[valid]})
        print(f"PocketMiner {record['id']} valid={valid.sum()}/{n} seconds={infer_seconds:.3f}",flush=True)
    except Exception as exc:
        failures.append({"id":record["id"],"error":str(exc)})
        print(f"PocketMiner failure {record['id']}: {exc}",flush=True)
        if not loaded: break  # Do not score an unverified checkpoint.
    atomic_json(out/"progress.json",{"completed":[r["id"] for r in rows],"failures":failures})
if not rows: raise RuntimeError(f"No verified predictions: {failures}")
result={"PocketMiner":evaluate_predictions(rows),"matched":{k:evaluate_predictions(v) for k,v in matched.items()},
        "failures":failures,"total_seconds":time.perf_counter()-start,"checkpoint_restore_verified":loaded}
atomic_json(out/"metrics.json",result)
manifest("pocketminer_complete",run=str(out),metrics_sha256=sha256(out/"metrics.json"),
         macro_ap=result["PocketMiner"]["macro_ap"],n_proteins=len(rows),failures=failures)
print(json.dumps({"PocketMiner_macro_ap":result["PocketMiner"]["macro_ap"],"matched":{k:v["macro_ap"] for k,v in result["matched"].items()}}))
