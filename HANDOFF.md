# Handoff — continue, do not restart

Existing checkout: C:\Users\nagan\PCP-EPcSeg\PCP-EPcSeg
Read AGENTS.md, PROJECT_STATE.md, TASKS.md, DATA_AUDIT.md, CLAIMS.md and docs/MASTER_PROMPT.md.
Required implementation:169c2075476de808ae7242c770d75ed08f97ada3 or later on research/bootstrap. Do not check out an older revision over current files. A is an8GB RTX5070 Laptop; B remains unavailable.

## Live work and first commands

The completed development jobs must NOT be rerun. A full official-training preparation/audit worker is being launched immediately after this handoff commit. Its actual PID, source revision and phase are in active-jobs.json (plural). The singular active-job.json is an older completed-stage record.

```powershell
Set-Location 'C:\Users\nagan\PCP-EPcSeg\PCP-EPcSeg'
git status --short
Get-Content active-jobs.json
Get-Content prepare-full.log -Tail 12
Get-Content prepare-full.err.log -Tail 12
```

Keep a live scripts/prepare_full.py process running; do not launch duplicates. It creates data/prepared-666/index.json and audit.json, records counts/exclusions, appends state and commits/pushes authorized status. It will not score test, launch new training, or change architecture. If the branch/remote changes or user changes are staged, it saves locally and skips auto-push. If narrative state files changed concurrently, it appends but does not stage those user changes. Check docs/FULL_DATA_PREP_STATUS.json and docs/FULL_DATA_PREP_HANDOFF.md after completion. Failed push does not imply failed data preparation.

## Next three actions / exit conditions

1. T02: finish/inspect the worker above. Expected: complete status, hashed full eligible training-pool index, explicit exclusions and sequence-overlap audit. If no live worker and no completed index, run `.venv\Scripts\python.exe -u scripts/prepare_full.py` with logs; it reuses downloaded structures. Do not restart a live worker.
2. T02: audit all16 prior apo/paired chains, aliases, close homologs and structural families before defining independent evidence. Inspect existing results with `.venv\Scripts\python.exe -c "import json; d=json.load(open('data/prepared-666/audit.json')); print({k:v for k,v in d.items() if k!='excluded'})"`. Implement the missing full-exposure/CATH/SCOP audit; current global sequence screening is insufficient. Expected: a documented strict-analysis split separate from original official folds, or explicit unresolved coverage. Keep test results locked.
3. If continuing full-data reproduction after the failed regional promotion gate, run `.venv\Scripts\python.exe -m pcp features --index data/prepared-666/index.json --output data/features-666`. Expected: hashed frozen-feature index with coverage/failure reasons. Add a strong sequence baseline and pocket-level localization metrics before claiming competitiveness; predeclare the remaining comparisons. Do not expand architecture or reinterpret tiny auxiliary-head gains as novelty.

## Completed evidence

- Small cohort21train/8val: geometry baselines,3neural modes with/without IF, energy bounded/concat/mask-only, IF-shuffle controls and official PocketMiner.
- Larger97train/35val:132/132MPNN extraction;9neural runs at20epochs, seeds17/23/47; official PocketMiner on35same validation proteins. Read docs/DEV120_RESULTS.md (regenerate with `.venv\Scripts\python.exe scripts/report120.py`).
- Regional meanAP .255615 vs auxiliary .255062; PocketMiner .262020. Same-mask regional mean-seed minus PocketMiner -.005872, protein bootstrap95%[-.050246,.039338]. Promotion gate not met. Nine sequence-overlap pairs; no family-disjoint claim.
- CUDA optimizer, rigid-motion invariance/apo-only schema, finite one-batch overfit, exact optimizer checkpoint next-step equivalence, missing-energy masking, transfer path safety and full hash import passed. Diagnostic evaluation replay matches saved AP exactly. Apo-only IF inference matches prepared features within1.2e-6. No cross-3070 execution claimed.
- OpenMM coverage8/29 (5train,3val); no-energy retained for larger stage. Native NLL is not energy; forces are not local energies; two endpoints are not a trajectory or opening probability.

## Checkpoints and transfer

Representative fixed-seed checkpoint: runs/dev120-if-regional-s17/best.pt
SHA256: ffc1d268b721c615e924bdcdaaba2099a62c5a1d4f9e4c4ab04e8726767cf482
Last resume checkpoint: runs/dev120-if-regional-s17/last.pt (already20epochs complete).
Input index: data/features-120/index.json. All runs include resolved config/provenance/hardware/metrics and per-residue/contact/region NPZ predictions. Root RUN_MANIFEST.jsonl is append-only.

Complete selected transfer: outputs/dev120-regional-s17-transfer.zip
SHA256: cd0cc3ef4a90a455b29cbd9da70361e9d0190449b74f973f0d931abca1d63ca4
139files: all132cached data shards plus index and six run artifacts. Import verified at outputs/transfer-120-check. Raw structures and external weights are not in this archive; scripts/fetch_external.py fetches pinned author weights/code. No transfer service was invented.

## Reproduction commands

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m pcp infer --structure data/raw/1a4u.cif --chain B --sequence outputs/resolved-chain.fasta --checkpoint runs/dev120-if-regional-s17/best.pt --out outputs/NEW-INFERENCE.npz --device cpu
.venv\Scripts\python.exe -m pcp evaluate --index data/features-120/index.json --checkpoint runs/dev120-if-regional-s17/best.pt --out outputs/NEW-VALIDATION.json
.venv-pocketminer\Scripts\python.exe scripts/pocketminer_baseline.py --index data/prepared-120/index.json --cohort dev120 --out runs/NEW-POCKETMINER-RUN
```

Do not rerun completed training under existing IDs. Resume only interrupted runs using the same config/index plus --resume <run>/last.pt. Standalone inference FASTA must match the resolved selected chain exactly. Diagnostic shuffled/mask-only checkpoints are deliberately rejected for deployment inference.

Known limitations: single standard-chain geometric protocol (multichain A-B selections excluded); missing/modified residues and ligand mapping can cause exclusions; selected holo supervises contacts while pocket labels union selected-chain annotations; official PocketMiner preprocessing is adapted, not an exact published benchmark reproduction; pretraining overlap unknown. Larger subset is sorted PDB IDs, not representative random sampling. Full CATH/SCOP audit, strong sequence baseline, pocket-level metrics and final locked evaluation are incomplete.

Use the isolated .venv; see requirements-lock.txt and requirements-pocketminer-lock.txt. Do not reinstall CUDA unnecessarily. Keep data/checkpoints outside Git. Update state/handoff/tasks and commit/push coherent stages. No paid cloud compute, submissions or new public publication.

Full training-data preparation worker complete at 2026-11-08T03:33:04.513846+00:00; PID 568 no longer needs to run. See docs/FULL_DATA_PREP_STATUS.json, docs/FULL_DATA_PREP_HANDOFF.md and prepare-full.log. Official test remains locked.
