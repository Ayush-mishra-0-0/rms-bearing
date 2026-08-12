import csv
from datetime import datetime

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

temps = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]

# For 17 & 18 Oct: distribution of the temp>60 values (are they ALL at 75.995 clip? or gradual real?)
for day in (17, 18):
    vals_hi = []
    vals_all = []
    samples = 0
    for r in rows:
        t = parse(r["devicetime"])
        if t.day == day:
            for c in temps:
                v = f(r[c])
                if v is not None and v < 300:
                    vals_all.append(v)
                    if v > 60:
                        vals_hi.append(v)
                        samples += 1
    clip = sum(1 for v in vals_hi if v > 75.9)
    print(f"--- {day}/10 ---")
    print(f"  rows(w any temp>60): {samples}")
    print(f"  of those, value>75.9 (full-scale clip): {clip} ({100*clip/max(samples,1):.1f}%)")
    print(f"  min/max of >60 values: {min(vals_hi):.2f}/{max(vals_hi):.2f}")
    print(f"  distribution: clip(76)={sum(1 for v in vals_hi if v>75.9)}, 60-70={sum(1 for v in vals_hi if 60<v<=70)}, 70-76={sum(1 for v in vals_hi if 70<v<=75.9)}")

# Are the 17/10 high temps coincident with stationary (speed 0) moments?
print("\n=== 17/10 temp>60 rows: speed & gps context ===")
stat = run = 0
for r in rows:
    t = parse(r["devicetime"])
    if t.day == 17:
        hi = any(f(r[c]) is not None and f(r[c]) > 60 for c in temps)
        if hi:
            if f(r["xspeedloco"]) in (0.0, None):
                stat += 1
            else:
                run += 1
print(f"  temp>60 while locospeed==0: {stat}, while locospeed>0: {run}")
