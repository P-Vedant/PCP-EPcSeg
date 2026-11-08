# Task status

| ID | Owner | Status | Next action |
|---|---|---|---|
| T01 | A | complete/verified | hardware/environment and20-step profiling saved |
| T02 | A | partial; full worker queued | full eligible training data plus exposure/sequence/CATH/SCOP audit; test locked |
| T03 | A | completed development baselines | strong sequence baseline still needed |
| T04 | A | core executed/verified | apo-only IF inference, checkpoint/evaluation/export work; pocket-level metrics pending |
| T05 | A (B unavailable) | MPNN132/132 plus ablations complete | full-cohort features only after preparation audit |
| T06 | A | official PocketMiner35proteins and energy controls complete | energy coverage8/29; disabled in larger stage |
| T07 | A | three-seed development comparisons complete | regional promotion gate failed; full/family/locked evidence incomplete |
| T08 | B | unassigned/unverified | see docs/MACHINE_B.md; checkpoint transfer verified locally only |

Stable schema: docs/SCHEMA.md. A integrates schema/model/trainer; B owns independent adapters/shards and separate run outputs. Do not concurrently edit common source or use Git as a live job queue. No active training remains; only the full-data preparation/audit worker will run next. Check active-jobs.json for actual state.
