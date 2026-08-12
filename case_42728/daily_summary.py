import csv
from datetime import datetime
from collections import defaultdict

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

print("=== DAILY SUMMARY ===")
print(f"{'day':<12}{'rows':>8}{'motion_min':>11}{'max_speed':>11}{'spd>100':>9}{'sentinel':>9}{'Tmax':>7}{'T>60':>7}{'BURoff':>8}")
byday = defaultdict(list)
for r in rows:
    t = parse(r["devicetime"])
    byday[t.date()].append(r)

for d in sorted(byday):
    grp = byday[d]
    spds = [f(r["xspeedloco"]) for r in grp]
    spds = [v for v in spds if v is not None]
    motion = sum(1 for v in spds if v > 5)
    hi = sum(1 for v in spds if v > 100)
    sent = sum(1 for r in grp if any((f(r[c]) is not None and f(r[c]) >= 6550) for c in
            ["xvist_a1_1","xvist_a2_1","xvist_a3_1","xvist_a1_2","xvist_a2_2","xvist_a3_2"]))
    temps = [f(r[c]) for r in grp for c in ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1",
            "xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]]
    temps = [v for v in temps if v is not None and v < 300]
    hot = sum(1 for v in temps if v > 60)
    bur = sum(1 for r in grp if r["bbur3_off"] not in (None,"","0"))
    print(f"{str(d):<12}{len(grp):>8}{motion:>11}{max(spds) if spds else 0:>11.1f}{hi:>9}{sent:>9}"
          f"{max(temps) if temps else 0:>7.1f}{hot:>7}{bur:>8}")

print("\n=== GPS summary: distinct lat/lon groups per day (rounded) ===")
seen = defaultdict(set)
for r in rows:
    t = parse(r["devicetime"])
    la = f(r["latitude"]); lo = f(r["longitude"])
    if la is not None and lo is not None and abs(la) > 1:
        seen[t.date()].add((round(la,3), round(lo,3)))
for d in sorted(seen):
    pts = sorted(seen[d])
    print(f"  {d}: {len(pts)} distinct points; first={pts[0]} last={pts[-1]}")

print("\n=== Sample GPS points on 14/10 ===")
prev = None
for r in rows:
    t = parse(r["devicetime"])
    if t.date().day == 14:
        la = f(r["latitude"]); lo = f(r["longitude"])
        if la is not None and lo is not None and abs(la) > 1 and (la, lo) != prev:
            print(f"  {t}  lat={la:.4f} lon={lo:.4f} spd={f(r['xspeedloco'])}")
            prev = (la, lo)
