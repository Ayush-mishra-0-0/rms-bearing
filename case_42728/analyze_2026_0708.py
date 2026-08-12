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

# Verify a3_2 sentinel (3276) across all days
vist3_2 = {}
for r in rows:
    t = parse(r["devicetime"])
    if not t:
        continue
    v = f(r["xvist_a3_2"])
    if v == 3276:
        vist3_2.setdefault(t.date(), 0)
        vist3_2[t.date()] += 1
print("days with xvist_a3_2=3276 (count):", dict(sorted(vist3_2.items())))

# 07/08 TM1_2 overheating episodes - summarize by time window
print("\n=== 07/08 TM1_2 > 75 episodes (windows) ===")
d7 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 7]
ep = []
cur = None
for r in d7:
    t = parse(r["devicetime"])
    v = f(r["xtempmotor1_2"])
    if v and v > 75:
        if cur is None:
            cur = [t, t, v, v]
        else:
            cur[1] = t
            cur[2] = min(cur[2], v)
            cur[3] = max(cur[3], v)
    else:
        if cur:
            ep.append(cur)
            cur = None
if cur:
    ep.append(cur)
for e in ep:
    print(f"  {e[0].time()} -> {e[1].time()}  min={e[2]:.1f} max={e[3]:.1f}")

# 07/08 full-day TM1_2 timeline (minute samples)
print("\n=== 07/08 TM1_2 minute timeline ===")
last_min = None
for r in d7:
    t = parse(r["devicetime"])
    v = f(r["xtempmotor1_2"])
    if not v:
        continue
    if last_min == t.strftime("%H:%M"):
        continue
    last_min = t.strftime("%H:%M")
    print(f"  {last_min} TM1_2={v:6.1f} gps={f(r['gpsspeed']):6.1f} ls={f(r['xspeedloco']):6.1f} vcb={r['mvcb_on']} lted={r['ltedemand']} mtrcct1={r['mtrcctract1']}")
