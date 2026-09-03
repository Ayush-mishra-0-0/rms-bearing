"""02: train Arm-A MLSTM (Wang FA-LSTM) on HEALTHY 1-min Gold only.
Emits: experiments/<run>/mlstm.pt + scaler.json + calib.json + run_manifest.json

- Train = healthy only. Failure locos (37282/30532/30751) must NEVER appear in --train/--calib.
- calib.json thresholds come from --calib healthy ONLY, never test failures (bake-off Fix 3).
- If --calib omitted, calib.json is a PENDING stub — 03 scoring must refuse to set thresholds from test.
"""
from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path
import sys
sys.path.insert(0, "src")
from rms_mlstm.config import load_config
from rms_mlstm.utils import set_seed, config_hash
from rms_mlstm.features import add_core_features
from rms_mlstm.model_mlstm import build_model, make_sequences
from rms_mlstm.calibrate import HealthyCalibrator


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()[:12]
    except Exception:
        return "unknown"


def _load_frames(path: str) -> "pd.DataFrame":
    import pandas as pd
    p = Path(path)
    files: list[Path] = []
    if p.is_dir():
        files = sorted([*p.glob("*.parquet"), *p.glob("*.csv")])
    else:
        files = [p]
    if not files:
        raise FileNotFoundError(f"no parquet/csv found at {path}")
    dfs = []
    for f in files:
        if f.suffix == ".parquet":
            dfs.append(pd.read_parquet(f))
        else:
            dfs.append(pd.read_csv(f))
    return pd.concat(dfs, ignore_index=True)


def _prep(df, target: str, covariates: list[str]):
    """Gold features (idempotent) -> numeric matrix [target, *covariates]. Drops target-null rows."""
    import pandas as pd
    import numpy as np
    df = add_core_features(df)
    cols = [target, *[c for c in covariates if c != target]]
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=[target]).reset_index(drop=True)
    # Fail-closed: refuse failure-loco contamination if locoid present
    if "locoid" in df.columns:
        bad = set(str(x) for x in df["locoid"].dropna().unique()) & {"37282", "30532", "30751"}
        if bad:
            raise ValueError(f"REFUSED: failure locos {bad} in healthy train/calib input")
    return df, cols


def _fit_scaler(mat):
    import numpy as np
    mu = mat.mean(axis=0)
    sd = mat.std(axis=0)
    sd[sd == 0] = 1.0
    return mu.astype("float64"), sd.astype("float64")


def _predict_batches(model, Xn, batch: int = 4096):
    import torch
    import numpy as np
    model.eval()
    outs = []
    with torch.no_grad():
        for i in range(0, len(Xn), batch):
            xb = torch.from_numpy(np.asarray(Xn[i:i + batch], dtype="float32"))
            outs.append(model(xb).cpu().numpy())
    return np.concatenate(outs) if outs else np.array([])


