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

cols = ["bg1tm1_ipvoltage", "bg2tm1_ipvoltage", "bur1_opcurrent", "bur2_opcurrent", "bur3_opcurrent",
        "xiprim_1", "xuiz1_bur1", "xuiz1_bur2", "xuiz1_bur3", "xaibur", "xangtrans", "xspeedloco",
        "ltedemand", "xenergymwh_ec"]
cov = {c: {} for c in cols}  # day -> count

with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        t = parse(r["devicetime"])
        if not t:
            continue
        d = t.strftime("%m-%d")
        for c in cols:
            if f(r.get(c)) is not None:
                cov[c][d] = cov[c].get(d, 0) + 1

days = sorted(cov["xiprim_1"].keys())
print("day", " ".join(f"{c:>8}" for c in cols))
for d in days:
    print(d, " ".join(f"{cov[c].get(d,0):>8}" for c in cols))

# check xangtrans meaning: relationship to traction
print("\nxangtrans: 0-50 range typical of traction demand? min/max/mean overall")
