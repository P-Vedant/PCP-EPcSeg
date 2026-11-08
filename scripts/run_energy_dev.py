"""Predeclared development controls; no test tuning or test evaluation."""
import json
import os
from pathlib import Path
import subprocess
import sys
os.chdir(Path(__file__).resolve().parents[1])
base=json.loads(Path("configs/dev-if-regional.json").read_text())
for tag in ("energy-bounded","energy-concat","energy-mask-only","if-shuffled"):
    config=json.loads(json.dumps(base))
    config["model"]["use_energy"]=tag!="if-shuffled"
    config["model"]["energy_mode"]="concat" if tag=="energy-concat" else "bounded"
    if tag=="energy-mask-only": config["energy_values"]="zero"
    if tag=="if-shuffled": config["shuffle_if"]=True
    path=Path(f"configs/dev-{tag}.json"); path.write_text(json.dumps(config,indent=2)+"\n")
    subprocess.run([sys.executable,"-u","-m","pcp","train","--index","data/energy-24/index.json",
                    "--run",f"runs/dev24-{tag}-s17","--config",str(path)],check=True)
print("ENERGY AND SHUFFLE CONTROLS COMPLETE",flush=True)
