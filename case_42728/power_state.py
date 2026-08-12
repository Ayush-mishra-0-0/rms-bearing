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

# 1. xspeedloco vs gpsspeed on the running days (17-18) to characterise the 151.9
print("=== xspeedloco vs gpsspeed: is 151.9 real or sentinel? ===")
import math
n_real = 0
for r in rows:
    ls = f(r["xspeedloco"]); gs = f(r["gpsspeed"])
    if ls is not None and ls > 100:
        print(f"  {r['devicetime']}  locospeed={ls:.1f}  gpsspeed={gs}")
        n_real += 1
        if n_real > 25:
            break

print("\n=== xspeedloco distribution (value: count) top 20 ===")
from collections import Counter
c = Counter()
for r in rows:
    ls = f(r["xspeedloco"])
    if ls is not None:
        c[round(ls, 1)] += 1
for v, n in c.most_common(20):
    print(f"  {v}: {n}")

# 2. Power-state timeline 14/10: mvcb_on, panto, battery, BUR, lte demand
print("\n=== 14/10 power state detail (transitions) ===")
prev = None
for r in rows:
    t = parse(r["devicetime"])
    if t.day != 14:
        continue
    key = (r["mvcb_on"], r["mprswpan1"], r["mprswpan2"], r["bbur1_off"], r["bbur2_off"], r["bbur3_off"])
    if key != prev:
        bat = f(r["xu_battery"])
        print(f"  {t}  VCB={key[0]} PAN1={key[1]} PAN2={key[2]} BUR_off=({key[3]},{key[4]},{key[5]}) bat={bat if bat is None else round(bat,1)}")
        prev = key
