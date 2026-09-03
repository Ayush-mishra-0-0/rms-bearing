"""Residual-distribution test for case 42728 (closeout experiment).

Question: does the distribution of r_t = I_t - Ihat_t change around the
abnormal period, using the existing 42728 telemetry only?

Chain under test:
  Expected electrical behaviour -> residual -> thermal response -> cross-motor deviation

Method (deliberately NOT spectral kurtosis, NOT a new model, NOT a pipeline):
  Ihat = median(I_baseline | speed-bin, accel-bin), baseline = 27-Jul..03-Aug,
  traction-active only (ltedemand=1). Same bins as test_B_plus.py so the two
  scripts stay comparable. Thermal decoupling (dT = TM1_2 - other5 mean,
  stuck 76C channel excluded) is reported alongside, not mixed into r_t.

Reads:  telemetry_42728_2026_rds.json.csv (same directory, 1-s cadence)
Stdlib only (no pandas/numpy/scipy), matching the other case_42728 scripts.
Run:    python residual_distribution_42728.py
"""

import csv
import os
from datetime import datetime

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "telemetry_42728_2026_rds.json.csv")


def parse(s):
    try:
        return datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def med(vals):
    vals = sorted(vals)
    if not vals:
        return float("nan")
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2


def pct(vals, p):
    vals = sorted(vals)
    if not vals:
        return float("nan")
    k = int((len(vals) - 1) * p)
    return vals[k]


def stdev(vals):
    n = len(vals)
    if n < 2:
        return float("nan")
    m = sum(vals) / n
    return (sum((v - m) ** 2 for v in vals) / (n - 1)) ** 0.5


def ks_2sample(a, b):
    """Two-sample Kolmogorov-Smirnov D statistic, hand-rolled (no p-value)."""
    a = sorted(a)
    b = sorted(b)
    if not a or not b:
        return float("nan")
    i = j = 0
    na, nb = len(a), len(b)
    cdf_a = cdf_b = 0.0
    d = 0.0
    while i < na or j < nb:
        nxt = None
        if j >= nb or (i < na and a[i] < b[j]):
            nxt = a[i]
        elif i >= na or (j < nb and b[j] < a[i]):
            nxt = b[j]
        else:
            nxt = a[i]
        while i < na and a[i] <= nxt:
            i += 1
            cdf_a = i / na
        while j < nb and b[j] <= nxt:
            j += 1
            cdf_b = j / nb
        d = max(d, abs(cdf_a - cdf_b))
    return d


TCOLS = ["xtempmotor1_1", "xtempmotor2_1", "xtempmotor3_1",
         "xtempmotor1_2", "xtempmotor2_2", "xtempmotor3_2"]


def other5_mean(r):
    vals = [f(r[c]) for c in TCOLS]
    ok = [v for v in (vals[:3] + vals[4:]) if v is not None and v < 75.99]
    return sum(ok) / len(ok) if ok else None


V_BINS = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 1e9)]
A_BINS = [(-1e9, -0.3), (-0.3, -0.1), (-0.1, 0.1), (0.1, 0.3), (0.3, 1e9)]

PER_BASE = ((27, 7), (3, 8))


def in_period(t, p):
    (d1, m1), (d2, m2) = p
    return datetime(2026, m1, d1) <= t <= datetime(2026, m2, d2, 23, 59, 59)