def main():
    import numpy as np
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/experiment.yaml")
    p.add_argument("--train", required=True, help="parquet file or folder of HEALTHY 1-min Gold")
    p.add_argument("--calib", default=None, help="optional parquet/folder of held-out HEALTHY for calib.json")
    p.add_argument("--run-dir", default=None)
    p.add_argument("--epochs", type=int, default=None)
    p.add_argument("--max-train-seqs", type=int, default=None, help="cap sequences for smoke tests")
    a = p.parse_args()
    cfg = load_config(a.config)
    set_seed(cfg["seed"])

    # Fail-closed: never train/calib on known failure cases (path guard + locoid guard in _prep).
    # 03 scoring uses failure windows for TEST only, never here.
    for label, val in (("--train", a.train), ("--calib", a.calib)):
        if val and any(bad in str(val) for bad in ("37282", "30532", "30751")):
            raise ValueError(f"REFUSED: {label}={val} looks like a failure case; train/calib must be healthy only")

    from datetime import datetime
    run_dir = Path(a.run_dir or f"experiments/{datetime.now():%Y%m%d_%H%M%S}_{cfg['run_name']}")
    run_dir.mkdir(parents=True, exist_ok=True)

    tgt = cfg["data"]["target"]
    covs = cfg["data"]["covariates"]
    lb, hz = cfg["data"]["lookback_min"], cfg["data"]["horizon_min"]
    epochs = a.epochs or cfg["model"]["epochs"]
    bs = cfg["model"]["batch_size"]
    lr = cfg["model"]["lr"]

    # --- Train ---
    df_tr, order = _prep(_load_frames(a.train), tgt, covs)
    mat = df_tr[order].to_numpy(dtype="float64")
    # median-impute covariates (target already dropna); record for inference parity
    med = np.nanmedian(mat, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    mat = np.where(np.isnan(mat), med, mat)
    mu, sd = _fit_scaler(mat)
    Xn = (mat - mu) / sd
    X, y = make_sequences(Xn, lookback=lb, horizon=hz)
    if a.max_train_seqs and len(X) > a.max_train_seqs:
        X, y = X[:a.max_train_seqs], y[:a.max_train_seqs]
    print(f"train rows={len(df_tr)} seqs={len(X)} feats={order}")

    import torch
    torch.manual_seed(cfg["seed"])
    model = build_model(len(order), cfg["model"]["hidden_size"],
                        cfg["model"]["num_layers"], cfg["model"]["dropout"])
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = torch.nn.MSELoss()
    dl = torch.utils.data.DataLoader(
        torch.utils.data.TensorDataset(torch.from_numpy(X), torch.from_numpy(y)),
        batch_size=bs, shuffle=True)
    for ep in range(1, epochs + 1):
        model.train()
        tot = 0.0
        for xb, yb in dl:
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            tot += float(loss) * len(xb)
        print(f"epoch {ep}/{epochs} mse={tot / len(X):.4f}", flush=True)

    torch.save({"state_dict": model.state_dict(), "feature_order": order,
                "lookback": lb, "horizon": hz,
                "model_cfg": cfg["model"], "gold_version": cfg.get("gold_version", "v1")},
               run_dir / "mlstm.pt")
    (run_dir / "scaler.json").write_text(json.dumps(
        {"feature_order": order, "mean": mu.tolist(), "std": sd.tolist(),
         "median_impute": med.tolist()}, indent=2))
    print(f"saved mlstm.pt + scaler.json -> {run_dir}")

    # --- Calib (healthy only) ---
    calib_out: dict
    if a.calib:
        from rms_mlstm.features import deviation_index
        import pandas as pd
        df_cb, _ = _prep(_load_frames(a.calib), tgt, covs)
        m_cb = df_cb[order].to_numpy(dtype="float64")
        m_cb = np.where(np.isnan(m_cb), med, m_cb)
        Xn_cb = (m_cb - mu) / sd
        Xc, yc = make_sequences(Xn_cb, lookback=lb, horizon=hz)
        pred = _predict_batches(model, Xc)
        # denormalize target (col 0) for interpretable residual in degC
        pred_deg = pred * sd[0] + mu[0]
        actual_deg = yc * sd[0] + mu[0]
        dev = deviation_index(pd.Series(actual_deg), pd.Series(pred_deg),
                              span=cfg["deviation"]["ewma_span"])
        cal = HealthyCalibrator().fit(dev.dropna().to_numpy())
        s = cal.sorted_
        keep = s if len(s) <= 20000 else np.quantile(s, np.linspace(0, 1, 20000))
        calib_out = {"status": "ready", "method": cfg["calibration"]["method"],
                     "source": str(a.calib), "n": int(len(s)),
                     "q90": float(np.quantile(s, 0.90)), "q97": float(np.quantile(s, 0.97)),
                     "q99_raw": float(np.quantile(s, cfg["iforest"]["threshold_quantile"])),
                     "max": float(s.max()), "sorted_sample": [float(x) for x in keep]}
    else:
        calib_out = {"status": "pending",
                     "reason": "no --calib given; thresholds MUST come from held-out healthy, never test failures"}
    (run_dir / "calib.json").write_text(json.dumps(calib_out, indent=2))
    print(f"calib.json status={calib_out['status']}")

    manifest = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "stage": "train_mlstm_armA",
        "git_sha": _git_sha(), "config_hash": config_hash(cfg), "config": cfg,
        "gold_version": cfg.get("gold_version"), "feature_order": order,
        "train": str(a.train), "train_rows": int(len(df_tr)), "train_seqs": int(len(X)),
        "calib": str(a.calib) if a.calib else None,
        "alarm": cfg.get("alarm"), "fusion_primary": cfg.get("fusion_primary"),
        "seed": cfg["seed"], "artifacts": ["mlstm.pt", "scaler.json", "calib.json"],
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Manifest -> {run_dir}/run_manifest.json")


if __name__ == "__main__":
    main()
