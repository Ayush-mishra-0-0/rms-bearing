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

tcols = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]
# motor 1_2 = TM1 bogie2 = axle 04

# 07/08 10:00-10:40: compare all motor temps at the overheated window
print("=== 07/08 10:05-10:40 all-motor temps (axle04 = TM1_2) ===")
d7 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 7]
seen = set()
for r in d7:
    t = parse(r["devicetime"])
    if not t or not (10, 5) <= (t.hour, t.minute) <= (10, 40):
        continue
    key = t.strftime("%H:%M")
    if key in seen:
        continue
    seen.add(key)
    vals = [f(r[c]) for c in tcols]
    gps = f(r["gpsspeed"])
    lted = r["ltedemand"]
    print(f"  {key} gps={gps:5.1f} lted={lted} temps={[f'{v:5.1f}' if v else '---' for v in vals]}")

# 07/08: was TM1_2 the max of all six during that window?
print("\n=== 07/08: TM1_2 minus (mean of other 5, excl stuck 76s) at overheating ===")
for r in d7:
    t = parse(r["devicetime"])
    if not t or not (10, 10) <= (t.hour, t.minute) <= (10, 35):
        continue
    v = [f(r[c]) for c in tcols]
    t12 = v[3]
    others = [x for x in v[:3] + v[4:] if x is not None]
    omean = sum(others) / len(others)
    print(f"  {t.strftime('%H:%M:%S')} TM1_2={t12:.1f} other_mean={omean:.1f} delta={t12-omean:+.1f}")

# 08/08: TM1_2 cold while others hot -> delta large negative
print("\n=== 08/08: TM1_2 vs other-5 mean (motion rows) ===")
d8 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 8 and (f(r["gpsspeed"]) or 0) > 5]
deltas = []
for r in d8:
    v = [f(r[c]) for c in tcols]
    t12 = v[3]
    others = [x for x in v[:3] + v[4:] if x is not None]
    omean = sum(others) / len(others)
    deltas.append((t12 - omean, t12, omean, parse(r["devicetime"]).time()))
deltas.sort()
print("  min delta (coldest TM1_2 vs others):", [(str(t), f"{d:+.1f}", f"{t12:.1f}", f"{om:.1f}") for d, t12, om, t in deltas[:3]])
print("  max delta:", [(str(t), f"{d:+.1f}", f"{t12:.1f}", f"{om:.1f}") for d, t12, om, t in deltas[-3:]])
print("  median delta:", f"{deltas[len(deltas)//2][0]:+.1f}")

# normal baseline: 07/08 motion rows (before failure) delta TM1_2 vs others
print("\n=== 07/08: TM1_2 vs other-5 mean (motion rows, normal) ===")
d7m = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 7 and (f(r["gpsspeed"]) or 0) > 5 and parse(r["devicetime"]).hour >= 12]
deltas7 = []
for r in d7m:
    v = [f(r[c]) for c in tcols]
    t12 = v[3]
    others = [x for x in v[:3] + v[4:] if x is not None]
    omean = sum(others) / len(others)
    deltas7.append((t12 - omean, t12, omean))
if deltas7:
    deltas7.sort()
    print("  n:", len(deltas7), "median delta:", f"{deltas7[len(deltas7)//2][0]:+.1f}")
