import csv
from datetime import datetime
from collections import defaultdict

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
    if not vals:
        return float("nan")
    return vals[len(vals)//2] if len(vals) % 2 else (vals[len(vals)//2-1]+vals[len(vals)//2])/2

tcols = ["xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2"]
def other5_mean(r):
    vals = [f(r[c]) for c in tcols]
    ok = [v for v in (vals[:3] + vals[4:]) if v is not None and v < 75.99]
    return sum(ok)/len(ok) if ok else None

rows = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)

# build time-ordered list with v, a, Ip, lte, t, TM1_2, other5
recs = []
for r in rows:
    t = parse(r["devicetime"])
    if not t:
        continue
    v = f(r["xspeedloco"])
    ip = f(r["xiprim_1"])
    lte = f(r["ltedemand"])
    if v is None or ip is None or lte is None:
        continue
    recs.append([t, v, ip, lte, f(r["xtempmotor1_2"]), other5_mean(r)])
recs.sort(key=lambda x: x[0])

# acceleration: dv/dt in km/h per second -> m/s^2
for i in range(1, len(recs)):
    dt = (recs[i][0] - recs[i-1][0]).total_seconds()
    if 0 < dt <= 5:
        a = (recs[i][1] - recs[i-1][1]) * 1000.0 / 3600.0 / dt  # m/s^2
        recs[i-1].append(a)
    else:
        recs[i-1].append(None)
recs[-1].append(None)

def in_period(t, p):
    (d1, m1), (d2, m2) = p
    return datetime(2026, m1, d1) <= t <= datetime(2026, m2, d2, 23, 59, 59)

PER_BASELINE = ((27,7),(3,8))

# ---------------- verify 07/08 19:00-21:00 motion context
print("=" * 70)
print("07/08 19:00-21:00 - motion / temps context (why cold state appears)")
print("=" * 70)
cnt = 0
for t, v, ip, lte, t12, om, a in recs:
    if t.month == 8 and t.day == 7 and 19 <= t.hour < 21:
        if t.second % 15 == 0:
            cnt += 1
            if cnt <= 60:
                print(f"  {t.strftime('%H:%M:%S')} v={v:5.1f} Ip={ip:5.1f} lte={lte:.0f} TM1_2={t12 if t12 is not None else -1:6.1f} other5={om if om is not None else -1:6.1f}")

# ---------------- TEST B: baseline I=f(v,a) from 27Jul-03Aug, residual for 06/07/08
print("\n" + "=" * 70)
print("TEST B: I_excess = I_obs - f(v,a). Baseline f(v,a)=median Ip from 27Jul-03Aug")
print("Speed bins: 0-10/10-20/20-30/30-40/40-50/50+. Accel bins: <-0.3/-0.3..-0.1/-0.1..0.1/0.1..0.3/>0.3 m/s2")
print("Only lte=1 (traction active). a = dv/dt (km/h->m/s2 per 1-5s step).")
print("=" * 70)
Vbins = [(0,10),(10,20),(20,30),(30,40),(40,50),(50,1e9)]
Abins = [(-1e9,-0.3),(-0.3,-0.1),(-0.1,0.1),(0.1,0.3),(0.3,1e9)]

base = defaultdict(list)
for t, v, ip, lte, t12, om, a in recs:
    if lte != 1 or a is None or not in_period(t, PER_BASELINE):
        continue
    vb = None
    for lo, hi in Vbins:
        if lo <= v < hi:
            vb = (lo, hi)
            break
    if vb is None:
        continue
    ab = None
    for lo, hi in Abins:
        if lo <= a < hi:
            ab = (lo, hi)
            break
    if ab is None:
        continue
    base[(vb, ab)].append(ip)

# fill empty baseline bins with nearest (simple: skip empty)
basemodel = {}
for k in base:
    basemodel[k] = med(base[k])

# report coverage + apply
print("\nBaseline coverage (n per (vbin,abin)) and median:")
print("  vbin\\abin     " + "  ".join(f"a<{hi:.1f}" if lo < -0.3 else (f"{lo:.1f}<a<{hi:.1f}" if lo < 0.1 else f"a>{lo:.1f}") for lo, hi in Abins))
for vb in Vbins:
    line = f"  v{vb[0]:<3}-{vb[1] if vb[1]<1e9 else '50+'}: "
    for ab in Abins:
        k = (vb, ab)
        n = len(base.get(k, []))
        m = basemodel.get(k, float("nan"))
        line += f"{n if n else 0:>5} " if n == 0 else f"{m:>5.0f} "
    print(line)

