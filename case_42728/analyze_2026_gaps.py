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

# exact time range per day
print("=== exact time range per day ===")
byday = {}
for r in rows:
    t = parse(r["devicetime"])
    if t:
        byday.setdefault(t.date(), []).append(t)
for d in sorted(byday):
    ts = byday[d]
    print(f"  {d}: first={min(ts).time()} last={max(ts).time()} n={len(ts)}")

# identify gaps > 5 min in the full stream
print("\n=== gaps > 5 min ===")
last = None
for r in rows:
    t = parse(r["devicetime"])
    if not t:
        continue
    if last and (t - last).total_seconds() > 300:
        print(f"  {last} -> {t}  (gap {int((t-last).total_seconds()//60)} min)")
    last = t

# rows in the critical window 08/08 14:00 - 09/08 12:00 with key columns
print("\n=== last 40 rows on Aug 8 (order by time) ===")
d8 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 8]
d8.sort(key=lambda r: parse(r["devicetime"]))
for r in d8[-40:]:
    t = parse(r["devicetime"]).time()
    print(f"  {t} gps={f(r['gpsspeed'])} ls={f(r['xspeedloco'])} vcb={r['mvcb_on']} b1={r['bbur1_off']} b2={r['bbur2_off']} b3={r['bbur3_off']} t1={f(r['xtempmotor1_1']):.0f} t6={f(r['xtempmotor3_2']):.0f} lat={f(r['latitude']):.3f} lon={f(r['longitude']):.3f}")
