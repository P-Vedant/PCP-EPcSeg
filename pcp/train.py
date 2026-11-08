from __future__ import annotations
import json
import os
import random
import time
from pathlib import Path
import numpy as np
import torch
from .data import load_records
from .io import atomic_json, sha256, manifest, hardware, revision, now
from .metrics import evaluate_predictions
from .model import RegionalPocket, loss_fn


def tensors(z, device, mean, std):
    # This object contains no coordinates or labels from the holo structure.
    apo = {"x": torch.tensor((z["x"]-mean)/std, device=device),
           "edges": torch.tensor(z["edges"], dtype=torch.long, device=device),
           "edge_attr": torch.tensor(z["edge_attr"], device=device)}
    for key, dim in (("if_features", 23), ("energy", 3)):
        mask = "if_mask" if key == "if_features" else "energy_mask"
        apo[key] = torch.tensor(z.get(key, np.zeros((len(z["x"]), dim), np.float32)), device=device)
        apo[mask] = torch.tensor(z.get(mask, np.zeros((len(z["x"]), 1), np.float32)), device=device)
    targets = {k: torch.tensor(z[k], device=device) for k in ("y", "contact_y", "contact_mask") if k in z}
    return apo, targets


def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def rng_state():
    return {"python": random.getstate(), "numpy": np.random.get_state(), "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}


def restore_rng(rng):
    random.setstate(rng["python"]); np.random.set_state(rng["numpy"]); torch.set_rng_state(rng["torch"].cpu())
    if torch.cuda.is_available() and rng["cuda"]:
        torch.cuda.set_rng_state_all([s.cpu() for s in rng["cuda"]])


def save_checkpoint(path, state):
    torch.save(state, str(path) + ".tmp")
    os.replace(str(path) + ".tmp", path)


def evaluate(model, records, device, mean, std, outdir=None):
    model.eval()
    rows = []
    with torch.no_grad():
        for r, z in records:
            inputs, targets = tensors(z, device, mean, std)
            pred = model(inputs)
            scores = pred["pocket_logits"].sigmoid().cpu().numpy()
            cp = pred["contact_logits"].sigmoid().cpu().numpy()
            mask = z["contact_mask"]
            rows.append({"id": r["id"], "y": z["y"], "scores": scores,
                         "contact_y": z["contact_y"][mask], "contact_scores": cp[mask]})
            if outdir:
                Path(outdir).mkdir(parents=True, exist_ok=True)
                np.savez_compressed(Path(outdir)/f"{r['id']}.npz", scores=scores, contacts=cp,
                                    regions=pred["regions"].cpu().numpy(), residue_ids=z["residue_ids"],
                                    edges=z["edges"], coords=z["coords"], y=z["y"], contact_y=z["contact_y"], contact_mask=mask)
    return evaluate_predictions(rows)


def train(index_path, run_dir, config, resume=None):
    run_dir = Path(run_dir)
    if run_dir.exists() and not resume:
        raise FileExistsError(f"refusing to overwrite {run_dir}; choose a new run or --resume")
    run_dir.mkdir(parents=True, exist_ok=True)
    records = load_records(index_path)
    tr = [(r,z) for r,z in records if r["split"] == "train"]
    val = [(r,z) for r,z in records if r["split"] == "val"]
    if not tr or not val:
        raise ValueError("need nonempty train and validation")
    device = torch.device(config.get("device", "cuda"))
    seed_all(config["seed"])
    torch.set_num_threads(4)
    features = np.concatenate([z["x"] for _,z in tr])
    mean, std = features.mean(0), features.std(0).clip(0.05)
    model_cfg = config["model"]
    for enabled, key in ((model_cfg.get("use_if"), "if_mask"), (model_cfg.get("use_energy"), "energy_mask")):
        if enabled and not any(key in z and z[key].any() for _,z in tr):
            raise ValueError(f"{key} requested but no training features present")
    model = RegionalPocket(**model_cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["lr"], weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.98)
    scaler = torch.amp.GradScaler("cuda", enabled=False)  # float32 until finite mixed-precision validation
    y = np.concatenate([z["y"] for _,z in tr])
    cy = np.concatenate([z["contact_y"][z["contact_mask"]] for _,z in tr])
    weights = (torch.tensor(np.clip((1-y).sum()/max(y.sum(), 1), 1, 50), device=device, dtype=torch.float32),
               torch.tensor(np.clip((1-cy).sum(0)/np.maximum(cy.sum(0), 1), 1, 100), device=device, dtype=torch.float32))
    start_epoch, offset, order, best = 0, 0, None, -1.0
    if resume:
        # Only load locally created trusted checkpoints; pickle is not a safe exchange format.
        state = torch.load(resume, map_location="cpu", weights_only=False)
        if state["index_sha256"] != sha256(index_path) or state["config"] != config:
            raise ValueError("resume config/index mismatch; preserve original experiment")
        model.load_state_dict(state["model"]); optimizer.load_state_dict(state["optimizer"])
        scheduler.load_state_dict(state["scheduler"]); scaler.load_state_dict(state["scaler"])
        start_epoch, offset, order, best = state["epoch"], state["offset"], state["order"], state["best"]
        mean, std = state["mean"], state["std"]
        restore_rng(state["rng"])
    atomic_json(run_dir/"config.json", config)
    hw = hardware()
    atomic_json(run_dir/"hardware.json", hw)
    provenance = {"commit": revision(), "index_sha256": sha256(index_path), "config": config,
                  "parameters": sum(p.numel() for p in model.parameters()), "start_time": now(),
                  "feature_hashes": {r["id"]: r["sha256"] for r,_ in records}, "hardware": hw}
    atomic_json(run_dir/("resume-provenance.json" if resume else "provenance.json"), provenance)
    manifest("train_start", run=str(run_dir), resume=resume, **provenance)
    def checkpoint(epoch, offset, order):
        return {"model": model.state_dict(), "optimizer": optimizer.state_dict(), "scheduler": scheduler.state_dict(),
                "scaler": scaler.state_dict(), "epoch": epoch, "offset": offset, "order": order,
                "best": best, "rng": rng_state(), "mean": mean, "std": std,
                "index_sha256": sha256(index_path), "config": config, "code_commit": revision()}
    started = last_save = time.monotonic()
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    for epoch in range(start_epoch, config["epochs"]):
        model.train()
        order = np.random.permutation(len(tr)).tolist() if order is None else order
        accum = config["accumulation"]
        losses = []
        for begin in range(offset, len(order), accum):
            chunk = order[begin:begin+accum]
            optimizer.zero_grad(set_to_none=True)
            for ix in chunk:
                inputs, targets = tensors(tr[ix][1], device, mean, std)
                loss = loss_fn(model(inputs), targets, inputs["edges"], weights, model.mode)
                if not torch.isfinite(loss):
                    raise FloatingPointError("nonfinite loss")
                (loss / len(chunk)).backward()
                losses.append(float(loss.detach()))
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0, error_if_nonfinite=True)
            optimizer.step()
            if time.monotonic() - last_save > 600:
                save_checkpoint(run_dir/"last.pt", checkpoint(epoch, begin+len(chunk), order))
                last_save = time.monotonic()
        metrics = evaluate(model, val, device, mean, std)
        scheduler.step()
        improved = metrics["macro_ap"] > best
        best = max(best, metrics["macro_ap"])
        state = checkpoint(epoch+1, 0, None)
        save_checkpoint(run_dir/"last.pt", state)
        if improved:
            save_checkpoint(run_dir/"best.pt", state)
            atomic_json(run_dir/"best_metrics.json", metrics)
        row = {"epoch": epoch+1, "train_loss": float(np.mean(losses)) if losses else None,
               "val_macro_ap": metrics["macro_ap"], "seconds": time.monotonic()-started}
        with open(run_dir/"history.jsonl", "a") as f:
            f.write(json.dumps(row)+"\n")
        print(json.dumps(row), flush=True)
        order, offset = None, 0
    best_state = torch.load(run_dir/"best.pt", map_location="cpu", weights_only=False)
    model.load_state_dict(best_state["model"])
    metrics = evaluate(model, val, device, mean, std, run_dir/"predictions")
    metrics.update(seconds=time.monotonic()-started, parameters=provenance["parameters"],
                   peak_allocated_bytes=torch.cuda.max_memory_allocated() if device.type=="cuda" else None,
                   peak_reserved_bytes=torch.cuda.max_memory_reserved() if device.type=="cuda" else None)
    atomic_json(run_dir/"metrics.json", metrics)
    manifest("train_complete", run=str(run_dir), checkpoint_sha256=sha256(run_dir/"best.pt"),
             metrics_sha256=sha256(run_dir/"metrics.json"), metrics=metrics)
    return metrics


