"""03: score deviation -> iForest alarms. Validates lead-time on 37282/30532."""
from __future__ import annotations
import argparse
import sys
sys.path.insert(0, "src")
from rms_mlstm.config import load_config

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/experiment.yaml"); p.add_argument("--input", required=True)
    a = p.parse_args()
    cfg = load_config(a.config)
    print(f"Score {a.input} with EWMA span={cfg['deviation']['ewma_span']}, q={cfg['iforest']['threshold_quantile']}")
    print("TODO: load mlstm.pt, predict, deviation_index(), iForest, write alarms.csv + lead-time.")

if __name__ == "__main__":
    main()
