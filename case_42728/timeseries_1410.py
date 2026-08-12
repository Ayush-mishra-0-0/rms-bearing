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

# Minute-bucket aggregation for the whole window
from collections import defaultdict

temp_cols = ["xtempmotor1_1", "xtempmotor2_1", "xtempmotor3_1",
             "xtempmotor1_2", "xtempmotor2_2", "xtempmotor3_2"]
speed_mot = ["xvist_a1_1", "xvist_a2_1", "xvist_a3_1",
             "xvist_a1_2", "xvist_a2_2", "xvist_a3_2"]

buckets = defaultdict(list)
for r in rows:
    t = parse(r["devicetime"])
    key = t.replace(second=0, microsecond=0)
    buckets[key].append(r)

keys = sorted(buckets)
print("Minute-buckets:", len(keys))

# For each minute: max motor temp, loco speed, motor speeds, flags
def get(r, c):
    return f(r[c])

print("\n=== Every minute 14/10 08:00 -> 18:00: max temp, speeds, flags ===")
for key in keys:
    if not (key.month == 10 and key.day == 14 and 8 <= key.hour <= 18):
        continue
    grp = buckets[key]
    mt = [get(r, c) for r in grp for c in temp_cols]
    mt = [v for v in mt if v is not None]
    sp = [get(r, "xspeedloco") for r in grp]
    sp = [v for v in sp if v is not None]
    ms = {}
    for c in speed_mot:
        vals = [get(r, c) for r in grp]
        vals = [v for v in vals if v is not None]
        ms[c] = max(vals) if vals else None
    bur1 = any(r["bbur1_off"] not in (None, "", "0") for r in grp)
    bur2 = any(r["bbur2_off"] not in (None, "", "0") for r in grp)
    bur3 = any(r["bbur3_off"] not in (None, "", "0") for r in grp)
    lted = max([get(r, "ltedemand") for r in grp] or [0])
    tmax = max(mt) if mt else None
    # mark if any motor speed is the 6553 sentinel
    sent = any(v is not None and v >= 6550 for v in ms.values())
    print(f"{key}  Tmax={tmax if tmax is None else round(tmax,1)}  spd={round(max(sp),1) if sp else None}"
          f"  sentinel_speed={sent}  BUR_off={int(bur1)+int(bur2)+int(bur3)}  TE={lted}")
