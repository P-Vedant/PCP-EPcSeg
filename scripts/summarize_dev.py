"""Regenerate a compact evidence table from actual immutable run artifacts."""
import json
import os
from pathlib import Path
import numpy as np
from pcp.io import atomic_json,sha256
os.chdir(Path(__file__).resolve().parents[1])
rows=[]
for path in sorted(Path("runs").glob("dev24*/metrics.json")):
    m=json.loads(path.read_text()); run=path.parent.name
    if "PocketMiner" in m:
        entries={"official PocketMiner (adapted mapping)":m["PocketMiner"]}
    elif "macro_ap" in m: entries={run:m}
    else: entries={run+"/"+k:v for k,v in m.items()}
    for name,v in entries.items():
        rows.append({"method":name,"macro_ap":v["macro_ap"],"ci":v["macro_ap_protein_bootstrap_95ci"],
                     "pooled_ap":v["pooled_ap"],"proteins":v["n_proteins"],"metrics":str(path),"sha256":sha256(path)})
report={"scope":"development only, seed17, 21 train/8 val; neural runs8 epochs","rows":rows}
base=json.loads(Path("runs/dev24-baseline-s17/metrics.json").read_text())["forest"]
reg=json.loads(Path("runs/dev24-regional-s17/metrics.json").read_text())
b={r["id"]:r["ap"] for r in base["per_protein"]}
d=np.array([r["ap"]-b[r["id"]] for r in reg["per_protein"]])
boot=np.random.default_rng(17).choice(d,size=(2000,len(d)),replace=True).mean(1)
report["regional_minus_forest"]={"mean":float(d.mean()),"paired_protein_bootstrap95":np.quantile(boot,[.025,.975]).tolist(),"family_independence":False}
coverage=json.loads(Path("data/energy-24/coverage.json").read_text())
valid_ids={r["id"] for r in coverage if r["valid"] and r["split"]=="val"}
report["energy_valid"]={s:sum(r["valid"] for r in coverage if r["split"]==s) for s in ("train","val")}
report["same_energy_valid_subset"]={}
for tag in ("if-regional","energy-bounded","energy-concat","energy-mask-only"):
    path=Path(f"runs/dev24-{tag}-s17/metrics.json")
    if path.exists():
        m=json.loads(path.read_text()); vals=[r["ap"] for r in m["per_protein"] if r["id"] in valid_ids]
        report["same_energy_valid_subset"][tag]={"n":len(vals),"macro_ap":float(np.mean(vals)) if vals else None}
atomic_json("outputs/dev24-evidence.json",report)
lines=["# Executed development results","","Regenerate: `.venv\\Scripts\\python.exe scripts/summarize_dev.py`.","",
       "21 training / 8 validation proteins, seed17; neural runs8 epochs. Official test untouched. These are debugging comparisons, not a competitive benchmark.","",
       "| Method | Macro AP | Pooled AP | Proteins |","|---|---:|---:|---:|"]
for r in rows: lines.append(f"| {r['method']} | {r['macro_ap']:.6f} | {r['pooled_ap']:.6f} | {r['proteins']} |")
delta=report["regional_minus_forest"]
lines += ["",f"Regional minus forest: {delta['mean']:.6f}; paired protein bootstrap95% interval {delta['paired_protein_bootstrap95']}. Family dependence remains unresolved.","",
          f"Energy preparation coverage: {sum(r['valid'] for r in coverage)}/{len(coverage)}. Validation valid IDs: {sorted(valid_ids)}. Same-successful-subset comparisons: `{json.dumps(report['same_energy_valid_subset'])}`.","",
          "Energy bounded/concat/mask-only runs use the same full prepared rows and masks. A mask-only improvement would suggest missingness confounding. Energy feature3 is reserved zero; active descriptors are log1p clash counts and log1p force magnitude. The whole-system potential is reported separately and never decomposed into local energies.","",
          "PocketMiner uses official frozen code/weights, strict checkpoint variable matching and explicit mmCIF atom mapping; all baseline/model scores must be compared on the adapter's same residue mask. Consult its metrics.json matched table. Pretraining overlap is unknown. No exact published-protocol reproduction claim.","",
          "The +.03 validation gain promotion gate is not met by the initial regional-vs-forest comparison. Larger data, matched seeds and family analysis are required; do not relabel this as a new proven CV method."]
Path("docs/DEV_RESULTS.md").write_text("\n".join(lines)+"\n")
print(json.dumps({"methods":len(rows),"delta":delta,"energy":report["energy_valid"]}))
