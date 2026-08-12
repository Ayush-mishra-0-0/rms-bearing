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

# hourly TM1_2 vs other-mean, 06-10 Aug
print("=== hourly: TM1_2 vs other5-mean (06..10 Aug) ===")
for day in (6, 7, 8, 9, 10):
    rs = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == day]
    byhour = {}
    for r in rs:
        t = parse(r["devicetime"])
        v = [f(r[c]) for c in tcols]
        if any(x is None for x in v):
            continue
        t12 = v[3]
        others = [x for x in v[:3] + v[4:] if x is not None and x < 75.99]
        if not others:
            continue
        byhour.setdefault(t.hour, []).append((t12, sum(others) / len(others)))
    for h in sorted(byhour):
        pts = byhour[h]
        t12 = sum(p[0] for p in pts) / len(pts)
        om = sum(p[1] for p in pts) / len(pts)
        n = len(pts)
        print(f"  {day:02d}/{h:02d}:00 n={n} TM1_2={t12:.1f} other={om:.1f} delta={t12-om:+.1f}")

# GPS: where was the loco on 08/08 and 09/08 (confirm NKE-CPJ / BSB region)
print("\n=== GPS path 08/08 (minutes) ===")
d8 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 8 and (f(r["gpsspeed"]) or 0) > 5]
seen = set()
for r in d8:
    t = parse(r["devicetime"])
    key = t.strftime("%H:%M")
    if key in seen:
        continue
    seen.add(key)
    print(f"  {key} lat={f(r['latitude']):.4f} lon={f(r['longitude']):.4f} gps={f(r['gpsspeed']):.1f}")

print("\n=== GPS 09/08 (minutes) ===")
d9 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 9]
seen = set()
for r in d9:
    t = parse(r["devicetime"])
    key = t.strftime("%H:%M")
    if key in seen:
        continue
    seen.add(key)
    print(f"  {key} lat={f(r['latitude']):.4f} lon={f(r['longitude']):.4f} gps={f(r['gpsspeed']):.1f}")
