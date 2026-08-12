import csv
from datetime import datetime
from collections import Counter

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

print("Total rows:", len(rows))

# Focus columns
temp_cols = ["xtempmotor1_1", "xtempmotor2_1", "xtempmotor3_1",
             "xtempmotor1_2", "xtempmotor2_2", "xtempmotor3_2"]
speed_mot = ["xvist_a1_1", "xvist_a2_1", "xvist_a3_1",
             "xvist_a1_2", "xvist_a2_2", "xvist_a3_2"]
iso_cols = ["bstb1_off", "bstb2_off", "bslg1_off", "bslg2_off",
            "bflg1_off", "bflg2_off", "bbur1_off", "bbur2_off", "bbur3_off",
            "bhbb1_off", "bhbb2_off", "bbda1_off", "bbda2_off"]
flag_cols = ["mvcb_on", "mldsein_1", "mldsein_2", "ltedemand"]

# 1. faultnum values
fn = Counter(r["faultnum"] for r in rows)
print("\n=== faultnum distribution (top 15) ===")
for k, v in fn.most_common(15):
    print(f"  {k}: {v}")

# 2. Temperature range per column
print("\n=== Motor temp ranges (deg C, non-null) ===")
for c in temp_cols:
    vals = [f(r[c]) for r in rows]
    vals = [v for v in vals if v is not None]
    if vals:
        print(f"  {c:<18} n={len(vals):>6}  min={min(vals):7.1f}  max={max(vals):7.1f}  mean={sum(vals)/len(vals):7.1f}")

# 3. Motor speed ranges
print("\n=== Motor speed ranges (km/h?) ===")
for c in speed_mot:
    vals = [f(r[c]) for r in rows]
    vals = [v for v in vals if v is not None]
    if vals:
        print(f"  {c:<18} n={len(vals):>6}  min={min(vals):8.2f}  max={max(vals):8.2f}")

# 4. Loco speed
sp = [f(r["xspeedloco"]) for r in rows]
sp = [v for v in sp if v is not None]
print("\nxspeedloco max:", max(sp), " (values >0:", len([v for v in sp if v>1]), ")")

# 5. Isolation flags: count non-zero / times
print("\n=== Isolation / status flags: count of non-zero values ===")
for c in iso_cols:
    nz = sum(1 for r in rows if r[c] not in (None, "", "0"))
    if nz:
        print(f"  {c}: {nz} non-zero")

# 6. When did each flag turn on (first/last nonzero ts)?
print("\n=== First/last non-zero timestamp for isolation flags ===")
for c in iso_cols:
    nz = [(parse(r["devicetime"]), r[c]) for r in rows if r[c] not in (None, "", "0")]
    if nz:
        print(f"  {c}: first={nz[0][0]} ({nz[0][1]})  last={nz[-1][0]} ({nz[-1][1]})  count={len(nz)}")
