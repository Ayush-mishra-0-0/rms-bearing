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

def med(vals):
    vals = sorted(vals)
    n = len(vals)
    if n == 0:
        return float("nan")
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2

def pct(vals, p):
    vals = sorted(vals)
    if not vals:
        return float("nan")
    k = int((len(vals) - 1) * p)
    return vals[k]

rows = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)

def get(r, c):
    return f(r.get(c))

tcols = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]

def other5_mean(r):
    vals = [get(r, c) for c in tcols]
    ok = [v for v in (vals[:3] + vals[4:]) if v is not None and v < 75.99]
    return sum(ok) / len(ok) if ok else None

# ------------------------------------------------------------------
print("=" * 78)
print("TEST 1: PRIMARY CURRENT vs SPEED BUCKET, per period")
print("Buckets: 0-10, 10-20, 20-30, 30-40, 40-50 km/h")
print("Only rows with ltedemand=1 (traction command active)")
print("=" * 78)

periods = [
    ("BASELINE 07-27..08-03", (27, 7), (3, 8)),
    ("06-Aug", (6, 8), (6, 8)),
    ("07-Aug", (7, 8), (7, 8)),
    ("08-Aug (pre-fail)", (8, 8), (8, 8)),
]

buckets = [(0,10),(10,20),(20,30),(30,40),(40,50)]

def in_period(r, period):
    t = parse(r["devicetime"])
    if not t:
        return False
    (d1, m1), (d2, m2) = period
    # period is (day, month)
    start = datetime(2026, m1, d1)
    end = datetime(2026, m2, d2, 23, 59, 59)
    return start <= t <= end

# gather per period + bucket: xiprim_1, xuiz per bur, speed, TM1_2, other mean, bg2tm1 vs others
data = {}
for r in rows:
    t = parse(r["devicetime"])
    if not t:
        continue
    sp = get(r, "xspeedloco")
    if sp is None:
        continue
    lte = get(r, "ltedemand")
    if lte != 1:
        continue
    for nm, p1, p2 in periods:
        if in_period(r, (p1, p2)):
            bucket = None
            for lo, hi in buckets:
                if lo <= sp < hi:
                    bucket = (lo, hi)
                    break
            if bucket is None:
                continue
            key = (nm, bucket)
            data.setdefault(key, []).append(r)
            break

hdr = f"{'period':<26}{'bucket':>10}{'n':>7}{'Ip_med':>9}{'Ip_p90':>9}{'xuzB1':>7}{'xuzB2':>7}{'xuzB3':>7}{'TM1_2':>8}{'oth5':>7}{'dT':>7}"
print(hdr)
print("-" * len(hdr))
for (nm, bucket), rl in sorted(data.items(), key=lambda kv: (kv[0][1][0], kv[0][0])):
    ips = [get(r, "xiprim_1") for r in rl if get(r, "xiprim_1") is not None]
    b1 = [get(r, "xuiz1_bur1") for r in rl if get(r, "xuiz1_bur1") is not None]
    b2 = [get(r, "xuiz1_bur2") for r in rl if get(r, "xuiz1_bur2") is not None]
    b3 = [get(r, "xuiz1_bur3") for r in rl if get(r, "xuiz1_bur3") is not None]
    t12 = [get(r, "xtempmotor1_2") for r in rl if get(r, "xtempmotor1_2") is not None]
    om = [m for m in (other5_mean(r) for r in rl) if m is not None]
    lo, hi = bucket
    print(f"{nm:<26}{lo:>3}-{hi:>3}{len(rl):>7}{med(ips):>9.1f}{pct(ips,0.9):>9.1f}{med(b1):>7.0f}{med(b2):>7.0f}{med(b3):>7.0f}{med(t12):>8.1f}{med(om):>7.1f}{med(t12)-med(om):>+7.1f}")

# ------------------------------------------------------------------
print()
print("=" * 78)
print("TEST 2: 07-Aug thermal event 10:00-10:40 - coupled signals")
print("time | speed | Ip | xuzB1/2/3 | bg2tm1/2/3 (axle04 motor IP) | TM1_2 | other5")
print("=" * 78)
for r in rows:
    t = parse(r["devicetime"])
    if not t or t.day != 7 or not (t.hour == 10 and t.minute <= 40):
        continue
    if t.second % 20 != 0 and not (t.minute in (13, 20, 27, 34) and t.second < 10):
        continue
    om = other5_mean(r)
    b2m1 = get(r, "bg2tm1_ipvoltage"); b2m2 = get(r, "bg2tm2_ipvoltage"); b2m3 = get(r, "bg2tm3_ipvoltage")
    t12 = get(r, "xtempmotor1_2")
    if t12 is None:
        continue
    print(f"{t.strftime('%H:%M:%S')} {get(r,'xspeedloco'):>6.1f} {get(r,'xiprim_1'):>6.1f} "
          f"{get(r,'xuiz1_bur1'):>5.0f}/{get(r,'xuiz1_bur2'):>5.0f}/{get(r,'xuiz1_bur3'):>5.0f} "
          f"{b2m1 if b2m1 is not None else -1:>8.0f}/{b2m2 if b2m2 is not None else -1:>8.0f}/{b2m3 if b2m3 is not None else -1:>8.0f} "
          f"{t12:>7.1f} {om if om is not None else -1:>7.1f}")

