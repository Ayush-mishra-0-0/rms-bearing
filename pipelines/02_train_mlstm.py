"""02: train MLSTM on healthy parquet -> experiments/<run>/mlstm.pt. Healthy only."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, "src")
from rms_mlstm.config import load_config
from rms_mlstm.utils import set_seed, write_run_manifest

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/experiment.yaml")
    p.add_argument("--train", required=True, help="parquet or folder of healthy 1-min data")
    p.add_argument("--run-dir", default=None)
    a = p.parse_args()
    cfg = load_config(a.config); set_seed(cfg["seed"])
    from datetime import datetime
    run_dir = Path(a.run_dir or f"experiments/{datetime.now():%Y%m%d_%H%M%S}_{cfg['run_name']}")
    write_run_manifest(run_dir, cfg, {"stage": "train_mlstm", "train": a.train})
    print(f"Manifest -> {run_dir}/run_manifest.json")
    print("TODO: fit MLSTM via src/rms_mlstm/model_mlstm.py on healthy data only. Val on 37282/30532.")

if __name__ == "__main__":
    main()
