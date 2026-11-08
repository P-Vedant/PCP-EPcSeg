import json
from pathlib import Path
from Bio import Align
from .io import atomic_json


def audit(index_path):
    index = json.loads(Path(index_path).read_text())
    records = index["records"]
    prior = json.loads(Path("configs/prior_exposure.json").read_text(encoding="utf-8-sig"))
    exposed = {s.split(":")[0].lower() for s in prior["apo_chains"]+prior["paired_chains"]}
    official = json.loads(Path("data/raw/folds.json").read_text())
    a = Align.PairwiseAligner(mode="global", match_score=2, mismatch_score=-1, open_gap_score=-5, extend_gap_score=-0.5)
    overlaps = []
    for r in records:
        if r["split"] != "train": continue
        for s in records:
            if s["split"] != "val": continue
            alignment = a.align(r["sequence"], s["sequence"])[0]
            matched = aligned = 0
            for (i,j), (k,l) in zip(*alignment.aligned):
                aligned += j-i
                matched += sum(x==y for x,y in zip(r["sequence"][i:j], s["sequence"][k:l]))
            identity = matched/max(aligned,1)
            coverage = aligned/max(len(r["sequence"]),len(s["sequence"]))
            if identity >= .3 and coverage >= .8:
                overlaps.append({"train":r["id"], "val":s["id"], "identity":identity,"coverage":coverage})
    report = {"official_exact_exposure_overlap": {k: sorted(set(v)&exposed) for k,v in official.items()},
              "selected_exact_exposure_overlap": [r["id"] for r in records if r["apo_id"] in exposed],
              "train_val_sequence_overlap_30pct_identity_80pct_coverage": overlaps,
              "threshold_note":"global alignment, identity among aligned residues; coverage of longer resolved chain",
              "uniprot_overlap": index["uniprot_overlap"],
              "family_metadata_audit": "pending CATH/SCOP; known exposure topology 3.40.190",
              "prior_homolog_audit": "pending all exposed full sequences/aliases; exact IDs insufficient",
              "pretraining_overlap": "unknown", "locked_test_enabled":False,
              "formed_contacts_total": sum(r["contact_audit"]["formed_total"] for r in records),
              "formed_contacts_covered": sum(r["contact_audit"]["formed_covered"] for r in records),
              "excluded":index["failures"]}
    atomic_json(Path(index_path).parent/"audit.json", report)
    return report
