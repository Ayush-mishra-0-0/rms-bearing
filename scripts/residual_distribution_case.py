"""Cross-case residual-distribution test (stdlib only, no pandas/numpy/scipy).

Same method as the closed 42728 case (see case_42728/findings_42728.txt
CLOSEOUT + case_42728/residual_distribution_42728.py, whose C# mirror was
executed on 155,089 real rows): per-case own-loco baseline

  Ihat = median(I | speed-bin, accel-bin), traction-active only (ltedemand=1)

then per-period distribution of r_t = I_obs - Ihat(v,a) plus thermal
decoupling dT = suspect-TM minus mean of the other five motors.

Usage (run where Python + extracted telemetry live):
  python scripts/residual_distribution_case.py --csv <telemetry.csv> ^
      --loco 37282 --failure "2024-12-10 05:00:00" ^
      --suspect xtempmotor3_2 ^
      --baseline-start "2024-12-01 00:00:00" --baseline-end "2024-12-07 23:59:59" ^
      --period "08-Dec:2024-12-08 00:00:00:2024-12-08 23:59:59" ^
      --period "09-Dec:2024-12-09 00:00:00:2024-12-09 23:59:59" ^
      --period "10-Dec pre-fail:2024-12-10 00:00:00:2024-12-10 05:00:00" ^
      --roll-start "2024-12-08 00:00:00" --roll-end "2024-12-10 05:00:00"

Suggested anchors (from data/processed/ground_truth_failure_registry.csv):
  37282  fail ~10/12/2024 05:00 (EP withdrawal; axle-6/wheel-12 locked)
         suspect xtempmotor3_2 (bogie2-motor3 = axle 6); dense telemetry.
  30532  fail 04/04/2024 ~05:00 (owner summary 04:25-05:00; candidate EXACT,
         needs validation per README); gear case no.4 opened -> axle 4 ->
         suspect xtempmotor1_2; sparse telemetry, expect n<30 flags.
  30751  SKIP residual (telemetry gap 11-17 Dec swallows pre-failure window).
Healthy controls: same script, same bins, on same-loco earlier windows
(37282 Nov, 30532 Mar) and 1-2 matched healthy locos; expect small KS-D
and no coupled dT excursion.
Schema risk: 2024 telemetry comes from dbo.Lotus_loco_process_signals
(169-col, LotusWireless), not the 2026 RDSOJson Equus feed. The script
aborts listing any missing column - verify xiprim_1/xspeedloco/ltedemand/
xtempmotor*/xvist* against docs/RMS data.xlsx before running.
"""

import argparse
import csv
from datetime import datetime

TMOLS = ["xtempmotor1_1", "xtempmotor2_1", "xtempmotor3_1",
         "xtempmotor1_2", "xtempmotor2_2", "xtempmotor3_2"]
