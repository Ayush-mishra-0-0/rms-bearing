import pandas as pd
from rms_mlstm.features import add_core_features, deviation_index, GOLD_FEATURES

def _base(n=20):
    return pd.DataFrame({
        "xtempmotor1_1": [70.0 + i * 0.1 for i in range(n)],
        "xtempmotor1_2": [69.0] * n,
        "xtempmotor2_1": [70] * n, "xtempmotor3_1": [70] * n,
        "xtempmotor2_2": [70] * n, "xtempmotor3_2": [70] * n,
        "xspeedloco": [60.0] * n, "gpsspeed": [60.0] * n,
        "xiprim_1": [200.0 + (i % 3) for i in range(n)],
        "xuprim_1": [25000.0] * n,
        "ltedemand": [50.0] * n, "lbedemand": [0.0] * n, "mtrcctract1": [1] * n,
        "mvcb_on": [1] * n,
        "bbur1_off": [0] * n, "bbur2_off": [0] * n, "bbur3_off": [0] * n,
        "bstb1_off": [0] * n, "bstb2_off": [0] * n,
        "bflg1_off": [0] * n, "bflg2_off": [0] * n,
        "Vendor": ["Lotus"] * n,
    })

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

def test_gold_v1_all_features_present():
    out = add_core_features(_base())
    missing = [c for c in GOLD_FEATURES if c not in out.columns]
    assert not missing, f"missing Gold v1: {missing}"

def test_gold_op_mode_and_status():
    out = add_core_features(_base())
    assert set(out["op_mode"].unique()) <= {"powering", "regen", "idle", "coast", "unknown"}
    assert out["op_mode"].iloc[0] == "powering"
    assert out["bbur_any_off"].tolist() == [0] * len(out)

def test_gold_no_row_drop_on_missing_optionals():
    df = _base().drop(columns=["bg1tm1_ipvoltage"] if "bg1tm1_ipvoltage" in _base().columns else [])
    n = len(df)
    out = add_core_features(df)
    assert len(out) == n
