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

cols = [
    "xiprim_1", "xuprim_1", "xenergymwh_ec", "xenergymwh_er",
    "bg1tm1_ipvoltage", "bg1tm2_ipvoltage", "bg1tm3_ipvoltage",
    "bg2tm1_ipvoltage", "bg2tm2_ipvoltage", "bg2tm3_ipvoltage",
    "sr1_ipvoltage", "sr2_ipvoltage",
    "bur_ipvoltage", "bur_ipcurrent",
    "bur1_opcurrent", "bur2_opcurrent", "bur3_opcurrent",
    "xuiz1_bur1", "xuiz1_bur2", "xuiz1_bur3",
    "xuuz1_bur1", "xuuz1_bur2", "xuuz1_bur3",
    "bur_1_xufwr", "bur_2_xufwr", "bur_3_xufwr",
    "xaibur", "xspeedloco", "xangtrans",
    "ltedemand", "lbedemand", "mvcb_on",
    "xadrucktr_1", "xadrucktr_2",
]
stats = {c: [0, None, None] for c in cols}  # count, min, max
sums = {c: 0.0 for c in cols}
examples = {c: [] for c in cols}

rows_seen = 0
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rows_seen += 1
        t = parse(r["devicetime"])
        day = t.day if t else None
        for c in cols:
            v = f(r.get(c))
            if v is None:
                continue
            stats[c][0] += 1
            sums[c] += v
            if stats[c][1] is None or v < stats[c][1]:
                stats[c][1] = v
            if stats[c][2] is None or v > stats[c][2]:
                stats[c][2] = v
            if len(examples[c]) < 8:
                examples[c].append((str(t), v))
        if rows_seen >= 400000:
            break

print("rows scanned:", rows_seen)
print(f"{'col':<22}{'n':>8}{'min':>14}{'max':>14}{'mean':>14}")
for c in cols:
    n, mn, mx = stats[c]
    mean = sums[c] / n if n else 0.0
    print(f"{c:<22}{n:>8}{mn if mn is not None else '-':>14}{mx if mx is not None else '-':>14}{mean:>14.1f}")

print("\nexamples:")
for c in cols:
    print(f"  {c}: {examples[c][:4]}")
