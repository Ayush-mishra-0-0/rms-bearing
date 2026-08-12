import csv
from datetime import datetime
from collections import defaultdict

path = "telemetry_42728_2026_rds.json.csv"

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
    return vals[len(vals)//2] if len(vals) % 2 else (vals[len(vals)//2-1]+vals[len(vals)//2])/2

tcols = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]
def other5_mean(r):
    vals = [f(r[c]) for c in tcols]
    ok = [v for v in (vals[:3] + vals[4:]) if v is not None and v < 75.99]
    return sum(ok)/len(ok) if ok else None

rows = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)

def in_period(t, p):
    (d1, m1), (d2, m2) = p
    return datetime(2026, m1, d1) <= t <= datetime(2026, m2, d2, 23, 59, 59)

# TEST E: how does TM1_2 and other5 respond as primary current rises?
# Bucket Ip into ranges; require speed > 20 km/h (loaded running) + lte=1.
print("=" * 74)
print("TEST E: temp response vs primary current (speed>20, traction active)")
print("       med TM1_2 | med other5 | n, per period & Ip bucket")
print("=" * 74)
Ip_bins = [(0,20),(20,40),(40,60),(60,80),(80,120),(120,1e9)]
periods = [("BASELINE 27Jul-3Aug", ((27,7),(3,8))), ("06-Aug", ((6,8),(6,8))),
           ("07-Aug", ((7,8),(7,8))), ("08-Aug", ((8,8),(8,8)))]
acc = defaultdict(lambda: defaultdict(list))
for r in rows:
    t = parse(r["devicetime"])
    if not t:
        continue
    v = f(r["xspeedloco"]); ip = f(r["xiprim_1"]); lte = f(r["ltedemand"])
    if v is None or ip is None or lte != 1 or v <= 20:
        continue
    t12 = f(r["xtempmotor1_2"]); om = other5_mean(r)
    if t12 is None or om is None:
        continue
    for nm, p in periods:
        if in_period(t, p):
            ib = None
            for lo, hi in Ip_bins:
                if lo <= ip < hi:
                    ib = (lo, hi); break
            if ib is not None:
                acc[(nm, ib)]["t12"].append(t12)
                acc[(nm, ib)]["om"].append(om)
            break

hdr = f"{'period':<22}{'Ip':>12}{'n':>7}{'TM1_2':>8}{'other5':>8}{'dT':>7}"
print(hdr)
print("-" * len(hdr))
for (nm, ib), d in sorted(acc.items(), key=lambda kv: (kv[0][1][0], kv[0][0])):
    lo, hi = ib
    lbl = f"{lo}-{hi}" if hi < 1e9 else f"{lo}+"
    t12 = med(d["t12"]); om = med(d["om"])
    print(f"{nm:<22}{lbl:>12}{len(d['t12']):>7}{t12:>8.1f}{om:>8.1f}{t12-om:>+7.1f}")

# Focused: 07-Aug morning (hot stage) vs 08-Aug (cold stage) - the response slope
print()
print("=" * 74)
print("TEST E focus: regression-style view of TM1_2 vs Ip, 07/08 hot run and 08/08")
print("   (mean TM1_2 and other5 in Ip bands, speed>20)")
print("=" * 74)
for nm, p, label in [("07-Aug", ((7,8),(7,8)), "07/08 (overheat stage)"),
                     ("08-Aug", ((8,8),(8,8)), "08/08 (cold-axle stage)")]:
    print(f"\n  {label}:")
    for lo, hi in Ip_bins:
        sel = []
        for r in rows:
            t = parse(r["devicetime"])
            if not t or not in_period(t, p):
                continue
            v = f(r["xspeedloco"]); ip = f(r["xiprim_1"]); lte = f(r["ltedemand"])
            if v is None or ip is None or lte != 1 or v <= 20:
                continue
            t12 = f(r["xtempmotor1_2"]); om = other5_mean(r)
            if t12 is None or om is None:
                continue
            if lo <= ip < hi:
                sel.append((t12, om))
        if not sel:
            continue
        t12 = med([s[0] for s in sel]); om = med([s[1] for s in sel])
        print(f"    Ip {lo:>4}-{hi:>4}: n={len(sel):<5} TM1_2={t12:6.1f} other5={om:6.1f} dT={t12-om:+7.1f}")
