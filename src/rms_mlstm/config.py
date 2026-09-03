"""Single loader for configs/experiment.yaml + .env. No hidden defaults."""
from __future__ import annotations
from pathlib import Path
import yaml

def load_config(path: str | Path = "configs/experiment.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert cfg.get("seed") is not None, "seed required for reproducibility"
    return cfg
