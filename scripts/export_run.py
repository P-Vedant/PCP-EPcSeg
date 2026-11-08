"""Export complete selected cached data and checkpoint state, with verified hashes."""
import argparse
import json
from pathlib import Path
from pcp.io import sha256
from pcp.transfer import export_bundle
p=argparse.ArgumentParser(); p.add_argument("--run",required=True); p.add_argument("--index",required=True); p.add_argument("--out",required=True)
a=p.parse_args(); index=json.loads(Path(a.index).read_text())
files=[a.index]
for r in index["records"]:
    if sha256(r["path"])!=r["sha256"]:raise ValueError(f"changed shard: {r['id']}")
    files.append(r["path"])
for name in ("best.pt","last.pt","config.json","provenance.json","metrics.json","hardware.json"):
    path=Path(a.run)/name
    if not path.is_file():raise FileNotFoundError(path)
    files.append(str(path))
print(json.dumps(export_bundle(files,a.out),indent=2))