def main():
    if not os.path.exists(PATH):
        print("MISSING: %s" % PATH)
        print("Place the 27-Jul..10-Aug 2026 RDSOJson extraction next to this script, then re-run.")
        return

    rows = []
    with open(PATH, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    print("Rows: %d" % len(rows))

    recs = []
    for r in rows:
        t = parse(r.get("devicetime"))
        v = f(r.get("xspeedloco"))
        ip = f(r.get("xiprim_1"))
        lte = f(r.get("ltedemand"))
        if t is None or v is None or ip is None or lte is None:
            continue
        t12 = f(r.get("xtempmotor1_2"))
        om = other5_mean(r)
        recs.append([t, v, ip, lte, t12, om])
    recs.sort(key=lambda x: x[0])

    for i in range(1, len(recs)):
        dt = (recs[i][0] - recs[i - 1][0]).total_seconds()
        if 0 < dt <= 5:
            a = (recs[i][1] - recs[i - 1][1]) * 1000.0 / 3600.0 / dt
            recs[i - 1].append(a)
        else:
            recs[i - 1].append(None)
    recs[-1].append(None)

    base = {}
    for t, v, ip, lte, t12, om, a in recs:
        if lte != 1 or a is None or not in_period(t, PER_BASE):
            continue
        vb = next((b for b in V_BINS if b[0] <= v < b[1]), None)
        ab = next((b for b in A_BINS if b[0] <= a < b[1]), None)
        if vb is None or ab is None:
            continue
        base.setdefault((vb, ab), []).append(ip)
    model = {k: med(v) for k, v in base.items() if v}
    print("Baseline bins covered: %d/%d (27-Jul..03-Aug, lte=1)" % (len(model), len(V_BINS) * len(A_BINS)))

    def residual(t, v, ip, a):
        vb = next((b for b in V_BINS if b[0] <= v < b[1]), None)
        ab = next((b for b in A_BINS if b[0] <= a < b[1]), None)
        if vb is None or ab is None:
            return None
        m = model.get((vb, ab))
        return ip - m if m is not None else None

    periods = [
        ("BASELINE 27Jul-03Aug", PER_BASE, None),
        ("06-Aug", ((6, 8), (6, 8)), None),
        ("07-Aug", ((7, 8), (7, 8)), None),
        ("07/08 10-11 event-hr", ((7, 8), (7, 8)), (10, 11)),
        ("07/08 14-20 post", ((7, 8), (7, 8)), (14, 20)),
        ("08/08 15-17 pre-fail", ((8, 8), (8, 8)), (15, 17)),
    ]

    pooled_base = []
    per = {}
    for nm, p, hrs in periods:
        rs, dts = [], []
        for t, v, ip, lte, t12, om, a in recs:
            if lte != 1 or a is None or not in_period(t, p):
                continue
            if hrs is not None and not (hrs[0] <= t.hour <= hrs[1]):
                continue
            r = residual(t, v, ip, a)
            if r is None:
                continue
            rs.append(r)
            if t12 is not None and om is not None:
                dts.append(t12 - om)
        per[nm] = (rs, dts)
        if nm.startswith("BASELINE"):
            pooled_base = rs

    print()
    print("=" * 86)
    print("RESIDUAL DISTRIBUTION r_t = I_obs - Ihat(v,a), traction-active only")
    print("Caveat: BASELINE row is in-sample (reference, not a test). Flag n<30.")
    print("=" * 86)
    print("%-22s %6s %8s %8s %8s %8s %8s %9s %9s" %
          ("period", "n", "med", "p10", "p25", "p75", "p90", "IQR", "P(|r|>30)"))
    for nm, _p, _h in periods:
        rs, _d = per[nm]
        if not rs:
            print("%-22s %6d  (no matched rows)" % (nm, 0))
            continue
        iqr = pct(rs, 0.75) - pct(rs, 0.25)
        tail = sum(1 for x in rs if abs(x) > 30.0) / len(rs)
        flag = "  <-- n<30" if len(rs) < 30 else ""
        print("%-22s %6d %+8.1f %+8.1f %+8.1f %+8.1f %+8.1f %8.1f %9.3f%s" %
              (nm, len(rs), med(rs), pct(rs, 0.10), pct(rs, 0.25),
               pct(rs, 0.75), pct(rs, 0.90), iqr, tail, flag))

    print()
    print("KS distance of each period vs pooled BASELINE residuals (D in [0,1], no p-value):")
    for nm, _p, _h in periods:
        if nm.startswith("BASELINE"):
            continue
        rs, _d = per[nm]
        print("  %-22s n=%-5d D=%5.3f%s" %
              (nm, len(rs), ks_2sample(pooled_base, rs),
               "  <-- n<30, directional only" if len(rs) < 30 else ""))

    print()
    print("Thermal decoupling alongside (dT = TM1_2 - other5, deg C):")
    for nm, _p, _h in periods:
        _rs, dts = per[nm]
        if not dts:
            continue
        print("  %-22s n=%-5d dT med=%+6.1f  IQR=%5.1f" %
              (nm, len(dts), med(dts), pct(dts, 0.75) - pct(dts, 0.25)))

    print()
    print("Rolling hourly residual median/IQR, 06..08-Aug (traction-active):")
    hrs = sorted({(t.day, t.hour) for t, v, ip, lte, t12, om, a in recs
                  if t.month == 8 and t.day in (6, 7, 8)})
    for d, h in hrs:
        rs = [residual(t, v, ip, a) for t, v, ip, lte, t12, om, a in recs
              if t.month == 8 and t.day == d and t.hour == h
              and lte == 1 and a is not None
              and residual(t, v, ip, a) is not None]
        if len(rs) < 10:
            continue
        print("  08/%02d %02d:00  n=%-5d med=%+7.1f  IQR=%6.1f" %
              (d, h, len(rs), med(rs), pct(rs, 0.75) - pct(rs, 0.25)))


if __name__ == "__main__":
    main()
