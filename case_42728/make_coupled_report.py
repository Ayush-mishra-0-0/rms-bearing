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

def other5_mean(r):
    vals = [f(r[c]) for c in tcols]
    ok = [v for v in (vals[:3] + vals[4:]) if v is not None and v < 75.99]
    return sum(ok) / len(ok) if ok else None

# ---------------------------------------------------------------- downsample
def downsample(rows, keyf, every_sec):
    """group by floor(epoch/every_sec), median per key"""
    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        t = parse(r["devicetime"])
        if not t:
            continue
        k = int(t.timestamp() // every_sec)
        for name in keyf:
            pass
    # simpler: return median of each numeric key per bucket
    buckets = defaultdict(lambda: defaultdict(list))
    for r in rows:
        t = parse(r["devicetime"])
        if not t:
            continue
        k = int(t.timestamp() // every_sec)
        for name in keyf:
            v = keyf[name](r)
            if v is not None:
                buckets[k][name].append(v)
    out = []
    for k in sorted(buckets):
        d = buckets[k]
        rec = {"t": datetime.fromtimestamp(k * every_sec + every_sec / 2)}
        for name in keyf:
            rec[name] = sorted(d[name])[len(d[name]) // 2] if d[name] else None
        out.append(rec)
    return out

# ---------------------------------------------------------------- SVG chart
def svg_line(title, x, series, w=1100, h=360, xlabel="", ylabel="", regimes=None):
    # series: list of (name, color, values) where values aligned to x
    pad_l, pad_r, pad_t, pad_b = 60, 16, 46, 40
    xmin, xmax = min(x), max(x)
    allv = [v for _, _, vs in series for v in vs if v is not None]
    ymin, ymax = min(allv), max(allv)
    if ymin == ymax:
        ymax += 1
    pad_y = (ymax - ymin) * 0.06
    ymin -= pad_y; ymax += pad_y
    iw, ih = w, h
    def X(v): return pad_l + (v - xmin) / (xmax - xmin) * (iw - pad_l - pad_r)
    def Y(v): return ih - pad_b - (v - ymin) / (ymax - ymin) * (ih - pad_t - pad_b)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{iw}" height="{ih}" viewBox="0 0 {iw} {ih}">']
    s.append(f'<rect x="0" y="0" width="{iw}" height="{ih}" fill="#ffffff"/>')
    s.append(f'<text x="{iw/2}" y="20" font-size="15" font-weight="bold" text-anchor="middle" fill="#111">{html.escape(title)}</text>')
    # regimes shading
    if regimes:
        for (x0, x1, col, label) in regimes:
            s.append(f'<rect x="{X(x0):.1f}" y="{pad_t:.0f}" width="{X(x1)-X(x0):.1f}" height="{ih-pad_t-pad_b:.0f}" fill="{col}" opacity="0.14"/>')
            s.append(f'<text x="{(X(x0)+X(x1))/2:.1f}" y="{pad_t-6:.0f}" font-size="10" text-anchor="middle" fill="#333">{label}</text>')
    # grid + y labels
    nyt = 6
    for i in range(nyt + 1):
        v = ymin + (ymax - ymin) * i / nyt
        s.append(f'<line x1="{pad_l}" y1="{Y(v):.1f}" x2="{iw-pad_r}" y2="{Y(v):.1f}" stroke="#e5e5e5"/>')
        s.append(f'<text x="{pad_l-6}" y="{Y(v)+3.5:.1f}" font-size="10" text-anchor="end" fill="#555">{v:.0f}</text>')
    # x ticks (n labels)
    nxt = 8
    for i in range(nxt + 1):
        v = xmin + (xmax - xmin) * i / nxt
        s.append(f'<line x1="{X(v):.1f}" y1="{pad_t}" x2="{X(v):.1f}" y2="{ih-pad_b}" stroke="#eeeeee"/>')
        s.append(f'<text x="{X(v):.1f}" y="{ih-pad_b+16}" font-size="10" text-anchor="middle" fill="#555">{xlabel(v)}</text>')
    for name, color, values in series:
        pts = [(X(x[i]), Y(values[i])) for i in range(len(x)) if values[i] is not None]
        if not pts:
            continue
        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
        s.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.4"/>')
    # legend
    lx = pad_l + 8
    for name, color, _ in series:
        s.append(f'<rect x="{lx}" y="{pad_t-18}" width="14" height="4" fill="{color}"/>')
        s.append(f'<text x="{lx+18}" y="{pad_t-14}" font-size="10" fill="#333">{html.escape(name)}</text>')
        lx += 18 + len(name) * 6.5
    s.append('</svg>')
    return "\n".join(s)

# ---------------------------------------------------------------- load
print("loading rows...")
rows = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        rows.append(r)
print("rows:", len(rows))

T = datetime(2026, 8, 10, 12, 0).timestamp()

def xlab_ts(v):
    dt = datetime.fromtimestamp(v)
    return f"{dt.month:02d}-{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}"

def xlab_min(v):
    dt = datetime.fromtimestamp(v)
    return f"{dt.day:02d}/{dt.hour:02d}:{dt.minute:02d}"

# ============================================================== PANEL 1: full window temps
keyf = {
    "TM1_2": lambda r: f(r["xtempmotor1_2"]),
    "other5": other5_mean,
    "dT": lambda r: (lambda o: f(r["xtempmotor1_2"]) - o if (o is not None and f(r["xtempmotor1_2"]) is not None) else None)(other5_mean(r)),
}
print("panel1...")
ds = downsample(rows, keyf, 120)
x = [r["t"].timestamp() for r in ds]
p1a = svg_line("AXLE-04 (TM1_2) vs mean of other 5 motors - TEMPERATURE (full window, 2-min median)",
    x, [("TM1_2 axle04", "#c0392b", [r["TM1_2"] for r in ds]),
        ("other-5 mean", "#2471a3", [r["other5"] for r in ds])],
    xlabel=xlab_ts, regimes=[(datetime(2026,8,6).timestamp(), datetime(2026,8,9).timestamp(), "#f39c12", "06-08 Aug")])
p1b = svg_line("DELTA T04 = TM1_2 - median(other 5) - full window (2-min median)",
    x, [("dT04 (degC)", "#8e44ad", [r["dT"] for r in ds])],
    xlabel=xlab_ts, regimes=[(datetime(2026,8,6).timestamp(), datetime(2026,8,9).timestamp(), "#f39c12", "06-08 Aug")])

# ============================================================== PANEL 2: full window Ip + speed
keyf2 = {
    "Ip": lambda r: f(r["xiprim_1"]) if f(r.get("ltedemand")) == 1 else None,
    "speed": lambda r: f(r["xspeedloco"]),
}
print("panel2...")
ds2 = downsample(rows, keyf2, 120)
x2 = [r["t"].timestamp() for r in ds2]
p2 = svg_line("PRIMARY CURRENT (traction-active, xiprim_1) - full window (2-min median)",
    x2, [("Ip (A)", "#1a7d3c", [r["Ip"] for r in ds2])], xlabel=xlab_ts,
    regimes=[(datetime(2026,8,6).timestamp(), datetime(2026,8,9).timestamp(), "#f39c12", "06-08 Aug")])
p2b = svg_line("LOCO SPEED xspeedloco - full window (2-min median)",
    x2, [("speed (km/h)", "#2874a6", [r["speed"] for r in ds2])], xlabel=xlab_ts,
    regimes=[(datetime(2026,8,6).timestamp(), datetime(2026,8,9).timestamp(), "#f39c12", "06-08 Aug")])

# ============================================================== PANEL 3: 07-Aug thermal event
print("panel3...")
w7 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).month == 8 and parse(r["devicetime"]).day == 7
      and 9 <= parse(r["devicetime"]).hour * 60 + parse(r["devicetime"]).minute <= 11 * 60]
keyf3 = {
    "TM1_2": lambda r: f(r["xtempmotor1_2"]),
    "other5": other5_mean,
    "Ip": lambda r: f(r["xiprim_1"]),
    "speed": lambda r: f(r["xspeedloco"]),
}
ds3 = downsample(w7, keyf3, 10)
x3 = [r["t"].timestamp() for r in ds3]
p3a = svg_line("07-Aug 09:00-11:00 THERMAL EVENT - temp (10-s median)",
    x3, [("TM1_2 axle04", "#c0392b", [r["TM1_2"] for r in ds3]),
         ("other-5 mean", "#2471a3", [r["other5"] for r in ds3])], xlabel=xlab_min)
p3b = svg_line("07-Aug 09:00-11:00 - PRIMARY CURRENT + SPEED (10-s median)",
    x3, [("Ip (A)", "#1a7d3c", [r["Ip"] for r in ds3]),
         ("speed (km/h)", "#2874a6", [r["speed"] for r in ds3])], xlabel=xlab_min)

# ============================================================== PANEL 4: 08-Aug pre-failure
print("panel4...")
w8 = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).month == 8 and parse(r["devicetime"]).day == 8]
keyf4 = {
    "TM1_2": lambda r: f(r["xtempmotor1_2"]),
    "other5": other5_mean,
    "Ip": lambda r: f(r["xiprim_1"]),
    "speed": lambda r: f(r["xspeedloco"]),
}
ds4 = downsample(w8, keyf4, 15)
x4 = [r["t"].timestamp() for r in ds4]
p4a = svg_line("08-Aug PRE-FAILURE 15:49-17:25 - temp (15-s median)",
    x4, [("TM1_2 axle04", "#c0392b", [r["TM1_2"] for r in ds4]),
         ("other-5 mean", "#2471a3", [r["other5"] for r in ds4])], xlabel=xlab_min)
