"""MLSTM predictor: 40min in -> 6min ahead bearing temp. LSTM stack (paper compared 3/4/5 layers)."""
from __future__ import annotations

def build_model(n_features: int, hidden_size: int = 64, num_layers: int = 3, dropout: float = 0.1):
    import torch.nn as nn
    class MLSTM(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(n_features, hidden_size, num_layers=num_layers,
                                dropout=dropout if num_layers > 1 else 0.0, batch_first=True)
            self.head = nn.Linear(hidden_size, 1)
        def forward(self, x):
            out, _ = self.lstm(x)
            return self.head(out[:, -1, :]).squeeze(-1)
    return MLSTM()

def make_sequences(values, lookback: int = 40, horizon: int = 6):
    import numpy as np
    X, y = [], []
    for i in range(len(values) - lookback - horizon + 1):
        X.append(values[i:i+lookback, :])
        y.append(values[i+lookback+horizon-1, 0])  # target col 0 = xtempmotor_max
    return np.asarray(X, dtype="float32"), np.asarray(y, dtype="float32")
