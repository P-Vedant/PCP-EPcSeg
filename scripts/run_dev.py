"""Sequential durable development jobs; stop immediately on a failed stage."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
os.chdir(root)
index = "data/prepared-24/index.json"
jobs = [["baseline", "--index", index, "--run", "runs/dev24-baseline-s17"],
        ["profile", "--index", index]]
for mode in ("regional", "auxiliary", "pocket"):
    jobs.append(["train", "--index", index, "--run", f"runs/dev24-{mode}-s17", "--config", f"configs/dev-{mode}.json"])
for args in jobs:
    print("RUN", " ".join(args), flush=True)
    subprocess.run([sys.executable, "-u", "-m", "pcp", *args], check=True)
print("ALL DEVELOPMENT JOBS COMPLETE", flush=True)
