import json
import time
from pathlib import Path
import numpy as np
import torch
from .data import apo_features, parse_structure, load_records
from .io import atomic_json, hardware, sha256, manifest
from .model import RegionalPocket, loss_fn
from .train import tensors, evaluate


def profile(index, out):
    records = sorted(load_records(index), key=lambda rz: len(rz[1]["x"]))
    results = []
    torch.set_num_threads(4)
    for ix in sorted(set([0, len(records)//2, len(records)-1])):
        r,z = records[ix]
        model = RegionalPocket().cuda()
        opt = torch.optim.AdamW(model.parameters())
        inputs, target = tensors(z, "cuda", 0, 1)
        weights = (torch.tensor(1., device="cuda"), torch.ones(2, device="cuda"))
        def step():
            opt.zero_grad(set_to_none=True)
            loss = loss_fn(model(inputs), target, inputs["edges"], weights, model.mode)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5, error_if_nonfinite=True)
            opt.step()
        for _ in range(5): step()
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
        start = time.perf_counter()
        for _ in range(20): step()
        torch.cuda.synchronize()
        results.append({"id":r["id"], "residues":len(z["x"]), "edges":z["edges"].shape[1],
                        "seconds_per_step":(time.perf_counter()-start)/20,
                        "peak_allocated_bytes":torch.cuda.max_memory_allocated(),
                        "peak_reserved_bytes":torch.cuda.max_memory_reserved(),
                        "parameters":sum(p.numel() for p in model.parameters())})
        del model, opt, inputs, target
        torch.cuda.empty_cache()
    result = {"hardware":hardware(), "warmup":5, "measured_steps":20, "microbatch":1, "precision":"float32", "results":results,
              "caveat":"Measured local 5070 Laptop only; RTX 3070 execution unverified"}
    atomic_json(out, result); manifest("profile", path=out, sha256=sha256(out))
    return result


def load_model(checkpoint, device):
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model = RegionalPocket(**state["config"]["model"]).to(device)
    model.load_state_dict(state["model"]); model.eval()
    return model, state


def infer(structure, chain, sequence_file, checkpoint, out, device):
    model, state = load_model(checkpoint, device)
    if model.use_if or model.use_energy:
        raise ValueError("this structure-only CLI does not yet extract enabled cached IF/energy features")
    residues, _ = parse_structure(structure, chain)
    apo = apo_features(residues)
    sequence = "".join(line.strip() for line in Path(sequence_file).read_text().splitlines() if not line.startswith(">"))
    # Require the resolved chain sequence exactly; full-sequence mapping is a separate preparation step.
    if sequence != apo.sequence:
        raise ValueError("FASTA must match the resolved selected chain; map missing positions explicitly first")
    z = {"x":apo.x,"edges":apo.edges,"edge_attr":apo.edge_attr}
    inputs, _ = tensors(z, device, state["mean"], state["std"])
    start = time.perf_counter()
    with torch.no_grad(): pred = model(inputs)
    if device.startswith("cuda"): torch.cuda.synchronize()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, scores=pred["pocket_logits"].sigmoid().cpu().numpy(),
                        contacts=pred["contact_logits"].sigmoid().cpu().numpy(),
                        regions=pred["regions"].cpu().numpy(), residue_ids=apo.residue_ids,
                        edges=apo.edges, coords=apo.coords)
    atomic_json(out+".json", {"structure_sha256":sha256(structure), "sequence_sha256":sha256(sequence_file),
                              "checkpoint_sha256":sha256(checkpoint), "chain":chain,
                              "model_forward_seconds":time.perf_counter()-start,
                              "input_protocol":"single resolved chain; apo only; no holo/ligand/targets"})


def evaluate_checkpoint(index, checkpoint, out, split):
    metadata = json.loads(Path(index).read_text())
    if split == "test":
        raise ValueError("Locked test evaluation is disabled until exposure/family audit and frozen configuration approval are recorded")
    model, state = load_model(checkpoint, "cpu")
    if sha256(index) != state["index_sha256"]:
        raise ValueError("checkpoint data index differs")
    rows = [(r,z) for r,z in load_records(index) if r["split"]==split]
    result = evaluate(model, rows, "cpu", state["mean"], state["std"], Path(out).parent/"eval-predictions")
    atomic_json(out, result)
