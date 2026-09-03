import pandas as pd
from rms_mlstm.features import add_core_features, deviation_index

def test_core_features():
    df = pd.DataFrame({"xtempmotor1_1": [70.0, 71.0], "xtempmotor1_2": [69.0, 75.0],
                       "xspeedloco": [60.0, 60.0], "xtempmotor2_1": [70, 70],
                       "xtempmotor3_1": [70, 70], "xtempmotor2_2": [70, 70], "xtempmotor3_2": [70, 70]})
    out = add_core_features(df)
    assert out["xtempmotor_max"].tolist() == [70.0, 75.0]
    assert out["Temp_Diff_Motor_1"].tolist() == [1.0, 4.0]

def test_deviation_smooths_spike():
    actual = pd.Series([70.0, 70.0, 90.0, 70.0, 70.0])
    pred = pd.Series([70.0, 70.0, 70.0, 70.0, 70.0])
    d = deviation_index(actual, pred, span=3)
    assert d.iloc[2] < 20.0  # EWMA damps single-sample spike
