import csv
from datetime import datetime
from collections import Counter

path = "telemetry_42728_raw.csv"

def parse(s):
    return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")

def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

rows = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)

temp_cols = ["xtempmotor1_1", "xtempmotor2_1", "xtempmotor3_1",
             "xtempmotor1_2", "xtempmotor2_2", "xtempmotor3_2"]

# Temperature 76.0 clip: distribution by motor and by time
print("=== Temp == 76.0 (sensor clip): per motor, count + time bands ===")
clip = {c: [] for c in temp_cols}
for r in rows:
    t = parse(r["devicetime"])
    for c in temp_cols:
        if f(r[c]) == 76.0:
            clip[c].append(t)
for c in temp_cols:
    if clip[c]:
        print(f"  {c}: n={len(clip[c])} first={min(clip[c])} last={max(clip[c])}")

print("\n=== 15-min buckets on 11/10 (first day w/ spikes) and 14/10: max temp ===")
for day, lo, hi in ((11, "10:00", "13:00"), (14, "10:00", "16:30")):
    print(f"  -- 14-10-{day} {lo}-{hi} --")
    bands = {}
    for r in rows:
        t = parse(r["devicetime"])
        if t.day != day:
            continue
        hhmm = f"{t.hour:02d}:{t.minute//15*15:02d}"
        band = f"{t.hour:02d}:{t.minute//15*15:02d}"
        if not (lo <= band[:2] + ":" + band[3:] <= hi):
            continue
        key = (t.hour, t.minute // 15)
        v = [f(r[c]) for c in temp_cols]
        v = [x for x in v if x is not None]
        m = max(v) if v else 0
        bands.setdefault(key, []).append(m)
    for key in sorted(bands):
        vals = bands[key]
        print(f"    {key[0]:02d}:{key[1]*15:02d}  maxT={max(vals):.1f}  n={len(vals)}")
