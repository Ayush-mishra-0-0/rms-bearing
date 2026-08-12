import csv
from datetime import datetime

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

rows = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)

# 1. faultnum distribution
from collections import Counter
fn = Counter(r["faultnum"] for r in rows)
print("faultnum distribution:", dict(fn))

# 2. per-day TM temp summary
tcols = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]
print("\n=== per-day TM temp ranges (deg C) ===")
byday = {}
for r in rows:
    t = parse(r["devicetime"])
    if t:
        byday.setdefault(t.date(), []).append(r)
for d in sorted(byday):
    rs = byday[d]
    print(f"--- {d} (n={len(rs)}) ---")
    for c in tcols:
        vals = [f(r[c]) for r in rs if f(r[c]) is not None]
        if vals:
            mx = max(vals)
            pct_clip = 100.0 * sum(1 for v in vals if v > 75.9) / len(vals)
            print(f"  {c}: min={min(vals):.1f} max={mx:.1f} mean={sum(vals)/len(vals):.1f} clip%={pct_clip:.1f}")

# 3. motion & speed context per day
print("\n=== per-day running stats ===")
for d in sorted(byday):
    rs = byday[d]
    mv = sum(1 for r in rs if (f(r["gpsspeed"]) or 0) > 2)
    mxls = max((f(r["xspeedloco"]) or 0) for r in rs)
    mxt1_2 = max((f(r["xtempmotor1_2"]) or 0) for r in rs)
    print(f"  {d}: motion_rows={mv} max_locomotive_speed={mxls:.0f} max_TM1_2={mxt1_2:.1f}")
