"""Download only pinned author code/weights needed for local inference."""
import os
from pathlib import Path
from pcp.io import download,atomic_json,sha256
os.chdir(Path(__file__).resolve().parents[1])
sources=[("ProteinMPNN","dauparas/ProteinMPNN","8907e6671bfbfc92303b5f79c4b5e6ce47cdef57",
          ["LICENSE","protein_mpnn_utils.py","vanilla_model_weights/v_48_020.pt"]),
         ("PocketMiner","Mickdub/gvp","187062df3c94127e991669768009141a08fd5d8b",
          ["LICENSE","src/models.py","src/gvp.py","src/util.py","src/validate_performance_on_xtals.py",
           "src/xtal_predict.py","models/pocketminer.index","models/pocketminer.data-00000-of-00001"])]
manifest=[]
for name,repo,revision,files in sources:
    for file in files:
        path=Path("external")/name/file
        url=f"https://raw.githubusercontent.com/{repo}/{revision}/{file}"
        download(url,path)
        manifest.append({"path":str(path),"url":url,"sha256":sha256(path)})
atomic_json("external/MANIFEST.json",manifest)
print("Pinned external files verified/present:",len(manifest))
