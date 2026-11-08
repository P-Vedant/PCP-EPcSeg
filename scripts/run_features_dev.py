"""Fixed small matched IF ablations, then energy coverage. No test-set access."""
import json
import os
from pathlib import Path
import subprocess
import sys
os.chdir(Path(__file__).resolve().parents[1])
for mode in ("regional","auxiliary","pocket"):
    c=json.loads(Path(f"configs/dev-{mode}.json").read_text())
    c["model"]["use_if"]=True
    p=Path(f"configs/dev-if-{mode}.json")
    p.write_text(json.dumps(c,indent=2)+"\n")
    subprocess.run([sys.executable,"-u","-m","pcp","train","--index","data/features-24/index.json",
                    "--run",f"runs/dev24-if-{mode}-s17","--config",str(p)],check=True)
subprocess.run([sys.executable,"-u","-m","pcp","energy-cache","--index","data/features-24/index.json","--output","data/energy-24"],check=True)
print("FEATURE DEVELOPMENT STAGE COMPLETE",flush=True)
