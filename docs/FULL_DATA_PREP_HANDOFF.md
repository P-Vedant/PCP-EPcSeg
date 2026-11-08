# Full-data worker handoff

Worker status: complete. Source revision: b9a9b451abfec551d05055c775ed3fe164012f2f, branch research/bootstrap.
Actual PID: 568; completed/failed worker must not be duplicated without inspecting logs.
Status and counts: docs/FULL_DATA_PREP_STATUS.json. Logs: prepare-full.log and prepare-full.err.log.
Data/checkpoints remain local and ignored. Original official test is untouched.

Next actions:
1. Read data/prepared-666/index.json and data/prepared-666/audit.json if present. Check all exclusions, sequence overlaps and configs/prior_exposure.json. Command: `.venv\Scripts\python.exe -m pcp audit --index data/prepared-666/index.json` (rerun only if audit was interrupted).
2. Complete exposed-sequence/alias and CATH/SCOP family audits before defining any new independent test. Current sequence-screening is not family independence. Keep official and stricter analysis splits separate.
3. The regional promotion gate failed on the smaller three-seed cohort (docs/DEV120_RESULTS.md). Decide whether a full-data reproduction is warranted before expanding experiments. If continuing unchanged: `.venv\Scripts\python.exe -m pcp features --index data/prepared-666/index.json --output data/features-666`. Expected: a hashed, coverage-audited IF index. Add a strong sequence baseline and pocket-level localization metrics; do not claim novelty from geometry-baseline gains.

Do not overwrite runs or existing checkpoints. Read HANDOFF.md for verified checkpoint/transfer paths.
