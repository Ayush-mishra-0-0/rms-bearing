"""FIX 1: common calibrated 0-1 risk scale.
Raw arm scores (residual / recon error / elec resid) live on different scales.
Map each through ECDF of CALIB-HEALTHY scores => P(anomalous | healthy) in [0,1].
Fusion then averages comparable quantities, not arbitrary normalizations.
"""
from __future__ import annotations
import numpy as np


class HealthyCalibrator:
    """Fit on calib-healthy raw scores ONLY. Never on test failures."""

    def __init__(self):
        self.sorted_: np.ndarray | None = None

    def fit(self, healthy_raw) -> "HealthyCalibrator":
        arr = np.asarray([float(x) for x in healthy_raw if x is not None and np.isfinite(float(x))])
        if len(arr) == 0:
            raise ValueError("empty healthy calibration scores")
        self.sorted_ = np.sort(arr)
        return self

    def to_01(self, raw) -> float:
        """ECDF: fraction of healthy <= raw. Higher = more anomalous."""
        if self.sorted_ is None:
            raise RuntimeError("call fit() on calib-healthy first")
        r = float(raw)
        if not np.isfinite(r):
            return 0.0
        return float(np.searchsorted(self.sorted_, r, side="right") / len(self.sorted_))

    def to_01_series(self, raws):
        return [self.to_01(r) for r in raws]

    def threshold_for_q(self, q: float) -> float:
        if self.sorted_ is None:
            raise RuntimeError("call fit() first")
        return float(np.quantile(self.sorted_, q))