p4b = svg_line("08-Aug PRE-FAILURE - PRIMARY CURRENT + SPEED (15-s median)",
    x4, [("Ip (A)", "#1a7d3c", [r["Ip"] for r in ds4]),
         ("speed (km/h)", "#2874a6", [r["speed"] for r in ds4])], xlabel=xlab_min)

# ============================================================== PANEL 5: Test C axle speeds
print("panel5 (axle speeds)...")
vcols = ["xvist_a1_1","xvist_a2_1","xvist_a3_1","xvist_a1_2","xvist_a2_2","xvist_a3_2"]
def axkf(name):
    return lambda r: f(r.get(name)) if f(r.get(name)) is not None and f(r.get(name)) < 1000 else None
keyf5 = {
    "axle1": lambda r: f(r["xvist_a1_1"]),
    "axle2": lambda r: f(r["xvist_a2_1"]),
    "axle3": lambda r: f(r["xvist_a3_1"]),
    "axle04": lambda r: f(r["xvist_a1_2"]),
    "axle5": lambda r: f(r["xvist_a2_2"]),
}
# 08/08 window axle speeds
w8a = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).month == 8 and parse(r["devicetime"]).day == 8]
ds5 = downsample(w8a, {"a1_1": lambda r, k="xvist_a1_1": (lambda v: v if v is not None and v < 1000 else None)(f(r[k])),
                        "a2_1": lambda r, k="xvist_a2_1": (lambda v: v if v is not None and v < 1000 else None)(f(r[k])),
                        "a3_1": lambda r, k="xvist_a3_1": (lambda v: v if v is not None and v < 1000 else None)(f(r[k])),
                        "a1_2": lambda r, k="xvist_a1_2": (lambda v: v if v is not None and v < 1000 else None)(f(r[k])),
                        "a2_2": lambda r, k="xvist_a2_2": (lambda v: v if v is not None and v < 1000 else None)(f(r[k]))}, 15)
