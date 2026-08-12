import csv, html
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

tcols = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]
tlab  = {"xtempmotor1_1":"TM1_1","xtempmotor2_1":"TM2_1","xtempmotor3_1":"TM3_1",
         "xtempmotor1_2":"TM1_2","xtempmotor2_2":"TM2_2","xtempmotor3_2":"TM3_2"}

def other5_median(r):
    vals = [f(r[c]) for c in tcols]
    ok = [v for v in (vals[:3]+vals[4:]) if v is not None and v < 75.99]
    if not ok:
        return None
    ok = sorted(ok)
    n = len(ok)
    return ok[n//2] if n % 2 else (ok[n//2-1]+ok[n//2])/2

recs = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        t = parse(r["devicetime"])
        if not t or t.month != 8 or t.day != 7:
            continue
        sec = t.hour*3600 + t.minute*60 + t.second
        if 19*3600 + 15*60 <= sec <= 19*3600 + 50*60:
            recs.append((t, r))
recs.sort(key=lambda x: x[0])
print("window rows:", len(recs))

# ------------------------------------------------------------- aligned dump, ~2 s stride
print("\n=== aligned 2-s dump: time | v | Ip | xang | lte/lbe | TM1_2 | other5 | bur3A | axle1/04/5 ===")
prev = None
for t, r in recs:
    if prev is None or (t - prev).total_seconds() >= 2:
        prev = t
        v  = f(r["xspeedloco"]); ip = f(r["xiprim_1"]); xa = f(r["xangtrans"])
        lte = f(r["ltedemand"]); lbe = f(r["lbedemand"])
        t12 = f(r["xtempmotor1_2"]); o5 = other5_median(r)
        b3 = f(r["xuiz1_bur3"])
        a1 = f(r["xvist_a1_1"]); a04 = f(r["xvist_a1_2"]); a5 = f(r["xvist_a2_2"])
        def s(x): return "-" if x is None else f"{x:5.1f}"
        print(f"{t.strftime('%H:%M:%S')}  v={s(v)} Ip={s(ip)} xang={s(xa)} "
              f"lte={lte:.0f}/lbe={lbe:.0f} TM1_2={s(t12)} o5={s(o5)} "
              f"bur3={s(b3)} a1={s(a1)} a04={s(a04)} a5={s(a5)}")
