import csv
from datetime import datetime

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

# Correlate: does the 151.9 speed / 6552 sentinel appear with VCB ON but stationary?
# i.e. artifact appears at power-on while not running
print("=== For each 151.9-spike minute: state (VCB, spd, gps, sentinel) ===")
n = 0
for r in rows:
    ls = f(r["xspeedloco"])
    if ls is not None and ls > 100:
        sent = any((f(r[c]) is not None and f(r[c]) >= 6550) for c in
                   ["xvist_a1_1","xvist_a2_1","xvist_a3_1","xvist_a1_2","xvist_a2_2","xvist_a3_2"])
        print(f"  {r['devicetime']} VCB={r['mvcb_on']} locospeed={ls:.1f} gpsspeed={f(r['gpsspeed']):.1f} sentinel={sent}")
        n += 1
        if n > 20:
            break

print(f"\nTotal rows with locospeed>100: ", sum(1 for r in rows if f(r['xspeedloco']) is not None and f(r['xspeedloco'])>100))
print("Total rows with VCB=1:", sum(1 for r in rows if r['mvcb_on']=='1'))
print("VCB=1 AND locospeed>100:", sum(1 for r in rows if r['mvcb_on']=='1' and f(r['xspeedloco']) is not None and f(r['xspeedloco'])>100))
print("VCB=1 AND locospeed=0:", sum(1 for r in rows if r['mvcb_on']=='1' and f(r['xspeedloco'])==0.0))

# Temp during actual running (17-18 Oct) - do temps rise normally?
print("\n=== TM temps during real running on 17/10 06:00-08:00 (should be real) ===")
vals = []
for r in rows:
    t = parse(r["devicetime"])
    if t.day == 17 and 6 <= t.hour <= 8:
        for c in ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]:
            v = f(r[c])
            if v is not None and v < 300:
                vals.append(v)
print(f"  n={len(vals)} min={min(vals):.1f} max={max(vals):.1f} mean={sum(vals)/len(vals):.1f}")
print("  rows with any temp>60:", sum(1 for r in rows if parse(r['devicetime']).day==17 and any(f(r[c]) is not None and f(r[c])>60 for c in ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"])))
