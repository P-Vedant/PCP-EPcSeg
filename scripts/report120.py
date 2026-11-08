"""Matched-mask, paired-protein evidence for the larger development cohort."""
import json
import os
from pathlib import Path
import numpy as np
from pcp.metrics import ap
from pcp.io import atomic_json,sha256
os.chdir(Path(__file__).resolve().parents[1])
seeds=(17,23,47)
rows=[]; by_mode={}
for mode in ("regional","auxiliary","pocket"):
    by_mode[mode]=[]
    for seed in seeds:
        path=Path(f"runs/dev120-if-{mode}-s{seed}/metrics.json")
        if not path.exists(): raise RuntimeError(f"Wait for active run: {path}")
        m=json.loads(path.read_text()); by_mode[mode].append(m)
        rows.append({"mode":mode,"seed":seed,"macro_ap":m["macro_ap"],
                     "formation_ap":m["formation_pooled_ap"],"breakage_ap":m["breakage_pooled_ap"],
                     "seconds":m["seconds"],"metrics_sha256":sha256(path)})
means={mode:float(np.mean([m["macro_ap"] for m in items])) for mode,items in by_mode.items()}
pocketminer=json.loads(Path("runs/dev120-pocketminer/metrics.json").read_text())
index=json.loads(Path("data/prepared-120/index.json").read_text())
matched=[]
for record in index["records"]:
    if record["split"]!="val":continue
    path=Path("runs/dev120-pocketminer")/f"{record['id']}.npz"
    if not path.exists(): continue
    with np.load(path,allow_pickle=False) as z:
        mask=z["mask"]; y=z["y"][mask]; pm_ap=ap(y,z["scores"][mask]); ids=z["residue_ids"]
    seed_aps=[]
    for seed in seeds:
        with np.load(f"runs/dev120-if-regional-s{seed}/predictions/{record['id']}.npz",allow_pickle=False) as z:
            np.testing.assert_array_equal(ids,z["residue_ids"])
            seed_aps.append(ap(y,z["scores"][mask]))
    if pm_ap is not None and all(x is not None for x in seed_aps):
        matched.append({"id":record["id"],"PocketMiner_ap":pm_ap,"regional_seed_aps":seed_aps,
                        "mean_seed_ap_difference":float(np.mean(seed_aps)-pm_ap)})
d=np.array([r["mean_seed_ap_difference"] for r in matched])
boot=np.random.default_rng(17).choice(d,size=(2000,len(d)),replace=True).mean(1)
audit=json.loads(Path("data/prepared-120/audit.json").read_text())
report={"rows":rows,"mean_macro_ap_by_mode":means,"matched_PocketMiner_macro_ap":pocketminer["PocketMiner"]["macro_ap"],
        "regional_mean_seed_macro_ap_minus_PocketMiner_on_same_masks":float(d.mean()),
        "paired_protein_bootstrap95":np.quantile(boot,[.025,.975]).tolist(),"matched_per_protein":matched,
        "regional_minus_auxiliary_by_seed":[by_mode["regional"][i]["macro_ap"]-by_mode["auxiliary"][i]["macro_ap"] for i in range(3)],
        "sequence_overlap_pairs":len(audit["train_val_sequence_overlap_30pct_identity_80pct_coverage"]),
        "independent_test":False,"family_independence":False,"selection":"best validation epoch, fixed20epochs, same35validation proteins",
        "promotion_gate_met":False}
atomic_json("outputs/dev120-evidence.json",report)
lines=["# Larger development evidence","","97 training /35validation proteins; 28exclusions from160requested structures. All official test results remain locked. Frozen MPNN succeeded132/132. Neural runs use20epochs and seeds17/23/47, best validation checkpoint.","",
       "| Mode | Seed | Macro AP | Formation pooled AP | Breakage pooled AP |","|---|---:|---:|---:|---:|"]
for r in rows:lines.append(f"| {r['mode']} | {r['seed']} | {r['macro_ap']:.6f} | {r['formation_ap']:.6f} | {r['breakage_ap']:.6f} |")
lines += ["",f"Mean macro AP by mode: `{json.dumps(means)}`.","",
          f"Official PocketMiner (adapted explicit atom mapping): macroAP {pocketminer['PocketMiner']['macro_ap']:.6f}. Regional mean-seed AP minus PocketMiner on identical residue masks/proteins: {d.mean():.6f}; paired protein bootstrap95% {report['paired_protein_bootstrap95']}.","",
          f"Regional minus ordinary auxiliary, by seed: {report['regional_minus_auxiliary_by_seed']}. The predeclared +.03 gain criterion over the strongest matched predictor is not met. No supported regional-mechanism novelty claim.","",
          "The interval samples proteins, not independent families, and averages each protein's AP over three seeds (not ensemble-probability AP). Nine train/validation sequence-similarity pairs exceed30%identity/80%coverage. No family-disjoint or independent-cohort inference is justified. Official model pretraining overlap remains unknown.","",
          "The model improves substantially over the simple geometry baseline on this larger development cohort, but that alone does not support the proposed CV contribution. More rigorous family/exposure audits, full eligible official training data, a strong sequence baseline and pocket-level localization metrics remain pending."]
Path("docs/DEV120_RESULTS.md").write_text("\n".join(lines)+"\n")
print(json.dumps({k:v for k,v in report.items() if k not in ("rows","matched_per_protein")},indent=2))
