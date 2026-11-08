from __future__ import annotations
import hashlib
import json
import os
import platform
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, allow_nan=False)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def download(url, path):
    path = Path(path)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".download")
    try:
        with urllib.request.urlopen(url, timeout=90) as source, os.fdopen(fd, "wb") as out:
            while chunk := source.read(1024 * 1024):
                out.write(chunk)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return path


def revision():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def manifest(event, **fields):
    row = {"time": now(), "event": event, "commit": revision(), **fields}
    # Only machine A writes the root manifest; B uses a separate checkout.
    with open("RUN_MANIFEST.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row, allow_nan=False) + "\n")


def hardware():
    import psutil
    import torch
    result = {"os": platform.platform(), "cpu": platform.processor(),
              "ram_bytes": psutil.virtual_memory().total,
              "free_disk_bytes": psutil.disk_usage(".").free,
              "python": platform.python_version(), "torch": torch.__version__,
              "cuda_runtime": torch.version.cuda, "cuda_available": torch.cuda.is_available()}
    if torch.cuda.is_available():
        result.update(gpu=torch.cuda.get_device_name(),
                      vram_bytes=torch.cuda.get_device_properties(0).total_memory,
                      capability=list(torch.cuda.get_device_capability()),
                      arch_list=torch.cuda.get_arch_list())
    return result
