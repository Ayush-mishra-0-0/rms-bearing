"""iForest on deviation index. Threshold from healthy val only. Reports false/missed + lead time."""
from __future__ import annotations
import numpy as np

def fit_iforest(dev_healthy, n_estimators: int = 200, max_samples=256, seed: int = 42):
    from sklearn.ensemble import IsolationForest
    clf = IsolationForest(n_estimators=n_estimators, max_samples=max_samples, random_state=seed)
    clf.fit(np.asarray(dev_healthy).reshape(-1, 1))
    return clf

def alarm_threshold(clf, dev_healthy, quantile: float = 0.99) -> float:
    scores = -clf.score_samples(np.asarray(dev_healthy).reshape(-1, 1))
    return float(np.quantile(scores, quantile))
