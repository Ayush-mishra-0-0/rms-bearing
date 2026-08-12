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
        v = float(x)
        return v
    except (TypeError, ValueError):
        return None

rows = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)
print("rows:", len(rows))

# GPS distinct locations & where loco was on 08/08
print("\n=== distinct GPS points (rounded 0.001) per day 07-10 Aug ===")
pts = {}
for r in rows:
    t = parse(r["devicetime"])
    if not t or t.month != 8:
        continue
    key = (round(f(r["latitude"] or 0) or 0, 3), round(f(r["longitude"] or 0) or 0, 3))
    pts.setdefault(t.day, set()).add(key)
for d in sorted(pts):
    print(f"  Aug {d:02d}: {len(pts[d])} distinct GPS points; sample:", list(pts[d])[:4])

# rows where loco moving (gpsspeed>2) per day
print("\n=== motion (gpsspeed>2) per day ===")
for d in (7, 8, 9, 10):
    mv = sum(1 for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == d and (f(r["gpsspeed"]) or 0) > 2)
    mx = max((f(r["gpsspeed"]) or 0) for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == d)
    print(f"  Aug {d:02d}: motion_rows={mv} max_gpsspeed={mx:.1f}")

# 08/08: hour-of-day distribution & key signals around 19:00-20:00
print("\n=== Aug 8 rows per hour ===")
from collections import Counter
hc = Counter()
for r in rows:
    t = parse(r["devicetime"])
    if t and t.day == 8:
        hc[t.hour] += 1
for h in sorted(hc):
    print(f"  {h:02d}:00  {hc[h]}")
