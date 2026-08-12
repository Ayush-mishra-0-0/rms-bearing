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

tcols = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]

def other5_mean(r):
    vals = [f(r[c]) for c in tcols]
    ok = [v for v in (vals[:3] + vals[4:]) if v is not None and v < 75.99]
    return sum(ok) / len(ok) if ok else None

def med(vals):
    vals = sorted(vals)
    if not vals:
        return float("nan")
    return vals[len(vals)//2] if len(vals) % 2 else (vals[len(vals)//2-1]+vals[len(vals)//2])/2

rows = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)

# ---------------- TEST F: fine-grained TM1_2 vs other5 across 05..09 Aug
print("=" * 70)
print("TEST F: TM1_2 vs other-5 (15-min medians), 05..09 Aug")
print("=" * 70)
buckets = defaultdict(lambda: defaultdict(list))
for r in rows:
    t = parse(r["devicetime"])
    if not t or t.month != 8 or t.day < 5:
        continue
    t12 = f(r["xtempmotor1_2"])
    om = other5_mean(r)
    if t12 is None or om is None:
        continue
    k = t.day * 1000 + (t.hour * 4 + t.minute // 15)
    buckets[k]["t12"].append(t12)
    buckets[k]["om"].append(om)

prev_key = None
for k in sorted(buckets):
    day = k // 1000
    q = k % 1000
    hh = q // 4
    mm = (q % 4) * 15
    t12 = med(buckets[k]["t12"])
    om = med(buckets[k]["om"])
    d = t12 - om
    # mark transition: d drops below -10
    flag = ""
    if d < -10:
        flag = "  <<< COLD STATE"
    if d > +5:
        flag = "  <<< HOT STATE"
    print(f"  08-{day:02d} {hh:02d}:{mm:02d}  TM1_2={t12:6.1f}  other5={om:6.1f}  dT={d:+7.1f}{flag}")

# ---------------- exact first-cold timestamp on each day
print("\n" + "=" * 70)
print("TEST F: first/continuous TM1_2 cold (dT < -10) per day")
print("=" * 70)
for day in (5, 6, 7, 8, 9):
    sel = []
    for r in rows:
        t = parse(r["devicetime"])
        if not t or t.month != 8 or t.day != day:
            continue
        t12 = f(r["xtempmotor1_2"])
        om = other5_mean(r)
        if t12 is None or om is None:
            continue
        sel.append((t, t12, om, t12 - om))
    if not sel:
        print(f"  08-{day:02d}: no data")
        continue
    # find earliest sustained cold run (>= 10 consecutive rows dT<-10)
    streak = 0
    first = None
    for t, t12, om, d in sel:
        if d < -10:
            if streak == 0:
                first = t
            streak += 1
            if streak >= 30:
                print(f"  08-{day:02d}: cold-state (dT<-10) sustained from {first.strftime('%H:%M:%S')} (n_cold={streak})")
                break
        else:
            streak = 0
            first = None
    else:
        # print max dT row summary
        mx = max(sel, key=lambda x: x[3])
        mn = min(sel, key=lambda x: x[3])
        print(f"  08-{day:02d}: no sustained cold run. max dT={mx[3]:+.1f} ({mx[0].strftime('%H:%M')}) min dT={mn[3]:+.1f} ({mn[0].strftime('%H:%M')})")