def baseline(index_path, run_dir, seed=17):
    import pickle
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    out = Path(run_dir); out.mkdir(parents=True, exist_ok=False)
    records = load_records(index_path)
    tr = [(r,z) for r,z in records if r["split"]=="train"]
    val = [(r,z) for r,z in records if r["split"]=="val"]
    x, y = np.concatenate([z["x"] for _,z in tr]), np.concatenate([z["y"] for _,z in tr])
    models = {"logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)),
              "forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=5, max_features="sqrt", class_weight="balanced", n_jobs=4, random_state=seed)}
    results = {}
    provenance = {"commit": revision(), "seed": seed, "index_sha256": sha256(index_path),
                  "feature_hashes": {r["id"]: r["sha256"] for r,_ in records}, "start_time": now()}
    atomic_json(out/"provenance.json", provenance)
    manifest("baseline_start", run=str(out), **provenance)
    for name, model in models.items():
        start = time.monotonic(); model.fit(x, y)
        rows = []
        for r,z in val:
            scores = model.predict_proba(z["x"])[:,1]
            rows.append({"id": r["id"], "y": z["y"], "scores": scores})
            np.savez_compressed(out/f"{name}-{r['id']}.npz", scores=scores, y=z["y"], residue_ids=z["residue_ids"])
        results[name] = evaluate_predictions(rows)
        results[name]["seconds"] = time.monotonic()-start
        with open(out/f"{name}.pkl", "wb") as f:
            pickle.dump(model, f)
    atomic_json(out/"metrics.json", results)
    manifest("baseline_complete", run=str(out), metrics=results, metrics_sha256=sha256(out/"metrics.json"))
    return results
