"""03: score Arm-A (MLSTM residual) + Rules on a TEST window. Test-only; never tunes thresholds.

Reads: <run-dir>/mlstm.pt + scaler.json + calib.json (healthy-only) + configs alarm contract.
Writes: <out-dir>/alarms.csv + onsets.json + report.json

- calib.json MUST be status=ready (healthy calib). Refuses test-derived thresholds.
- Reports candidate/warning/critical onsets separately + per-case leads (Fix 4/5).
- Also scores deterministic Rule Engine standalone (esp. 30751 cutout check).
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, "src")
from rms_mlstm.config import load_config
from rms_mlstm.features import add_core_features, deviation_index
from rms_mlstm.model_mlstm import build_model, make_sequences
from rms_mlstm.calibrate import HealthyCalibrator
from rms_mlstm.evaluate import onsets_per_level, per_case_report
from rms_mlstm.rules import score_rules_df


def _load_input(path: str):
    import pandas as pd
    p = Path(path)
    if p.is_dir():
        files = sorted([*p.glob("*.parquet"), *p.glob("*.csv")])
        dfs = [pd.read_parquet(f) if f.suffix == ".parquet" else pd.read_csv(f) for f in files]
        return pd.concat(dfs, ignore_index=True)
    return pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)


def main():
    import numpy as np
    import pandas as pd
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/experiment.yaml")
    ap.add_argument("--run-dir", required=True, help="experiments/<run> with mlstm.pt+scaler+calib")
    ap.add_argument("--input", required=True, help="TEST window parquet/csv (failure case or unseen healthy)")
    ap.add_argument("--loco", default="unknown")
    ap.add_argument("--failure-ts", default=None, help="Owner failure timestamp ISO, e.g. 2024-12-09T14:00:00")
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args()
    cfg = load_config(a.config)
    run = Path(a.run_dir)

    ckpt = __import__("torch").load(run / "mlstm.pt", map_location="cpu", weights_only=False)
    scaler = json.loads((run / "scaler.json").read_text())
    calib = json.loads((run / "calib.json").read_text())
    if calib.get("status") != "ready" or not calib.get("sorted_sample"):
        raise SystemExit("REFUSED: calib.json not ready — thresholds must come from held-out HEALTHY, never test. "
                         "Re-run 02 with --calib <healthy>.")
    order: list = scaler["feature_order"]
    mu = np.asarray(scaler["mean"], dtype="float64")
    sd = np.asarray(scaler["std"], dtype="float64")
    med = np.asarray(scaler["median_impute"], dtype="float64")
    lb, hz = ckpt["lookback"], ckpt["horizon"]

    import torch
    model = build_model(len(order), ckpt["model_cfg"]["hidden_size"],
                        ckpt["model_cfg"]["num_layers"], ckpt["model_cfg"]["dropout"])
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

    df = add_core_features(_load_input(a.input))
    if "devicetime" not in df.columns:
        raise SystemExit("input needs devicetime column")
    df["devicetime"] = pd.to_datetime(df["devicetime"])
    df = df.sort_values("devicetime").reset_index(drop=True)
    for c in order:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")
    mat = df[order].to_numpy(dtype="float64")
    mat = np.where(np.isnan(mat), med, mat)
    Xn = (mat - mu) / sd
    X, y = make_sequences(Xn, lookback=lb, horizon=hz)
    ts_seq = df["devicetime"].iloc[lb + hz - 1:].reset_index(drop=True)

    with torch.no_grad():
        preds = []
        for i in range(0, len(X), 4096):
            preds.append(model(torch.from_numpy(X[i:i + 4096])).cpu().numpy())
    pred = np.concatenate(preds) if preds else np.array([])
    actual_deg = y * sd[0] + mu[0]
    pred_deg = pred * sd[0] + mu[0]
    dev = deviation_index(pd.Series(actual_deg), pd.Series(pred_deg), span=cfg["deviation"]["ewma_span"])

    cal = HealthyCalibrator().fit(np.asarray(calib["sorted_sample"], dtype=float))
    score01 = pd.Series(cal.to_01_series(dev.to_numpy()))

    # Rules on Gold rows aligned to seq timestamps
    gold_seq = df.iloc[lb + hz - 1:].reset_index(drop=True)
    resid01_aligned = score01.copy()
    resid01_aligned.index = gold_seq.index
    rule01 = score_rules_df(gold_seq, resid01_aligned)

    out_dir = Path(a.out_dir or (run / f"score_{a.loco}"))
    out_dir.mkdir(parents=True, exist_ok=True)
    alarms = pd.DataFrame({"devicetime": ts_seq, "actual_deg": actual_deg, "pred_deg": pred_deg,
                           "resid_deg": np.abs(actual_deg - pred_deg), "dev": dev.to_numpy(),
                           "score01": score01.to_numpy(), "rule01": rule01.to_numpy()})
    alarms.to_csv(out_dir / "alarms.csv", index=False)

    onsets_model = onsets_per_level(ts_seq, score01, cfg["alarm"])
    onsets_rule = onsets_per_level(ts_seq, rule01, cfg["alarm"])
    (out_dir / "onsets.json").write_text(json.dumps(
        {"model": {k: (v.isoformat() if v is not None else None) for k, v in onsets_model.items()},
         "rules": {k: (v.isoformat() if v is not None else None) for k, v in onsets_rule.items()}}, indent=2))

    failure_ts = datetime.fromisoformat(a.failure_ts) if a.failure_ts else None
    report = {"loco": str(a.loco), "input": str(a.input), "run": str(run),
              "model": per_case_report(str(a.loco), onsets_model, failure_ts),
              "rules": per_case_report(str(a.loco), onsets_rule, failure_ts),
              "note": "research detection only; Critical->withdrawal needs separate operational approval"}
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"wrote {out_dir}/alarms.csv ({len(alarms)} rows) + onsets.json + report.json")


if __name__ == "__main__":
    main()
