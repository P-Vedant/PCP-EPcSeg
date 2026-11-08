import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def ap(y, p):
    return float(average_precision_score(y, p)) if np.any(y) else None


def evaluate_predictions(rows, seed=17):
    per = []
    for r in rows:
        y, p = r["y"], r["scores"]
        budget = max(1, int(np.ceil(len(y) * 0.1)))
        item = {"id": r["id"], "ap": ap(y, p), "auroc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
                "recall_top_10pct": float(y[np.argsort(-p)[:budget]].sum() / y.sum()) if y.sum() else None}
        if "contact_scores" in r:
            for k, name in enumerate(("formation", "breakage")):
                item[name+"_ap"] = ap(r["contact_y"][:, k], r["contact_scores"][:, k])
        per.append(item)
    vals = np.array([r["ap"] for r in per if r["ap"] is not None])
    rng = np.random.default_rng(seed)
    boot = np.mean(rng.choice(vals, size=(2000, len(vals)), replace=True), axis=1) if len(vals) else []
    result = {"n_proteins": len(rows), "macro_ap": float(vals.mean()) if len(vals) else None,
              "macro_ap_protein_bootstrap_95ci": np.quantile(boot, [.025, .975]).tolist() if len(vals) else None,
              "pooled_ap": ap(np.concatenate([r["y"] for r in rows]), np.concatenate([r["scores"] for r in rows])),
              "per_protein": per, "ci_caveat": "protein bootstrap; family dependence not resolved"}
    if all("contact_scores" in r for r in rows):
        for k, name in enumerate(("formation", "breakage")):
            result[name+"_pooled_ap"] = ap(np.concatenate([r["contact_y"][:, k] for r in rows]), np.concatenate([r["contact_scores"][:, k] for r in rows]))
    return result