x5 = [r["t"].timestamp() for r in ds5]
p5a = svg_line("08-Aug PRE-FAILURE - ALL AXLE SPEEDS (15-s median) - axle04 tracks pack",
    x5, [("axle1", "#2c3e50", [r["a1_1"] for r in ds5]),
         ("axle2", "#7f8c8d", [r["a2_1"] for r in ds5]),
         ("axle3", "#95a5a6", [r["a3_1"] for r in ds5]),
         ("axle04", "#e74c3c", [r["a1_2"] for r in ds5]),
         ("axle5", "#34495e", [r["a2_2"] for r in ds5])], xlabel=xlab_min)
# 09/08 window: axle04 dead at 3276
w9a = [r for r in rows if parse(r["devicetime"]) and parse(r["devicetime"]).month == 8 and parse(r["devicetime"]).day == 9]
ds6 = downsample(w9a, {"a1_1": lambda r, k="xvist_a1_1": (lambda v: v if v is not None and v < 1000 else None)(f(r[k])),
                        "a2_1": lambda r, k="xvist_a2_1": (lambda v: v if v is not None and v < 1000 else None)(f(r[k])),
                        "a3_1": lambda r, k="xvist_a3_1": (lambda v: v if v is not None and v < 1000 else None)(f(r[k])),
                        "a1_2": lambda r, k="xvist_a1_2": (lambda v: v if v is not None and v < 1000 else None)(f(r[k])),
                        "a2_2": lambda r, k="xvist_a2_2": (lambda v: v if v is not None and v < 1000 else None)(f(r[k]))}, 15)
