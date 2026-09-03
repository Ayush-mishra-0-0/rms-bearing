"""01: extract read-only window -> data/interim. Example: python pipelines/01_extract_windows.py --loco 37282 --start "2024-12-03 00:00:00" --end "2024-12-10 00:00:00" """
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, "src")
from rms_mlstm.data import fetch_window
from rms_mlstm.features import add_core_features, resample_1min
from rms_mlstm.config import load_config

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--loco", required=True); p.add_argument("--start", required=True); p.add_argument("--end", required=True)
    p.add_argument("--config", default="configs/experiment.yaml"); p.add_argument("--out", default=None)
    a = p.parse_args()
    cfg = load_config(a.config)
    df = fetch_window(a.loco, a.start, a.end, cfg["data"]["table"])
    df = resample_1min(add_core_features(df))
    out = Path(a.out or f"data/interim/{a.loco}_{a.start[:10]}_1min.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df)} 1-min rows -> {out}")

if __name__ == "__main__":
    main()
