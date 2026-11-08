# Continuation rules

Continue this checkout; preserve user edits and immutable run directories. Read HANDOFF.md, PROJECT_STATE.md, TASKS.md and docs/MASTER_PROMPT.md before acting. Use .venv/Scripts/python.exe on A. The local GPU is an 8 GB RTX5070 Laptop, not a desktop5070Ti.

Keep data/cache/checkpoints/environments/external code under ignored directories; never git-add those artifacts. Use explicit selected files for transfers and verify hashes. No paid cloud compute, conference submission, new public repository or invented credentials/server. Existing origin pushes of code/state are user-authorized. Do not spawn extra AI agents unless explicitly requested.

Official test results stay locked. Keep official splits separate from new independence analyses. configs/prior_exposure.json lists all16 exposed apo/paired chains; exact IDs alone do not establish independence. No SOTA/novelty/family-disjoint claim without evidence. Record failed comparisons honestly.

Each coherent completed stage: update HANDOFF.md, PROJECT_STATE.md, TASKS.md; append immutable RUN_MANIFEST.jsonl records; commit and push source/state. Save before long jobs and at least every15minutes. Record job PID, log, checkpoint, source/config/data hashes and exact next commands. Use durable Python scripts with logs. Check active-jobs.json and actual processes before launching duplicates; a stale PID file is not proof of a live job.

Do not modify model/trainer source underneath active training jobs. Wait for completion or use a separate branch/worktree when a fix must diverge. Run meaningful focused checks for changed behavior. Keep numeric arrays for later figures; no figures required now.
