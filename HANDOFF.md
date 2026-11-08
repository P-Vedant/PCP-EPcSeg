# Continuation handoff

Continue the existing checkout; do not restart: `C:\Users\nagan\PCP-EPcSeg\PCP-EPcSeg`.
Read docs/MASTER_PROMPT.md, PROJECT_STATE.md, TASKS.md, DATA_AUDIT.md and configs/prior_exposure.json.
Branch: research/bootstrap. Core experiment revision: e3c8d0c; feature-stage revisions are later commits (use `git log -3 --oneline`). No AGENTS.md was present. Preserve any later user edits.

## Current files / jobs

- Completed runs: runs/dev24-{baseline,regional,auxiliary,pocket}-s17. Checkpoint: runs/dev24-regional-s17/best.pt. Baseline revision recorded in each run's provenance.json; root RUN_MANIFEST.jsonl is append-only.
- Data: data/prepared-24/index.json (21 train, 8 val), data/features-24/index.json (29/29 frozen IF coverage), outputs/profile.json, outputs/hardware.json.
- Verified transfer: outputs/dev24-transfer.zip, SHA-256 `814a368c829cf368a0a707b08de98a160259959357924d429f11cc2ffdd38904`. Contains only checkpoint/index/one shard, not a full dataset. Validation: outputs/artifact-checks.json.
- Check active-job.json and logs before launching anything. The old PID 36156 completed scripts/run_dev.py. The older PowerShell PID 44620 failed before running experiments.
- Installation is complete; no need to redownload torch or MPNN. `.venv\Scripts\python.exe` is the interpreter. Source is editable in this checkout and visible in VS Code.

## Next three concrete actions

1. Finish T05/T06: inspect feature stage logs and `data/energy-24/coverage.json`. If no live feature job and runs/dev24-if-regional-s17 does not exist, run `.venv\Scripts\python.exe -u scripts/run_features_dev.py`. Expected: three matched IF runs and energy index with explicit coverage/failures. If partially complete, run only missing CLI stages, not the entire launcher.
2. Expand T02: `.venv\Scripts\python.exe -m pcp prepare --limit 120` then `.venv\Scripts\python.exe -m pcp audit --index data/prepared-120/index.json`. Expected: up to 120 training + 40 validation examples, exclusions and overlap audit. These remain a development subset. Full official train pool is still pending. Do not evaluate test.
3. Complete comparisons on the **same rows**: train regional/auxiliary/pocket with IF using new immutable run IDs; evaluate no-energy and missingness controls before enabling energy. Use the fixed configs as templates and preserve resolved configs. Then implement an official external predictor (PocketMiner or CryptoBench pLM); README links in docs/PRIOR_ART.md. Expected: a numeric matched evidence table, with no novelty claim unless it survives the declared gate.

## Exact useful commands

```powershell
git status --short
Get-Content active-job.json
Get-Content features-dev.log -Tail 15
Get-Content features-dev.err.log -Tail 15
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m pcp train --index data/prepared-24/index.json --run runs/dev24-regional-s17 --config configs/dev-regional.json --resume runs/dev24-regional-s17/last.pt
```

The resume command for the completed run verifies load/final evaluation but has no remaining epochs. To extend training, create an explicit new experiment policy; do not silently change a resume config. `verify_artifacts.py` was executed already and intentionally refuses to overwrite its transfer outputs.

## Caveats that must survive handoff

The master prompt's desktop 5070 Ti assumption was false: local GPU is 8 GB laptop 5070. Region mechanism has not beaten geometry forest. Only 8 validation proteins, no family-level confidence claim. One pair per apo is chosen deterministically among main entries; pocket labels union all pairs on selected chain; contact labels use only the selected pair. Multi-chain IDs such as A-B are excluded with reasons; full multichain graph support pending. Standard modified residues and missing heavy atoms limit coverage. Apo structure may retain unrelated cofactors in raw context; no target ligand/holo coordinates enter inference. PDB inference insertion numbering is less rigorous than mmCIF. Energy force is a strain proxy, not local energy or opening probability. Retained cofactor template failures are not repaired by deleting cofactors.

Keep official benchmark split separate from any new independent test. Exposure list includes 16 apo and paired chains plus known CATH topology 3.40.190 overlap (3PPN/4P0I). Exact-ID exclusion is insufficient: aliases, sequences, close homologs and family metadata must be audited. No locked test evaluation enabled. Partner commands are unverified remotely. No submission/publication or paid cloud compute.

After each task update state/handoff/tasks, record PIDs/logs/checkpoint hashes, commit/push coherent source stages to existing origin, and provide the next continuation block. Preserve data/checkpoints outside Git.

ACTIVE FEATURE JOB: PID 40820, machine A, scripts/run_features_dev.py, logs features-dev.log and features-dev.err.log. Keep running; do not duplicate. Launched after feature-stage commit; check git log -1.

LATEST: PID 40820 job completed successfully (FEATURE DEVELOPMENT STAGE COMPLETE in features-dev.log). No running jobs to preserve. All three dev24-if runs exist: do not rerun launcher. Energy 8/29 valid; index data/energy-24/index.json. Next: energy/no-energy/missingness controls, expand to120, bounded official predictor install. PocketMiner install was not executed because automatic approval review reached usage limit. Resume only after approval service recovers.
