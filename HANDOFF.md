# Handoff

Continue here: C:\Users\nagan\PCP-EPcSeg\PCP-EPcSeg. Do not restart.
Read docs/MASTER_PROMPT.md, PROJECT_STATE.md, TASKS.md, DATA_AUDIT.md and CLAIMS.md.
Current base: 9648717 main; bootstrap files not yet committed.
Next actions:
1. Verify torch CUDA forward/backward and capture hardware in outputs/hardware.json.
2. Audit official CryptoBench/PocketMiner source, licenses and splits; establish apo-only schema.
3. Run a real-data geometry baseline and implement regional contact model.
No training jobs/checkpoints/transfer archives yet. Partner execution unverified.
Unknown identities of prior 16 exposed proteins block a fresh locked test. Do not invent them.
Keep all data, features and checkpoints out of Git. Update this file after every stage.

Latest: configs/prior_exposure.json contains the user-supplied exposure list. Check prepare-24.log and install-project.log. Preparation launched in exec session 27263. Do not duplicate until logs/index checked. Current uncommitted source implements data preparation, sparse regional model and trainer; CLI/tests next.

Next exact command: powershell -NoProfile -File scripts/run_dev.ps1. It runs baseline, 20-step profile, and 8-epoch regional/auxiliary/pocket comparisons sequentially. It refuses existing run directories. Check runs and active-job.json before launching. Source code now verified by four CPU tests and CUDA smoke test.