# ------------------------------------------------------------------
print()
print("=" * 78)
print("TEST 3: 08-Aug pre-failure 15:49-17:25 - coupled signals (thinned)")
print("time | speed | Ip | xuzB1/2/3 | bg2tm1/2/3 (axle04 motor IP) | TM1_2 | other5")
print("=" * 78)
cnt = 0
for r in rows:
    t = parse(r["devicetime"])
    if not t or t.day != 8:
        continue
    if t.second % 20 != 0:
        continue
    om = other5_mean(r)
    b2m1 = get(r, "bg2tm1_ipvoltage"); b2m2 = get(r, "bg2tm2_ipvoltage"); b2m3 = get(r, "bg2tm3_ipvoltage")
    t12 = get(r, "xtempmotor1_2")
    if t12 is None:
        continue
    cnt += 1
    if cnt > 250:
        break
    print(f"{t.strftime('%H:%M:%S')} {get(r,'xspeedloco'):>6.1f} {get(r,'xiprim_1'):>6.1f} "
          f"{get(r,'xuiz1_bur1'):>5.0f}/{get(r,'xuiz1_bur2'):>5.0f}/{get(r,'xuiz1_bur3'):>5.0f} "
          f"{b2m1 if b2m1 is not None else -1:>8.0f}/{b2m2 if b2m2 is not None else -1:>8.0f}/{b2m3 if b2m3 is not None else -1:>8.0f} "
          f"{t12:>7.1f} {om if om is not None else -1:>7.1f}")

# ------------------------------------------------------------------
print()
print("=" * 78)
print("TEST 4: 08-Aug - bg2tm1 (axle04) vs bg2tm2/3 motor IP voltage distribution")
print("       Is axle-04 motor input voltage distinct (cut-out)?")
print("=" * 78)
b2m1 = [get(r, "bg2tm1_ipvoltage") for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 8 and get(r,"bg2tm1_ipvoltage") is not None]
b2m2 = [get(r, "bg2tm2_ipvoltage") for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 8 and get(r,"bg2tm2_ipvoltage") is not None]
b2m3 = [get(r, "bg2tm3_ipvoltage") for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 8 and get(r,"bg2tm3_ipvoltage") is not None]
b1m1 = [get(r, "bg1tm1_ipvoltage") for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == 8 and get(r,"bg1tm1_ipvoltage") is not None]
for nm, vals in [("bg1tm1(axle1)", b1m1), ("bg2tm1(axle04)", b2m1), ("bg2tm2(axle05)", b2m2), ("bg2tm3(axle06)", b2m3)]:
    m = med(vals)
    print(f"  {nm:<16} n={len(vals):>5} med={m:>8.1f} p05={pct(vals,0.05):>8.1f} p95={pct(vals,0.95):>8.1f} max={max(vals) if vals else -1:>8.1f}")

# ------------------------------------------------------------------
print()
print("=" * 78)
print("TEST 5: 07-Aug and 08-Aug - xiprim_1 (primary current) at SPEED 20-40, per hour")
print("       (comparable running condition; both days running 20-40 km/h)")
print("=" * 78)
for day, hrange in [(7, (10,11)), (7, (14,20)), (8, (15,17))]:
    sel = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == day and hrange[0] <= parse(r["devicetime"]).hour <= hrange[1]]
    run = [r for r in sel if get(r, "xspeedloco") is not None and 20 <= get(r,"xspeedloco") < 40 and get(r,"ltedemand") == 1]
    ips = [get(r, "xiprim_1") for r in run if get(r,"xiprim_1") is not None]
    t12 = [get(r, "xtempmotor1_2") for r in run if get(r,"xtempmotor1_2") is not None]
    om = [m for m in (other5_mean(r) for r in run) if m is not None]
    print(f"  0{day}/08 {hrange[0]:02d}-{hrange[1]:02d}  n={len(run):>5}  Ip med={med(ips):>6.1f} p90={pct(ips,0.9):>6.1f}  TM1_2 med={med(t12):>6.1f}  other5 med={med(om):>6.1f}  dT={med(t12)-med(om):+7.1f}")

# ------------------------------------------------------------------
print()
print("=" * 78)
print("TEST 6: energy consumption rate (xenergymwh_ec slope) per day, during running")
print("       d(MWh)/row during traction-active running = effort indicator")
print("=" * 78)
for day in (5, 6, 7, 8):
    sel = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).day == day and get(r,"xspeedloco") and get(r,"xspeedloco") > 10 and get(r,"ltedemand") == 1]
    if len(sel) < 10:
        print(f"  0{day}/08  n={len(sel)}  (too few)")
        continue
    mwh = [get(r, "xenergymwh_ec") for r in sel if get(r,"xenergymwh_ec") is not None]
    times = [parse(r["devicetime"]) for r in sel]
    if mwh[-1] - mwh[0] <= 0:
        print(f"  0{day}/08  energy meter not incrementing (n={len(sel)})")
        continue
    dt = (times[-1] - times[0]).total_seconds()
    dm = mwh[-1] - mwh[0]
    print(f"  0{day}/08  n={len(sel)}  dMWh={dm:>8.1f} over {dt/60:>6.0f} min  rate={dm*60.0/dt*1000:>7.1f} kWh/min")
