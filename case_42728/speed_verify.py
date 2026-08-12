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

# 1. On running days 17/18 Oct: compare locospeed vs gpsspeed to see if 151 is real
print("=== 17-18/10: samples where locospeed>20 (is it real?) ===")
n = 0
for r in rows:
    t = parse(r["devicetime"])
    if t.day not in (17, 18):
        continue
    ls = f(r["xspeedloco"]); gs = f(r["gpsspeed"])
    if ls is not None and ls > 20:
        print(f"  {r['devicetime']}  locospeed={ls:.1f}  gpsspeed={gs:.1f}  lat={r['latitude'][:7]} lon={r['longitude'][:7]}")
        n += 1
        if n > 30:
            break

# 2. Max genuine speed: highest gpsspeed
print("\n=== Highest gpsspeed values ===")
g = sorted((f(r["gpsspeed"]), r["devicetime"]) for r in rows if f(r["gpsspeed"]) is not None)
for v, t in g[-15:]:
    print(f"  {t}  gpsspeed={v:.1f}")

# 3. Traction current signals (xvist are speeds; currents are xa1 etc). Check available signals.
print("\n=== Sample of current/voltage signals on 14/10 12:47-12:49 (the spike) ===")
for r in rows:
    t = parse(r["devicetime"])
    if t.day == 14 and t.hour == 12 and 47 <= t.minute <= 49:
        rec = {k: r[k] for k in ["xspeedloco","gpsspeed","xte_be_loco","xu_battery","mvcb_on",
                                 "ltedemand","xvist_a1_1","xvist_a2_1","xvist_a3_1",
                                 "xvist_a1_2","xvist_a2_2","xvist_a3_2"]}
        print(f"  {t}  {rec}")
        if t.minute == 49 and t.second > 5:
            break
