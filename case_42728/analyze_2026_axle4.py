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

vist = ["xvist_a1_1","xvist_a2_1","xvist_a3_1","xvist_a1_2","xvist_a2_2","xvist_a3_2"]
tcols = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]

# On 08/08 during motion: per-axle motor speed & temp consistency
print("=== 08/08 during motion: per-axle speeds and TM1_2 ===")
d8 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 8 and (f(r["gpsspeed"]) or 0) > 5]
for r in d8[::50]:
    t = parse(r["devicetime"]).time()
    sp = [f(r[c]) for c in vist]
    tm = [f(r[c]) for c in tcols]
    print(f"  {t} gps={f(r['gpsspeed']):.0f} vist={'/'.join(f'{v:.0f}' if v else '-' for v in sp)} TM1_2={tm[3]:.0f} others={','.join(f'{v:.0f}' if v else '-' for v in tm[:3]+tm[4:5])}")

# 07/08: when did TM1_2 hit 91.7? context
print("\n=== 07/08 TM1_2 high (>75) rows ===")
d7 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 7]
n = 0
for r in d7:
    t = parse(r["devicetime"]).time()
    v = f(r["xtempmotor1_2"])
    if v and v > 75:
        print(f"  {t} TM1_2={v:.1f} gps={f(r['gpsspeed']):.0f} ls={f(r['xspeedloco']):.0f} vcb={r['mvcb_on']}")
        n += 1
        if n > 15:
            break
print("total >75 rows on 07/08:", sum(1 for r in d7 if f(r["xtempmotor1_2"]) and f(r["xtempmotor1_2"])>75))

# mtrcctract signals on 07/08 (traction circuit contactor)
print("\n=== 07/08 mtrcctract1/2 & xangtrans ===")
cnt = 0
for r in d7:
    t = parse(r["devicetime"]).time()
    if f(r["xtempmotor1_2"]) and f(r["xtempmotor1_2"]) > 75 and cnt < 10:
        print(f"  {t} mtrcct1={r['mtrcctract1']} mtrcct2={r['mtrcctract2']} xangtrans={f(r['xangtrans'])} ltedemand={r['ltedemand']}")
        cnt += 1
