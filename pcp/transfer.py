"""Explicit file selection, SHA-256 validation, no archive path traversal."""
import json
import os
import zipfile
from pathlib import Path, PurePosixPath
from .io import sha256


def export_bundle(files, out):
    root = Path.cwd().resolve()
    selected = []
    for name in files:
        p = Path(name).resolve()
        rel = p.relative_to(root)
        if not p.is_file() or rel.parts[0] not in ("data", "cache", "runs", "outputs"):
            raise ValueError("only explicit data/cache/runs/outputs files may be exported")
        selected.append((p, rel.as_posix()))
    if len({r for _,r in selected}) != len(selected): raise ValueError("duplicate file")
    manifest = {r:sha256(p) for p,r in selected}
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    if Path(out).exists(): raise FileExistsError(out)
    with zipfile.ZipFile(out+".tmp", "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p,r in selected: z.write(p,r)
        z.writestr("SHA256.json", json.dumps(manifest, indent=2))
    os.replace(out+".tmp", out)
    return {"archive":out,"sha256":sha256(out),"files":len(selected)}


def import_bundle(archive, destination):
    import hashlib
    root = Path(destination).resolve()
    # Validate EVERYTHING before creating or replacing any output file.
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names)!=len(set(names)): raise ValueError("duplicate archive names")
        manifest = json.loads(z.read("SHA256.json"))
        if set(names)!=(set(manifest)|{"SHA256.json"}): raise ValueError("unexpected members")
        for name,digest in manifest.items():
            rel = PurePosixPath(name)
            if rel.is_absolute() or ".." in rel.parts or "\\" in name or ":" in name:
                raise ValueError("unsafe archive path")
            path = (root/Path(*rel.parts)).resolve()
            path.relative_to(root)
            if path.exists(): raise FileExistsError(path)
            if hashlib.sha256(z.read(name)).hexdigest()!=digest: raise ValueError("hash mismatch")
        for name in manifest:
            path = root/Path(*PurePosixPath(name).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path,"xb") as f: f.write(z.read(name))
    return {"imported":len(manifest),"destination":str(root)}
