"""Durable full-official-training preparation/audit, with bounded status commits.

Only existing origin/research branch is used. No data, caches or checkpoints enter
Git. Concurrent user changes in the three narrative state files are not staged.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
os.chdir(Path(__file__).resolve().parents[1])
from pcp.io import atomic_json,sha256,now,revision
from pcp.data import prepare
from pcp.audit import audit

def git(*args):
    return subprocess.check_output(["git",*args],text=True).strip()

branch=git("branch","--show-current"); remote=git("remote","get-url","origin")
state_files=[Path(p) for p in ("PROJECT_STATE.md","TASKS.md","HANDOFF.md")]
before={str(p):sha256(p) for p in state_files}
status={"pid":os.getpid(),"machine":"A","started":now(),"source_commit":revision(),
        "script":"scripts/prepare_full.py","stdout":"prepare-full.log","stderr":"prepare-full.err.log",
        "status":"running","must_keep_running":True,"official_test_evaluation":False}
atomic_json("active-jobs.json",{"jobs":[status]})
try:
    index=prepare(limit=666)
    status.update(phase="sequence_audit",index=str(index),index_sha256=sha256(index))
    atomic_json("active-jobs.json",{"jobs":[status]})
    a=audit(index)
    d=json.loads(index.read_text())
    status.update(status="complete",must_keep_running=False,ended=now(),
                  train=sum(r["split"]=="train" for r in d["records"]),
                  val=sum(r["split"]=="val" for r in d["records"]),excluded=len(d["failures"]),
                  sequence_overlap_pairs=len(a["train_val_sequence_overlap_30pct_identity_80pct_coverage"]))
except Exception as exc:
    status.update(status="failed",must_keep_running=False,ended=now(),error=str(exc))
    traceback.print_exc()
atomic_json("active-jobs.json",{"jobs":[status]})
atomic_json("docs/FULL_DATA_PREP_STATUS.json",status)
message=(f"\nFull training-data preparation worker {status['status']} at {status['ended']}; "
         f"PID {status['pid']} no longer needs to run. See docs/FULL_DATA_PREP_STATUS.json, "
         "docs/FULL_DATA_PREP_HANDOFF.md and prepare-full.log. Official test remains locked.\n")
safe_state=[]
for p in state_files:
    unchanged=sha256(p)==before[str(p)]
    with open(p,"a",encoding="utf-8") as f:f.write(message)
    if unchanged:safe_state.append(str(p))
handoff=f"""# Full-data worker handoff

Worker status: {status['status']}. Source revision: {status['source_commit']}, branch {branch}.
Actual PID: {status['pid']}; completed/failed worker must not be duplicated without inspecting logs.
Status and counts: docs/FULL_DATA_PREP_STATUS.json. Logs: prepare-full.log and prepare-full.err.log.
Data/checkpoints remain local and ignored. Original official test is untouched.

Next actions:
1. Read data/prepared-666/index.json and data/prepared-666/audit.json if present. Check all exclusions, sequence overlaps and configs/prior_exposure.json. Command: `.venv\\Scripts\\python.exe -m pcp audit --index data/prepared-666/index.json` (rerun only if audit was interrupted).
2. Complete exposed-sequence/alias and CATH/SCOP family audits before defining any new independent test. Current sequence-screening is not family independence. Keep official and stricter analysis splits separate.
3. The regional promotion gate failed on the smaller three-seed cohort (docs/DEV120_RESULTS.md). Decide whether a full-data reproduction is warranted before expanding experiments. If continuing unchanged: `.venv\\Scripts\\python.exe -m pcp features --index data/prepared-666/index.json --output data/features-666`. Expected: a hashed, coverage-audited IF index. Add a strong sequence baseline and pocket-level localization metrics; do not claim novelty from geometry-baseline gains.

Do not overwrite runs or existing checkpoints. Read HANDOFF.md for verified checkpoint/transfer paths.
"""
Path("docs/FULL_DATA_PREP_HANDOFF.md").write_text(handoff,encoding="utf-8")
if git("branch","--show-current")!=branch or git("remote","get-url","origin")!=remote:
    print("State saved; branch/remote changed, so automatic commit/push skipped.",flush=True)
else:
    staged=git("diff","--cached","--name-only")
    if staged:
        print("State saved; pre-existing staged user changes detected, auto commit skipped.",flush=True)
    else:
        files=["docs/FULL_DATA_PREP_STATUS.json","docs/FULL_DATA_PREP_HANDOFF.md","active-jobs.json",*safe_state]
        # Preparation owns these generated files on A during this standalone worker.
        files += ["SPLITS.json","RUN_MANIFEST.jsonl"]
        subprocess.run(["git","add","--",*files],check=True)
        subprocess.run(["git","commit","-m",f"Record full-training-data preparation {status['status']}"],check=True)
        subprocess.run(["git","push","origin",branch],check=True)
print("FULL DATA WORKER",status["status"].upper(),flush=True)
if status["status"]!="complete":sys.exit(1)