# residual for target windows
print("\nI_excess (median) vs baseline model, per period & speed bin (traction active):")
targets = [("06-Aug", ((6,8),(6,8))), ("07-Aug", ((7,8),(7,8))), ("08-Aug", ((8,8),(8,8)))]
out = defaultdict(list)
for t, v, ip, lte, t12, om, a in recs:
    if lte != 1 or a is None:
        continue
    for nm, p in targets:
        if in_period(t, p):
            vb = None
            for lo, hi in Vbins:
                if lo <= v < hi:
                    vb = (lo, hi); break
            if vb is None: break
            ab = None
            for lo, hi in Abins:
                if lo <= a < hi:
                    ab = (lo, hi); break
            if ab is None: break
            bm = basemodel.get((vb, ab))
            if bm is not None:
                out[(nm, vb)].append((ip - bm, t12, om, v))
            break

for (nm, vb), pts in sorted(out.items(), key=lambda kv: (kv[0][1][0], kv[0][0])):
    res = [p[0] for p in pts]
    t12 = [p[1] for p in pts if p[1] is not None]
    om = [p[2] for p in pts if p[2] is not None]
    vmed = med([p[3] for p in pts])
    print(f"  {nm:<10} v{vb[0]:<3}-{vb[1] if vb[1]<1e9 else '50+'}: n={len(pts):<5} "
          f"I_excess med={med(res):+6.1f} A   (TM1_2={med(t12):5.1f} other5={med(om):5.1f})")

# ---------------- TEST D: current->temperature lag, 07/08 09:30-11:30
print("\n" + "=" * 70)
print("TEST D: cross-correlation of TM1_2 dT vs primary current lag (07/08 09:30-11:30)")
print("positive tau = current leads temp. Coarse lag in seconds over 1-s series.")
print("=" * 70)
w = [(t, ip, t12) for t, v, ip, lte, t12, om, a in recs
     if t.month == 8 and t.day == 7 and 9.5*3600 <= t.hour*3600 + t.minute*60 + t.second <= 11.5*3600]
n = len(w)
ipv = [p[1] for p in w]
t12v = [p[2] for p in w]
dT = [t12v[i] - t12v[0] for i in range(n)]
# demean
def demean(x):
    m = sum(x)/len(x)
    return [v-m for v in x]
ipd = demean(ipv)
t12d = demean([p[2] for p in w])
ipv2 = demean(ipv)
# corr at lags -60..+60 (samples ~1s)
print("  tau(s)  corr(T,dTlaggedI)  corr(T, dTlaggedT)")
for tau in (-60, -45, -30, -20, -15, -10, -5, -2, 0, 2, 5, 10, 15, 20, 30, 45, 60):
    # corr(dT(t), Ip(t-tau))  i.e. Ip leading by tau
    pairs = []
    for i in range(n):
        j = i - tau
        if 0 <= j < n:
            pairs.append((t12d[i], ipv2[j]))
    if len(pairs) < 50:
        continue
    sx = sum(p[0] for p in pairs); sy = sum(p[1] for p in pairs)
    sxx = sum(p[0]*p[0] for p in pairs); syy = sum(p[1]*p[1] for p in pairs); sxy = sum(p[0]*p[1] for p in pairs)
    denom = ((sxx - sx*sx/len(pairs)) * (syy - sy*sy/len(pairs))) ** 0.5
    c = (sxy - sx*sy/len(pairs)) / denom if denom else 0
    # autocorr of dT
    pairs2 = []
    for i in range(n):
        j = i - tau
        if 0 <= j < n:
            pairs2.append((t12d[i], t12d[j]))
    sx = sum(p[0] for p in pairs2); sy = sum(p[1] for p in pairs2)
    sxx = sum(p[0]*p[0] for p in pairs2); syy = sum(p[1]*p[1] for p in pairs2); sxy = sum(p[0]*p[1] for p in pairs2)
    denom2 = ((sxx - sx*sx/len(pairs2)) * (syy - sy*sy/len(pairs2))) ** 0.5
    c2 = (sxy - sx*sy/len(pairs2)) / denom2 if denom2 else 0
    print(f"  {tau:>5}   {c:+.3f}   {c2:+.3f}")
