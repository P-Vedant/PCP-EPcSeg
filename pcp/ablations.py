"""Deterministic input controls shared by fitting and checkpoint evaluation."""
import hashlib
import numpy as np


def apply_controls(records,config):
    if not config.get("shuffle_if") and config.get("energy_values")!="zero": return records
    altered=[]
    for r,z in records:
        z=dict(z)
        if config.get("shuffle_if") and "if_features" in z:
            seed=config["seed"]+int(hashlib.sha256(r["id"].encode()).hexdigest()[:8],16)
            permutation=np.random.default_rng(seed).permutation(len(z["x"]))
            z["if_features"]=z["if_features"][permutation]
            z["if_mask"]=z["if_mask"][permutation]
        if config.get("energy_values")=="zero" and "energy" in z:
            z["energy"]=np.zeros_like(z["energy"])
        altered.append((r,z))
    return altered
