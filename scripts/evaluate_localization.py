"""Matched development localization; uses existing predictions, never refits."""
import json
import os
from pathlib import Path
import numpy as np
from pcp.io import atomic_json,sha256,revision,manifest
from pcp.localization import PROTOCOL,candidates,target_centers,matched_count
os.chdir(Path(__file__).resolve().parents[1])
out=Path("outputs/localization-dev120-v1.json")
if out.exists():raise FileExistsError("Preserve existing protocol result; use a new version for a protocol change")
index_path=Path("data/prepared-120/index.json")
index=json.loads(index_path.read_text()); annotations=json.loads(Path("data/raw/dataset.json").read_text())
methods={"PocketMiner":Path("runs/dev120-pocketminer"),"forest":Path("runs/dev120-baseline-s17")}
for mode in ("regional","auxiliary","pocket"):
    for seed in (17,23,47):methods[f"{mode}-s{seed}"]=Path(f"runs/dev120-if-{mode}-s{seed}/predictions")
rows=[]; failures=[]
for r in index["records"]:
    if r["split"]!="val":continue
    with np.load(r["path"],allow_pickle=False) as z:coords=z["coords"];ids=z["residue_ids"]
    files={name:base/(f"forest-{r['id']}.npz" if name=="forest" else f"{r['id']}.npz") for name,base in methods.items()}
    if any(not p.exists() for p in files.values()):
        failures.append({"id":r["id"],"reason":"missing method prediction"});continue
    valid=np.ones(len(ids),bool); loaded={}
    for name,path in files.items():
        with np.load(path,allow_pickle=False) as z:
            np.testing.assert_array_equal(ids,z["residue_ids"])
            scores=z["scores"];mask=z["mask"] if "mask" in z.files else np.ones(len(ids),bool)
        loaded[name]=scores;valid &= mask & np.isfinite(scores)
    selected=[p["apo_pocket_selection"] for p in annotations[r["apo_id"]] if p["apo_chain"]==r["source"]["pair"]["apo_chain"]]
    truth=target_centers(coords,ids,selected,valid)
    row={"id":r["id"],"valid_residues":int(valid.sum()),"targets":truth,"methods":{}}
    for name,scores in loaded.items():
        pred=candidates(coords,scores,valid)
        row["methods"][name]={"predicted_pockets":pred,"prediction_sha256":sha256(files[name]),
                              "matched":{str(k):matched_count(pred,truth,k) for k in PROTOCOL["top_k"]}}
    rows.append(row)
summary={}
for name in methods:
    summary[name]={}
    for k in PROTOCOL["top_k"]:
        eligible=[r for r in rows if r["targets"]]
        counts=[r["methods"][name]["matched"][str(k)] for r in eligible]
        summary[name][f"top{k}"]={"protein_hit_rate":float(np.mean(np.array(counts)>0)),
                                   "macro_pocket_recall":float(np.mean([c/len(r["targets"]) for c,r in zip(counts,eligible)])),
                                   "micro_pocket_recall":sum(counts)/sum(len(r["targets"]) for r in eligible),
                                   "proteins":len(eligible),"target_pockets":sum(len(r["targets"]) for r in eligible)}
result={"protocol":PROTOCOL,"code_commit":revision(),"source_index_sha256":sha256(index_path),
        "annotation_sha256":sha256("data/raw/dataset.json"),"rows":rows,"failures":failures,"summary":summary,
        "scope":"same35development validation proteins; post-hoc fixed metric; no test access or threshold tuning"}
atomic_json(out,result)
manifest("localization_evaluation",output=str(out),sha256=sha256(out),proteins=len(rows),protocol=PROTOCOL)
lines=["# Development pocket localization proxy","","This fixed protocol was declared after residue-ranking experiments, before inspecting localization results. It was not tuned. It is NOT ligand-center DCC or an independent test.","",
       "Candidates: top10% valid residue scores, connected at8A, score-weighted centroids ranked by mean score. Targets: official apo residue sets merged at Jaccard>=.5, unweighted centroids. Maximum one-to-one matching within4A. All methods share the exact same residue mask per protein.","",
       "| Method | Top1 protein hit | Top3 protein hit | Top3 macro pocket recall |","|---|---:|---:|---:|"]
for name,s in summary.items():lines.append(f"| {name} | {s['top1']['protein_hit_rate']:.4f} | {s['top3']['protein_hit_rate']:.4f} | {s['top3']['macro_pocket_recall']:.4f} |")
lines+= ["",f"Evaluated {len(rows)} proteins. Complete target/predicted centroids, membership and input hashes are saved in outputs/localization-dev120-v1.json. No family independence or physical pocket-geometry claim follows from this proxy."]
Path("docs/LOCALIZATION_RESULTS.md").write_text("\n".join(lines)+"\n")
print(json.dumps(summary,indent=2))
