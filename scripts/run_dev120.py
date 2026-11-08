"""Bounded larger development experiment; resumes completed stages by artifact checks."""
import json
import os
from pathlib import Path
import subprocess
import sys
os.chdir(Path(__file__).resolve().parents[1])
py=sys.executable
def run(args):
    print("RUN", " ".join(args),flush=True)
    subprocess.run([py,"-u",*args],check=True)
index="data/prepared-120/index.json"
if not Path(index).exists(): raise RuntimeError("Wait for prepare120 to finish; do not launch a duplicate download")
run(["-m","pcp","audit","--index",index])
features="data/features-120/index.json"
if not Path(features).exists(): run(["-m","pcp","features","--index",index,"--output","data/features-120"])
if not Path("runs/dev120-baseline-s17/metrics.json").exists():
    run(["-m","pcp","baseline","--index",index,"--run","runs/dev120-baseline-s17"])
if not Path("outputs/profile-120.json").exists(): run(["-m","pcp","profile","--index",index,"--out","outputs/profile-120.json"])
for seed in (17,23,47):
    for mode in ("regional","auxiliary","pocket"):
        config=json.loads(Path(f"configs/dev-if-{mode}.json").read_text())
        config.update(seed=seed,epochs=20)
        path=Path(f"configs/dev120-if-{mode}-s{seed}.json")
        path.write_text(json.dumps(config,indent=2)+"\n")
        out=Path(f"runs/dev120-if-{mode}-s{seed}")
        if (out/"metrics.json").exists(): continue
        args=["-m","pcp","train","--index",features,"--run",str(out),"--config",str(path)]
        if (out/"last.pt").exists(): args.extend(["--resume",str(out/"last.pt")])
        run(args)
print("DEV120 THREE-SEED STAGE COMPLETE",flush=True)
