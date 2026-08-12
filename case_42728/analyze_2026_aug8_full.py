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

# Full Aug 8 timeline with key signals (bogie voltages + temps)
print("=== Aug 8 full day, minute-level (every row, key cols) ===")
d8 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 8]
d8.sort(key=lambda r: parse(r["devicetime"]))
hdr = ["time","gps","ls","vcb","b1","b2","b3","lted","sr1","sr2","bg1t1","bg1t2","bg1t3","bg2t1","bg2t2","bg2t3",
       "TM1_1","TM2_1","TM3_1","TM1_2","TM2_2","TM3_2","fault","lat","lon"]
print("  ".join(hdr))
for r in d8:
    t = parse(r["devicetime"]).time()
    vals = [f(r["gpsspeed"]), f(r["xspeedloco"]), r["mvcb_on"], r["bbur1_off"], r["bbur2_off"], r["bbur3_off"],
            r["ltedemand"], f(r["sr1_ipvoltage"]), f(r["sr2_ipvoltage"]),
            f(r["bg1tm1_ipvoltage"]), f(r["bg1tm2_ipvoltage"]), f(r["bg1tm3_ipvoltage"]),
            f(r["bg2tm1_ipvoltage"]), f(r["bg2tm2_ipvoltage"]), f(r["bg2tm3_ipvoltage"]),
            f(r["xtempmotor1_1"]), f(r["xtempmotor2_1"]), f(r["xtempmotor3_1"]),
            f(r["xtempmotor1_2"]), f(r["xtempmotor2_2"]), f(r["xtempmotor3_2"]),
            r["faultnum"], f(r["latitude"]), f(r["longitude"])]
    line = [str(t)] + ["" if v is None else f"{v:.1f}" if isinstance(v, float) else str(v) for v in vals]
    print("  ".join(line))
