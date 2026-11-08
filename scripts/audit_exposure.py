"""Durable exposure audit; save progress and completion state without test scoring."""
import json
import os
from pathlib import Path
import traceback
os.chdir(Path(__file__).resolve().parents[1])
from pcp.exposure import run
from pcp.io import atomic_json,now,revision,manifest,sha256
status={"pid":os.getpid(),"script":"scripts/audit_exposure.py","machine":"A","source_commit":revision(),
        "started":now(),"status":"running","must_keep_running":True,"stdout":"exposure-audit.log","stderr":"exposure-audit.err.log"}
atomic_json("active-jobs.json",{"jobs":[status]})
try:
    report=run()
    status.update(status="complete",must_keep_running=False,ended=now(),
                  chains_parsed=report["chains_parsed"],chains_requested=report["chains_requested"],
                  strict_val_count=report["strict_val_count"],prior_annotation_gaps=report["prior_annotation_gaps"],
                  report_sha256=sha256("data/exposure-audit-v1/report.json"))
    manifest("exposure_audit_complete",**status)
except Exception as exc:
    status.update(status="failed",must_keep_running=False,ended=now(),error=str(exc));traceback.print_exc()
atomic_json("active-jobs.json",{"jobs":[status]})
atomic_json("docs/EXPOSURE_AUDIT_STATUS.json",status)
message=f"\nExposure/CATH audit worker {status['status']} at {status['ended']}; see docs/EXPOSURE_AUDIT_STATUS.json and data/exposure-audit-v1/report.json. Test remains locked.\n"
for name in ("PROJECT_STATE.md","TASKS.md","HANDOFF.md"):
    with open(name,"a",encoding="utf-8") as f:f.write(message)
print(json.dumps(status,indent=2),flush=True)
if status["status"]!="complete":raise SystemExit(1)
