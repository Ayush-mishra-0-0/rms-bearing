import csv
from datetime import datetime
from collections import defaultdict

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

vcols = ["xvist_a1_1","xvist_a2_1","xvist_a3_1","xvist_a1_2","xvist_a2_2","xvist_a3_2"]
labels = {"xvist_a1_1":"axle1","xvist_a2_1":"axle2","xvist_a3_1":"axle3","xvist_a1_2":"axle04","xvist_a2_2":"axle5","xvist_a3_2":"axle6"}

# coverage + min/max/median per channel per day
print("=== per-channel per-day: n, min, median, max, #of distinct values ===")
cov = defaultdict(lambda: defaultdict(list))
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        t = parse(r["devicetime"])
        if not t:
            continue
        day = t.strftime("%m-%d")
        for c in vcols:
            v = f(r.get(c))
            if v is not None:
                cov[day][c].append(v)

for day in sorted(cov):
    row = []
    for c in vcols:
        vals = cov[day][c]
        if not vals:
            row.append(f"{labels[c]}: -")
            continue
        sv = sorted(vals)
        n = len(vals)
        med = sv[n // 2]
        lo, hi = sv[0], sv[-1]
        uniq = len(set(round(x, 2) for x in vals))
        row.append(f"{labels[c]}: n{n} [{lo:.0f}..{hi:.0f}] md{med:.0f} u{uniq}")
    print(f"  {day}: " + " | ".join(row))

# distribution of the 08-Aug axle speeds vs loco speed
print("\n=== 08-Aug: loco speed vs each axle speed channel (rows where loco moving >5) ===")
for r in []:
    pass
cnt = 0
for r in []:
    pass

with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        t = parse(r["devicetime"])
        if not t or t.day != 8:
            continue
        ls = f(r.get("xspeedloco"))
        if ls is None or ls < 5:
            continue
        vals = {c: f(r.get(c)) for c in vcols}
        if any(v is None for v in vals.values()):
            continue
        cnt += 1
        if cnt <= 40:
            print(f"  {t.strftime('%H:%M:%S')} loco={ls:5.1f}  " +
                  "  ".join(f"{labels[c]}={vals[c]:5.0f}" for c in vcols))
print("rows shown:", cnt)
