import csv
from datetime import datetime
from collections import Counter, defaultdict

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
speed_mot = ["xvist_a1_1", "xvist_a2_1", "xvist_a3_1",
             "xvist_a1_2", "xvist_a2_2", "xvist_a3_2"]

# Classification of each row: which motors are clipped (>74) or elevated (>45)
print("=== Per-row clip/elevation pattern counts ===")
pat = Counter()
hot_pattern = defaultdict(int)
for r in rows:
    t = parse(r["devicetime"])
    clipped = tuple(c for c in temp_cols if f(r[c]) is not None and f(r[c]) > 74)
    pat[clipped] += 1
for k, v in pat.most_common(12):
    print(f"  clipped={k} count={v}")

# Time series of clip state over time (coarse)
print("\n=== Hourly: number of rows where any motor clipped, and which motor ===")
hourly = defaultdict(lambda: {"n": 0, "clip": Counter()})
for r in rows:
    t = parse(r["devicetime"])
    key = t.replace(minute=0, second=0, microsecond=0)
    hourly[key]["n"] += 1
    for c in temp_cols:
        if f(r[c]) is not None and f(r[c]) > 74:
            hourly[key]["clip"][c] += 1

prev = None
for key in sorted(hourly):
    d = hourly[key]
    if d["clip"] or prev != (bool(d["clip"])):
        clip_str = ",".join(f"{c}({n})" for c, n in sorted(d["clip"].items())) if d["clip"] else "-"
        print(f"  {key}  rows={d['n']:>5}  clipped: {clip_str}")
    prev = bool(d["clip"])