x6 = [r["t"].timestamp() for r in ds6]
p5b = svg_line("09-Aug (day after lock) - AXLE SPEEDS (15-s median) - axle04 channel DEAD(3276)",
    x6, [("axle1", "#2c3e50", [r["a1_1"] for r in ds6]),
         ("axle2", "#7f8c8d", [r["a2_1"] for r in ds6]),
         ("axle3", "#95a5a6", [r["a3_1"] for r in ds6]),
         ("axle04", "#e74c3c", [r["a1_2"] for r in ds6]),
         ("axle5", "#34495e", [r["a2_2"] for r in ds6])], xlabel=xlab_min)

# ============================================================== PANEL 6: Test B residual (bar)
print("panel6 (residual bars)...")
# recompute I_excess median per period/vbin from test_B_plus logic (compact)
def in_period2(t, p):
    (d1, m1), (d2, m2) = p
    return datetime(2026, m1, d1) <= t <= datetime(2026, m2, d2, 23, 59, 59)
Vbins = [(0,10),(10,20),(20,30),(30,40),(40,50),(50,1e9)]
Abins = [(-1e9,-0.3),(-0.3,-0.1),(-0.1,0.1),(0.1,0.3),(0.3,1e9)]
recs = []
for r in rows:
    t = parse(r["devicetime"])
    if not t:
        continue
    v = f(r["xspeedloco"]); ip = f(r["xiprim_1"]); lte = f(r["ltedemand"])
    if v is None or ip is None or lte is None:
        continue
    recs.append([t, v, ip, lte])
recs.sort(key=lambda x: x[0])
for i in range(1, len(recs)):
    dt = (recs[i][0]-recs[i-1][0]).total_seconds()
    if 0 < dt <= 5:
        a = (recs[i][1]-recs[i-1][1])*1000.0/3600.0/dt
        recs[i-1].append(a)
    else:
        recs[i-1].append(None)
recs[-1].append(None)
bmod = {}
bcnt = {}
for t, v, ip, lte, a in recs:
    if lte != 1 or a is None or not in_period2(t, ((27,7),(3,8))):
        continue
    vb = next((vb for lo, hi in Vbins if lo <= v < hi for vb in [None]), None)
    for lo, hi in Vbins:
        if lo <= v < hi:
            vb = (lo, hi); break
    ab = None
    for lo, hi in Abins:
        if lo <= a < hi:
            ab = (lo, hi); break
    if vb is None or ab is None:
        continue
    bcnt.setdefault((vb, ab), []).append(ip)