V_BINS = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 1e9)]
A_BINS = [(-1e9, -0.3), (-0.3, -0.1), (-0.1, 0.1), (0.1, 0.3), (0.3, 1e9)]
NEED = ["devicetime", "xspeedloco", "xiprim_1", "ltedemand"] + TMOLS


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
    return vals[len(vals) // 2] if len(vals) % 2 else (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2


def pct(vals, p):
    vals = sorted(vals)
    if not vals:
        return float("nan")
    return vals[int((len(vals) - 1) * p)]


def ks_2sample(a, b):
    a, b = sorted(a), sorted(b)
    if not a or not b:
        return float("nan")
    i = j = 0
    na, nb, ca, cb, d = len(a), len(b), 0.0, 0.0, 0.0
    while i < na or j < nb:
        if j >= nb or (i < na and a[i] < b[j]):
            nxt = a[i]
        elif i >= na or (j < nb and b[j] < a[i]):
            nxt = b[j]
        else:
            nxt = a[i]
        while i < na and a[i] <= nxt:
            i += 1
            ca = i / na
        while j < nb and b[j] <= nxt:
            j += 1
            cb = j / nb
        d = max(d, abs(ca - cb))
    return d


def period_arg(s):
    # name:start:end[:h0-h1], datetimes "YYYY-MM-DD HH:MM:SS" (name: no colons)
    tok = s.split(":")
    if len(tok) < 7:
        raise SystemExit("Bad --period (want name:YYYY-MM-DD HH:MM:SS:YYYY-MM-DD HH:MM:SS[:h0-h1]): " + s)
    name = tok[0]
    start = ":".join(tok[1:4])
    end = ":".join(tok[4:7])
    hrs = None
    if len(tok) > 7 and "-" in tok[7]:
        h0, h1 = tok[7].split("-")
        hrs = (int(h0), int(h1))
    return (name, datetime.strptime(start, "%Y-%m-%d %H:%M:%S"),
            datetime.strptime(end, "%Y-%m-%d %H:%M:%S"), hrs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--loco", default="")
    ap.add_argument("--failure", default="")
    ap.add_argument("--suspect", default="xtempmotor1_2")
    ap.add_argument("--clip", type=float, default=75.99)
    ap.add_argument("--baseline-start", required=True)
    ap.add_argument("--baseline-end", required=True)
    ap.add_argument("--period", action="append", default=[])
    ap.add_argument("--roll-start", default="")
    ap.add_argument("--roll-end", default="")
    a = ap.parse_args()
    b0 = datetime.strptime(a.baseline_start, "%Y-%m-%d %H:%M:%S")
    b1 = datetime.strptime(a.baseline_end, "%Y-%m-%d %H:%M:%S")
    periods = [("BASELINE " + b0.strftime("%d%b") + "-" + b1.strftime("%d%b"), b0, b1, None)]
    periods += [period_arg(p) for p in a.period]
    if a.suspect not in TMOLS:
        raise SystemExit("suspect must be one of: " + ",".join(TMOLS))
    others = [c for c in TMOLS if c != a.suspect]

    rows = []
    with open(a.csv, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        missing = [c for c in NEED if c not in (rd.fieldnames or [])]
        if missing:
            raise SystemExit("Missing columns in %s: %s (check 2024 vs 2026 feed schema)"
                             % (a.csv, ",".join(missing)))
        rows = list(rd)
    print("Rows: %d  loco=%s  failure=%s  suspect=%s" % (len(rows), a.loco, a.failure, a.suspect))

    recs = []
    for r in rows:
        t = parse(r.get("devicetime"))
        v, ip, lte = f(r.get("xspeedloco")), f(r.get("xiprim_1")), f(r.get("ltedemand"))
        if t is None or v is None or ip is None or lte is None:
            continue
        ts = f(r.get(a.suspect))
        om = [f(r.get(c)) for c in others]
        om = [x for x in om if x is not None and x < a.clip]
        recs.append([t, v, ip, lte, ts, sum(om) / len(om) if om else None])
    recs.sort(key=lambda x: x[0])
    if not recs:
        raise SystemExit("No usable rows (need devicetime/xspeedloco/xiprim_1/ltedemand).")
    for i in range(1, len(recs)):
        dt = (recs[i][0] - recs[i - 1][0]).total_seconds()
        recs[i - 1].append((recs[i][1] - recs[i - 1][1]) * 1000.0 / 3600.0 / dt
                           if 0 < dt <= 5 else None)
    recs[-1].append(None)

    def bin_of(v, av):
        vb = next((b for b in V_BINS if b[0] <= v < b[1]), None)
        ab = next((b for b in A_BINS if b[0] <= av < b[1]), None) if av is not None else None
        return vb, ab

    base = {}
    for t, v, ip, lte, _ts, _om, av in recs:
        if lte != 1 or av is None or not (b0 <= t <= b1):
            continue
        vb, ab = bin_of(v, av)
        if vb and ab:
            base.setdefault((vb, ab), []).append(ip)
    model = {k: med(v) for k, v in base.items() if v}
    print("Baseline bins covered: %d/30" % len(model))

    per = {}
    for nm, p0, p1, hrs in periods:
        rs, ds = [], []
        for t, v, ip, lte, ts, om, av in recs:
            if lte != 1 or av is None or not (p0 <= t <= p1):
                continue
            if hrs is not None and not (hrs[0] <= t.hour <= hrs[1]):
                continue
            vb, ab = bin_of(v, av)
            m = model.get((vb, ab)) if vb and ab else None
            if m is None:
                continue
            rs.append(ip - m)
            if ts is not None and om is not None:
                ds.append(ts - om)
        per[nm] = (rs, ds)
    pbase = per[periods[0][0]][0]

    print("RESIDUAL r_t = I_obs - Ihat(v,a), traction-active only (BASELINE row in-sample ref)")
    print("%-24s %6s %8s %8s %8s %8s %8s %8s %9s" %
          ("period", "n", "med", "p10", "p25", "p75", "p90", "IQR", "P(|r|>30)"))
    for nm, _p0, _p1, _h in periods:
        rs, _d = per[nm]
        if not rs:
            print("%-24s %6d  (no matched rows)" % (nm, 0))
            continue
        tail = sum(1 for x in rs if abs(x) > 30.0) / len(rs)
        print("%-24s %6d %+8.1f %+8.1f %+8.1f %+8.1f %+8.1f %8.1f %9.3f%s" %
              (nm, len(rs), med(rs), pct(rs, 0.10), pct(rs, 0.25), pct(rs, 0.75),
               pct(rs, 0.90), pct(rs, 0.75) - pct(rs, 0.25), tail,
               "  <-- n<30" if len(rs) < 30 else ""))
    print("KS-D vs pooled BASELINE (no p-value):")
    for nm, _p0, _p1, _h in periods[1:]:
        rs, _d = per[nm]
        print("  %-24s n=%-5d D=%5.3f%s" % (nm, len(rs), ks_2sample(pbase, rs),
              "  <-- n<30, directional only" if len(rs) < 30 else ""))
    print("dT = suspect - other5 mean (deg C):")
    for nm, _p0, _p1, _h in periods:
        _rs, ds = per[nm]
        if ds:
            print("  %-24s n=%-5d dT med=%+6.1f IQR=%5.1f" %
                  (nm, len(ds), med(ds), pct(ds, 0.75) - pct(ds, 0.25)))

    if a.roll_start and a.roll_end:
        r0 = datetime.strptime(a.roll_start, "%Y-%m-%d %H:%M:%S")
        r1 = datetime.strptime(a.roll_end, "%Y-%m-%d %H:%M:%S")
        print("Rolling hourly residual med/IQR:")
        days = sorted({(t.month, t.day, t.hour) for t, _v, _i, _l, _s, _o, _x in recs
                       if r0 <= t <= r1})
        for m, _d, h in days:
            rs = []
            for t, v, ip, lte, _ts, _om, av in recs:
                if not (t.month == m and t.day == _d and t.hour == h and r0 <= t <= r1):
                    continue
                if lte != 1 or av is None:
                    continue
                vb, ab = bin_of(v, av)
                mv = model.get((vb, ab)) if vb and ab else None
                if mv is not None:
                    rs.append(ip - mv)
            if len(rs) >= 10:
                print("  %02d/%02d %02d:00 n=%-5d med=%+7.1f IQR=%6.1f" %
                      (_d, m, h, len(rs), med(rs), pct(rs, 0.75) - pct(rs, 0.25)))


if __name__ == "__main__":
    main()
