# PCP-EPcSeg

Research prototype for cryptic pocket localization from an apo structure and sequence, with sparse contact formation/breakage prediction and learned soft regions. **No competitive-performance or novelty claim yet.** See `PROJECT_STATE.md` and `HANDOFF.md` for executed versus pending work.

The existing checkout is `C:\Users\nagan\PCP-EPcSeg\PCP-EPcSeg`. Work continues on `research/bootstrap`. Open that folder in VS Code. Data, features, environments and checkpoints are local and Git-ignored.

## Environment

Python 3.11, Windows, verified physical GPU RTX 5070 Laptop (8 GB). The partner RTX 3070 is unverified. Use an isolated environment and the CUDA wheel index; no custom CUDA extensions or compilation are required.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install torch==2.11.0+cu128 --index-url https://download.pytorch.org/whl/cu128
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -m pcp hardware
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The installed versions are captured in `requirements-lock.txt`. The CUDA version was selected from the official index and must pass a real optimizer step on each machine.

## Development run

```powershell
.venv\Scripts\python.exe -m pcp prepare --limit 24
.venv\Scripts\python.exe -m pcp audit --index data/prepared-24/index.json
.venv\Scripts\python.exe -m pcp baseline --index data/prepared-24/index.json --run runs/dev24-baseline-s17
.venv\Scripts\python.exe -m pcp profile --index data/prepared-24/index.json
.venv\Scripts\python.exe -m pcp train --index data/prepared-24/index.json --run runs/dev24-regional-s17 --config configs/dev-regional.json
.venv\Scripts\python.exe -m pcp train --index data/prepared-24/index.json --run runs/dev24-auxiliary-s17 --config configs/dev-auxiliary.json
.venv\Scripts\python.exe -m pcp train --index data/prepared-24/index.json --run runs/dev24-pocket-s17 --config configs/dev-pocket.json
```

Never overwrite a completed run. Resume interrupted training with the original arguments plus `--resume runs/<run>/last.pt`; the index and configuration must match. Saves occur every epoch and at optimizer boundaries after ten minutes. A checkpoint includes optimizer, scheduler, scaler, RNG and exact next sampler position. Only load trusted local checkpoints.

`--limit 24` selects at most 24 training and 8 validation apo structures, in deterministic PDB order. This is a debugging subset, not a benchmark result. Validation comes from official **training fold 0**; other official training folds supply training. The official test is never evaluated. `configs/prior_exposure.json` records all 16 previously inspected chains and paired structures. Family and homolog audits remain required.

## Inference and transfer

```powershell
.venv\Scripts\python.exe -m pcp infer --structure data/raw/PROTEIN.cif --chain A --sequence resolved-chain.fasta --checkpoint runs/dev24-regional-s17/best.pt --out outputs/predictions.npz
.venv\Scripts\python.exe -m pcp evaluate --index data/prepared-24/index.json --checkpoint runs/dev24-regional-s17/best.pt --out outputs/validation.json
.venv\Scripts\python.exe -m pcp export --out outputs/transfer.zip runs/dev24-regional-s17/best.pt data/prepared-24/index.json
.venv\Scripts\python.exe -m pcp import --archive outputs/transfer.zip --destination transfer-check
```

Replace the inference structure and FASTA placeholders; FASTA must match the resolved chain exactly. Add selected `.npz` shards explicitly to a transfer command. The archive contains a SHA-256 manifest; import verifies every member before writing and refuses overwrites/path traversal. Checkpoint architecture is common to both GPUs; portability has to be executed on B before claiming cross-GPU validation.

## Scientific limits

Core implemented architecture: four invariant distance-based message-passing layers, width 96, 12 learned regions; symmetric region-pair contact factors; predicted incident contacts feed pocket decoding. `auxiliary` removes regions and feedback while retaining the same module parameter allocation; `pocket` omits contact supervision. Inactive parameters are retained for interface compatibility, so effective trained capacity is not exactly matched.

Frozen ProteinMPNN extraction, OpenMM context scoring, energy controls and official PocketMiner checkpoint inference have now executed. See `docs/DEV_RESULTS.md` and `docs/DEV120_RESULTS.md` for actual evidence. The larger stage has 97training/35validation proteins and three seeds; regional factorization has not demonstrated a meaningful advantage over ordinary contact supervision. Full eligible official training data, family/exposure analysis, a strong sequence baseline, pocket-level localization and locked evaluation remain pending. Read `docs/SCHEMA.md`, `DATA_AUDIT.md`, `CLAIMS.md` and `HANDOFF.md` before making scientific claims.

Optional feature commands:

```powershell
.venv\Scripts\python.exe scripts/fetch_external.py
.venv\Scripts\python.exe -m pcp features --index data/prepared-24/index.json --output data/features-24
.venv\Scripts\python.exe -m pcp energy-cache --index data/features-24/index.json --output data/energy-24
.venv-pocketminer\Scripts\python.exe scripts/pocketminer_baseline.py --index data/prepared-120/index.json --cohort dev120 --out runs/NEW-POCKETMINER-RUN
```

PocketMiner needs a separate environment installed with `requirements-pocketminer-lock.txt`; its author code/checkpoint are fetched above. `infer` automatically caches apo-only IF/energy features when enabled by a checkpoint; it requires no paired structure or labels. CPU inference with IF was executed and matched the prepared-feature pathway to 1.2e-6 probability tolerance. Energy failures remain masked and recorded. Use Python job launchers on this machine because its default policy blocks `.ps1` files.
