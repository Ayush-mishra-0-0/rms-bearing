"""Determinism + run manifest. Every run is traceable."""
from __future__ import annotations
import hashlib, json, random
from datetime import datetime
from pathlib import Path
import numpy as np

def set_seed(seed: int) -> None:
    random.seed(seed); np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass

def config_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]

def write_run_manifest(out_dir: str | Path, cfg: dict, extra: dict | None = None) -> Path:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    manifest = {"timestamp": datetime.now().isoformat(timespec="seconds"),
                "config_hash": config_hash(cfg), "config": cfg, **(extra or {})}
    p = out / "run_manifest.json"
    p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return p