for k, vl in bcnt.items():
    bmod[k] = sorted(vl)[len(vl)//2]
# residual per period & vbin
resid = {}
for t, v, ip, lte, a in recs:
    if lte != 1 or a is None:
        continue
    for nm, p in [("06-Aug",((6,8),(6,8))), ("07-Aug",((7,8),(7,8))), ("08-Aug",((8,8),(8,8)))]:
        if in_period2(t, p):
            vb = None
            for lo, hi in Vbins:
                if lo <= v < hi:
                    vb = (lo, hi); break
            ab = None
            for lo, hi in Abins:
                if lo <= a < hi:
                    ab = (lo, hi); break
            if vb is None or ab is None:
                break
            bm = bmod.get((vb, ab))
            if bm is not None:
                resid.setdefault((nm, vb), []).append(ip - bm)
            break
# bar chart: median residual per period per vbin
bv = []
for (nm, vb), rl in resid.items():
    bv.append((nm, vb, sorted(rl)[len(rl)//2]))
x7 = [i for i in range(len(bv))]
colors = {"06-Aug": "#e67e22", "07-Aug": "#c0392b", "08-Aug": "#8e44ad"}
bars_svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="300" viewBox="0 0 1100 300">']
bars_svg.append('<rect width="1100" height="300" fill="#fff"/>')
bars_svg.append('<text x="550" y="18" font-size="14" font-weight="bold" text-anchor="middle">TEST B - I_excess (A) vs baseline f(v,a) model, per period & speed bin (median)</text>')
allv = [r[2] for r in bv]
ymin = min(allv + [0]); ymax = max(allv + [0])
if ymin > -5: ymin = -5
if ymax < 5: ymax = 5
pl, pr, pt, pb = 50, 10, 40, 40
def BY(v): return 300 - pb - (v - ymin)/(ymax - ymin)*(300 - pt - pb)
bars_svg.append(f'<line x1="{pl}" y1="{BY(0)}" x2="1090" y2="{BY(0)}" stroke="#999"/>')
for i in range(int(ymin), int(ymax)+1, 10):
    bars_svg.append(f'<text x="{pl-4}" y="{BY(i)+3}" font-size="10" text-anchor="end" fill="#555">{i}</text>')
for idx, (nm, vb, val) in enumerate(bv):
    w = 40
    x0 = pl + idx * (w + 4)
    hgt = abs(val) * (300 - pt - pb)/(ymax - ymin)
    y0 = BY(val) if val >= 0 else BY(0)
    bars_svg.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{max(hgt,1):.1f}" fill="{colors[nm]}" opacity="0.85"/>')
    bars_svg.append(f'<text x="{x0+w/2}" y="{BY(0)+14}" font-size="9" text-anchor="middle" fill="#333">{vb[0]}{"-" if vb[1]>=1e9 else "-"+(str(vb[1]) if vb[1]<50 else "50+")}</text>')
# second text line for period
bars_svg.append('<text x="550" y="290" font-size="10" text-anchor="middle" fill="#666">color: 06-Aug=orange, 07-Aug=red, 08-Aug=purple. x = speed bin. bars = median I_excess (A).</text>')
bars_svg.append('</svg>')
p6 = "\n".join(bars_svg)

# ============================================================== PANEL 7: Test E response curves
print("panel7 (Test E response)...")
def other5_mean(r):
    vals = [f(r[c]) for c in tcols]
    ok = [v for v in (vals[:3]+vals[4:]) if v is not None and v < 75.99]
    return sum(ok)/len(ok) if ok else None
IpB = [(0,20),(20,40),(40,60),(60,80),(80,120),(120,1e9)]
def resp_series(p, want):
    out = []
    for lo, hi in IpB:
        sel = []
        for r in rows:
            t = parse(r["devicetime"])
            if not t or not in_period2(t, p):
                continue
            v = f(r["xspeedloco"]); ip = f(r["xiprim_1"]); lte = f(r["ltedemand"])
            if v is None or ip is None or lte != 1 or v <= 20:
                continue
            if lo <= ip < hi:
                val = f(r["xtempmotor1_2"]) if want == "t12" else other5_mean(r)
                if val is not None:
                    sel.append(val)
        out.append(sorted(sel)[len(sel)//2] if sel else None)
    return out
x8 = [i for i in range(len(IpB))]
def xlab8(v):
    return f"{IpB[int(v)][0]}-{IpB[int(v)][1]}" if IpB[int(v)][1] < 1e9 else f"{IpB[int(v)][0]}+"
p7a = svg_line("TEST E - TM1_2 response vs primary current (speed>20, traction) - 07/08 vs 08/08",
    x8, [("TM1_2 07-Aug", "#c0392b", resp_series(((7,8),(7,8)), "t12")),
         ("TM1_2 08-Aug", "#8e44ad", resp_series(((8,8),(8,8)), "t12")),
         ("TM1_2 baseline", "#95a5a6", resp_series(((27,7),(3,8)), "t12"))],
    xlabel=xlab8, ylabel="deg C")
p7b = svg_line("TEST E - other-5 mean response vs primary current (speed>20, traction)",
    x8, [("other5 07-Aug", "#c0392b", resp_series(((7,8),(7,8)), "om")),
         ("other5 08-Aug", "#8e44ad", resp_series(((8,8),(8,8)), "om")),
         ("other5 baseline", "#95a5a6", resp_series(((27,7),(3,8)), "om"))],
    xlabel=xlab8, ylabel="deg C")


# ============================================================== write HTML
html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>42728 coupled-signal analysis</title>
<style>body{{font-family:Consolas,monospace;background:#fafafa;margin:20px;color:#222}}
h1{{font-size:18px}}h2{{font-size:15px;margin-top:30px;border-bottom:1px solid #ccc;padding-bottom:4px}}
.section{{background:#fff;border:1px solid #ddd;padding:14px;margin-bottom:18px;border-radius:6px}}
table{{border-collapse:collapse;font-size:12px}}td,th{{border:1px solid #ccc;padding:3px 8px;text-align:right}}
th{{background:#eef}} .k{{text-align:left}}
.note{{background:#fff8dc;border:1px solid #e6d68a;padding:10px;border-radius:6px;font-size:12px}}</style></head><body>
<h1>Loco 42728 — coupled-signal analysis (friction → resistance → traction effort → temperature)</h1>
<p>Failure ground truth: <b>08-Aug-2026 19:26, axle locked — 2nd bogie, 04 axle</b> (SinglePageFailureReport).
Telemetry: 155,095 rows (Equus feed) 27-Jul→10-Aug 2026. Charts are SVG (matplotlib unavailable in this env).</p>
<div class="section"><h2>Plot A — all six TM temperatures / Plot B — relative dT04</h2>
{p1a}
{p1b}
<div class="note"><b>Read:</b> through 05-Aug TM1_2 tracks the pack (dT04 ≈ 0). 06-Aug afternoon dT04 rises
(+9…+10 °C). 07-Aug 10:13–10:34 massive spike to 91.7 °C (dT04 +19.7). On 08-Aug TM1_2 goes <i>cold</i>
(≈ 37–40 °C, dT04 −27.7) while the other 5 motors run 60–74 °C — axle-04 no longer contributing, the
remaining five carrying the train. Telemetry gap 08-Aug 17:25 → 09-Aug 14:25 covers the 19:26 lock event.</div></div>

<div class="section"><h2>Electrical effort (primary current) + speed, full window</h2>
{p2}
{p2b}
<div class="note"><b>Read:</b> primary current is <i>not</i> simply higher over time — it depends on speed/traction
command/grade. The correct comparison is current <i>conditioned on speed AND acceleration</i> (Test B below).
The energy counter (xenergymwh_ec) is a cumulative meter with unverified units — only the statement
"the counter changes more rapidly during the failure-day running window" is safe; the raw kWh/min figure
should NOT be quoted to senior.</div></div>

<div class="section"><h2>Window 3 — 07-Aug 10:00–10:40 thermal event (aligned signals)</h2>
{p3a}
{p3b}
<div class="note"><b>Read:</b> at the thermal peak (10:13–10:27, TM1_2 83→91.7 °C) the loco was doing ~53–55 km/h
with Ip ≈ 70–92 A, then <b>speed decayed to ~40 km/h and to 0 by 10:34</b> as temperature crested — the
locomotive could not hold speed while axle-04 overheated. All six bg*tm* IP voltages are equal (≈1713 V) —
they are the shared DC-link, not a per-axle effort signal.</div></div>

<div class="section"><h2>Window 4 — 08-Aug 15:49–17:25 pre-failure state</h2>
{p4a}
{p4b}
<div class="note"><b>Read:</b> axle-04 (TM1_2) is flat-cold ≈ 37–40 °C for the whole session while the other five
run 48–74 °C and the loco accelerates to 60–73 km/h with primary current up to 130–144 A (17:17–17:18,
accel to 2180 V DC-link). This is the state the 5-other-motors hypothesis predicts just before a lock:
axle-04 motor cut out / unloaded, remaining traction system doing all the work.</div></div>

<div class="section"><h2>TEST 1 — median primary current vs speed bucket (traction-active only)</h2>
<table>
<tr><th>period</th><th>bucket km/h</th><th>n</th><th>Ip med</th><th>Ip p90</th><th>TM1_2</th><th>other5</th><th>dT</th></tr>
<tr><td class="k">06-Aug</td><td>0-10</td><td>631</td><td>13.2</td><td>22.0</td><td>50.6</td><td>49.1</td><td>+1.5</td></tr>
<tr><td class="k">07-Aug</td><td>0-10</td><td>266</td><td>14.5</td><td>27.8</td><td>39.9</td><td>40.2</td><td>-0.3</td></tr>
<tr><td class="k">08-Aug</td><td>0-10</td><td>169</td><td>12.7</td><td>16.6</td><td>37.6</td><td>53.4</td><td>-15.8</td></tr>
<tr><td class="k">BASELINE 27Jul-03Aug</td><td>0-10</td><td>7603</td><td>12.5</td><td>20.8</td><td>45.9</td><td>45.9</td><td>-0.0</td></tr>
<tr><td class="k">06-Aug</td><td>10-20</td><td>307</td><td>27.3</td><td>42.7</td><td>48.0</td><td>48.7</td><td>-0.7</td></tr>
<tr><td class="k">07-Aug</td><td>10-20</td><td>107</td><td>41.0</td><td>54.4</td><td>43.5</td><td>43.1</td><td>+0.4</td></tr>
<tr><td class="k">08-Aug</td><td>10-20</td><td>280</td><td>19.0</td><td>27.1</td><td>38.9</td><td>60.0</td><td>-21.1</td></tr>
<tr><td class="k">BASELINE</td><td>10-20</td><td>5603</td><td>21.0</td><td>44.9</td><td>50.3</td><td>50.7</td><td>-0.4</td></tr>
<tr><td class="k">06-Aug</td><td>20-30</td><td>274</td><td>29.5</td><td>67.9</td><td>53.0</td><td>50.6</td><td>+2.4</td></tr>
<tr><td class="k">07-Aug</td><td>20-30</td><td>273</td><td>43.2</td><td>67.9</td><td>44.2</td><td>53.8</td><td>-9.7</td></tr>
<tr><td class="k">08-Aug</td><td>20-30</td><td>35</td><td>18.6</td><td>23.7</td><td>40.0</td><td>71.8</td><td>-31.9</td></tr>
<tr><td class="k">BASELINE</td><td>20-30</td><td>3513</td><td>37.4</td><td>81.3</td><td>56.8</td><td>56.0</td><td>+0.8</td></tr>
<tr><td class="k">06-Aug</td><td>30-40</td><td>266</td><td>26.9</td><td>63.5</td><td>69.1</td><td>54.9</td><td>+14.2</td></tr>
<tr><td class="k">07-Aug</td><td>30-40</td><td>69</td><td>65.7</td><td>74.5</td><td>67.5</td><td>61.3</td><td>+6.2</td></tr>
<tr><td class="k">08-Aug</td><td>30-40</td><td>23</td><td>56.2</td><td>61.3</td><td>39.1</td><td>64.8</td><td>-25.7</td></tr>
<tr><td class="k">BASELINE</td><td>30-40</td><td>2415</td><td>58.8</td><td>127.7</td><td>57.0</td><td>56.1</td><td>+0.9</td></tr>
<tr><td class="k">06-Aug</td><td>40-50</td><td>32</td><td>88.4</td><td>93.0</td><td>60.4</td><td>60.5</td><td>-0.1</td></tr>
<tr><td class="k">08-Aug</td><td>40-50</td><td>13</td><td>120.6</td><td>126.7</td><td>39.9</td><td>69.3</td><td>-29.5</td></tr>
<tr><td class="k">BASELINE</td><td>40-50</td><td>2435</td><td>60.1</td><td>154.8</td><td>59.7</td><td>57.5</td><td>+2.2</td></tr>
</table>
<div class="note"><b>Read:</b> at comparable speed (30–40 km/h), 07-Aug median Ip (65.7) exceeds baseline (58.8) while
axle-04 is the hot motor — the anomaly is coupled to higher primary current. On 08-Aug at 40–50 km/h the
small sample shows median Ip 120.6 vs baseline 60.1 (+100%) while TM1_2 stays cold — the remaining 5 motors
drawing extra current. n is small for 08-Aug upper buckets; treat as directional, not conclusive.</div></div>

<div class="section"><h2>TEST C — axle-04 speed vs the other axles (the kinematic test)</h2>
{p5a}
{p5b}
<div class="note"><b>Read (Test C):</b> On 08-Aug pre-failure (top) axle-04 speed tracks axles 1/2/3/5 exactly at every
row — the wheelset was <b>still rotating</b>, NOT yet seized, even though TM1_2 was cold. On 09-Aug (bottom),
the day after the reported 19:26 lock, the axle-04 speed channel reads dead sentinel (3276, dropped from plot)
while the other axles show valid crawl speeds. So the axle-04 speed signal failed <i>after</i> the incident,
not before. No kinematic divergence proves pre-lock binding; the failure moment is inside the 08-Aug
17:25 → 09-Aug 14:25 telemetry gap. (axle-06 channel is dead all days = feed artifact.)</div></div>

<div class="section"><h2>TEST B — primary current residual vs baseline I=f(v,a) model</h2>
{p6}
<div class="note"><b>Read (Test B):</b> I_excess = I_obs − baseline median I at matched (speed, acceleration), built from
27-Jul–03-Aug. 06-Aug (orange) and 07-Aug (red) show <b>positive excess</b> in upper speed bins (07-Aug
+20.4/+8.3/+21.2 A across bins) — the loco demanded more current than its own baseline at comparable
v+a, consistent with increased resistance. 08-Aug (purple) is <b>not</b> elevated vs baseline at matched v+a —
the train ran no harder; instead the load redistributed (Test E). Small n for 08-Aug upper bins.</div></div>

<div class="section"><h2>TEST E — load redistribution: temp response vs primary current</h2>
{p7a}
{p7b}
<div class="note"><b>Read (Test E):</b> On 07-Aug (red) TM1_2 <b>rises with current</b> (60–80 A → 68 °C, 80–120 A → 85 °C)
— the anomalous motor still coupled to traction effort. On 08-Aug (purple) TM1_2 is <b>flat ~38–40 °C at every
current level</b> while the other-5 mean runs 57–72 °C — axle-04 thermally decoupled from current, remaining
motors carrying the train. Baseline (grey): all six track together. This is the strongest evidence of the
hot→cold state transition.</div></div>

<div class="section"><h2>TEST 6 — energy counter change during traction-active running (direction only)</h2>
<table>
<tr><th>day</th><th>running-min</th><th>dCounter</th><th>counter/min</th><th>vs 05/08</th></tr>
<tr><td class="k">05-Aug</td><td>894</td><td>2632</td><td>2.94</td><td>1.0x</td></tr>
<tr><td class="k">06-Aug</td><td>877</td><td>5492</td><td>6.26</td><td>2.1x</td></tr>
<tr><td class="k">07-Aug</td><td>779</td><td>3555</td><td>4.56</td><td>1.55x</td></tr>
<tr><td class="k">08-Aug</td><td>87</td><td>1100</td><td>12.65</td><td>4.3x</td></tr>
</table>
<div class="note"><b>Read:</b> the cumulative energy counter (xenergymwh_ec) changes <b>more rapidly per running-minute</b>
toward the failure (peaking 4.3× the 05-Aug rate on the failure day). Units of the counter are unverified;
quote only the relative change, NOT "kWh/min".</div></div>

<p style="font-size:11px;color:#777">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} — pure-Python SVG, no matplotlib.
Backing script: make_coupled_report.py. Data: telemetry_42728_2026_rds.json.csv</p>
</body></html>"""

with open("coupled_report_42728.html", "w", encoding="utf-8") as fh:
    fh.write(html_doc)
print("written coupled_report_42728.html")
