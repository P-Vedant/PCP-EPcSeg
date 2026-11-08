"""Execute checkpoint portability/inference and transfer integrity on real prepared data."""
from pathlib import Path
import json
import numpy as np
from pcp.io import atomic_json,sha256
from pcp.ops import infer,evaluate_checkpoint
from pcp.transfer import export_bundle,import_bundle

index="data/prepared-24/index.json"
record=json.loads(Path(index).read_text())["records"][0]
with np.load(record["path"],allow_pickle=False) as z:
    sequence=str(z["sequence"])
Path("outputs").mkdir(exist_ok=True)
Path("outputs/resolved-chain.fasta").write_text(">resolved\n"+sequence+"\n")
checkpoint="runs/dev24-regional-s17/best.pt"
infer(f"data/raw/{record['apo_id']}.cif",record["source"]["pair"]["apo_chain"],"outputs/resolved-chain.fasta",checkpoint,"outputs/apo-inference.npz","cpu")
evaluate_checkpoint(index,checkpoint,"outputs/cpu-validation.json","val")
bundle=export_bundle([checkpoint,index,record["path"]],"outputs/dev24-transfer.zip")
imported=import_bundle(bundle["archive"],"outputs/transfer-check")
assert sha256(checkpoint)==sha256(Path(imported["destination"])/checkpoint)
atomic_json("outputs/artifact-checks.json",{"gpu_checkpoint_cpu_inference":True,"validation_recomputed_cpu":True,"bundle":bundle,"imported":imported,
                                          "cross_gpu":"not executed; partner unavailable"})
print(json.dumps(bundle))
