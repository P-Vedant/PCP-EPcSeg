# Task ownership and status

| ID | Owner | Status | Dependencies | Files / result |
|---|---|---|---|---|
| T01 | A | complete / verified | none | isolated env, CUDA smoke, hardware/profile, requirements lock |
| T02 | A | partial / dev subset verified | T01 | data.py/audit.py; 21 train/8 val; full benchmark and family/exposure audit pending |
| T03 | A | dev baseline complete | T02 | train.py/metrics.py; LR/RF predictions and metrics |
| T04 | A | core implemented / dev runs verified | T02 | model.py, trainer/CLI, 3 matched no-IF neural configs; CPU checkpoint inference and transfer verified |
| T05 | A (B unavailable) | features extracted; comparisons next | T02 | features.py; frozen MPNN 29/29; cached shard schema |
| T06 | A (B unavailable) | one energy context verified; coverage next | T02 | energy.py; Amber14/OBC2 with explicit solvent policy; official predictor execution pending |
| T07 | A | partial | T03-T06 | initial ablations and bootstrap; full seeds/family metrics/locked evaluation pending |
| T08 | B | unassigned / remote unverified | T04 | cross-3070 checkpoint load and independent jobs; see docs/MACHINE_B.md |

Shared schema v1 is in docs/SCHEMA.md; A integrates schema changes. B must use disjoint SHA-256 shard IDs and separate run directories. This is not a Git-based live queue. Do not concurrently append one shared manifest across machines.

T05 completed first matched IF runs; no improvement over forest. T06 coverage executed: 8/29 valid energy contexts. Matched energy/missingness ablations and official predictor still pending.

T06 energy bounded/concat/mask-only and within-protein IF-shuffle controls completed on29 rows. T02 prepare120 complete; audit next. T07 larger 3-seed matrix next. PocketMiner baseline environment installed; first execution missing tqdm, now installed; checkpoint execution retry pending.
