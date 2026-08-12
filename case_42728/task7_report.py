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

def other5_median(r):
    vals = [f(r[c]) for c in tcols]
    ok = sorted(v for v in (vals[:3]+vals[4:]) if v is not None and v < 75.99)
    if not ok:
        return None
    n = len(ok)
    return ok[n//2] if n % 2 else (ok[n//2-1]+ok[n//2])/2

recs = []
with open(path, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        t = parse(r["devicetime"])
        if not t or t.month != 8 or t.day != 7:
            continue
        sec = t.hour*3600 + t.minute*60 + t.second
        if 19*3600 + 10*60 <= sec <= 19*3600 + 50*60:
            recs.append((t, r))
recs.sort(key=lambda x: x[0])

# per-row values
data = []
for t, r in recs:
    data.append({
        "t": t,
        "tm12": f(r["xtempmotor1_2"]),
        "o5": other5_median(r),
        "tm11": f(r["xtempmotor1_1"]), "tm21": f(r["xtempmotor2_1"]), "tm31": f(r["xtempmotor3_1"]),
        "tm22": f(r["xtempmotor2_2"]), "tm32": f(r["xtempmotor3_2"]),
        "ip": f(r["xiprim_1"]), "v": f(r["xspeedloco"]), "xang": f(r["xangtrans"]),
        "lte": f(r["ltedemand"]), "lbe": f(r["lbedemand"]),
        "a1": f(r["xvist_a1_1"]), "a2": f(r["xvist_a2_1"]), "a3": f(r["xvist_a3_1"]),
        "a04": f(r["xvist_a1_2"]), "a5": f(r["xvist_a2_2"]),
        "mvcb": f(r["mvcb_on"]), "fault": f(r["faultnum"]),
    })

# ---------------- 6-panel SVG
W, H = 1150, 720
PL, PR, PT, PB = 55, 12, 24, 26
PANEL_H = (H - PT - PB) / 6
t0 = datetime(2026, 8, 7, 19, 10)
t1 = datetime(2026, 8, 7, 19, 50)
xmin, xmax = 0, 2280  # seconds from t0

def X(sec): return PL + sec / (xmax - xmin) * (W - PL - PR)

MARK1 = (19*60+36 - 10*60)  # 19:36 -> 576s? use (19*60+36) - (19*60+10) = 26*60? no: 19:36:00 = 19*3600+36*60; minus t0 (19:10) = 26*60=1560? t0=19:10 => (19*60+36)-(19*60+10) = 26 min? wait 19:36-19:10=26min=1560s
MARK1 = ((19*3600 + 36*60) - (19*3600 + 10*60))  # 1560 s
MARK2 = ((19*3600 + 46*60) - (19*3600 + 10*60))  # 2160 s

def sec_of(t): return (t.hour*3600 + t.minute*60 + t.second) - (19*3600 + 10*60)

def panel(title, series, ymin, ymax, ylabel, draw_lte=False, xlabels=False):
    """series: list of (name, color, vals)"""
    top = PT + PANEL_H * panelstate["p"]
    panelstate["p"] += 1
    bottom = top + PANEL_H
    s = []
    s.append(f'<rect x="{PL}" y="{top:.1f}" width="{W-PL-PR}" height="{PANEL_H:.1f}" fill="#fbfbfb" stroke="#ddd"/>')
    s.append(f'<text x="{PL}" y="{top+11}" font-size="10.5" font-weight="bold" fill="#111">{html.escape(title)}</text>')
    # markers
    for mx, lbl, col in [(MARK1, "19:36 loaded run", "#2e7d32"), (MARK2, "19:46 (dT<-10)", "#c0392b")]:
        s.append(f'<line x1="{X(mx):.1f}" y1="{top+14}" x2="{X(mx):.1f}" y2="{bottom:.1f}" stroke="{col}" stroke-width="1" stroke-dasharray="4,3"/>')
        s.append(f'<text x="{X(mx)+3}" y="{top+14}" font-size="8.5" fill="{col}">{lbl}</text>')
    # grid
    for i in range(5):
        yy = top + 14 + (PANEL_H - 14) * i / 4
        s.append(f'<line x1="{PL}" y1="{yy:.1f}" x2="{W-PR}" y2="{yy:.1f}" stroke="#eee"/>')
        val = ymax - (ymax - ymin) * i / 4
        s.append(f'<text x="{PL-4}" y="{yy+3:.1f}" font-size="8.5" text-anchor="end" fill="#555">{val:.0f}</text>')
    s.append(f'<text x="{PL-4}" y="{top+ (PANEL_H)/2 +3:.1f}" font-size="9" text-anchor="end" fill="#777">{ylabel}</text>')
    # series
    for name, color, vals in series:
        pts = []
        for d, val in zip(data, vals):
            if val is None:
                continue
            pts.append((X(sec_of(d["t"])), top + 14 + (PANEL_H - 14) * (ymax - val) / (ymax - ymin)))
        if len(pts) > 1:
            dstr = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)
            s.append(f'<path d="{dstr}" fill="none" stroke="{color}" stroke-width="1.3"/>')
    # x labels only on last panel
    if xlabels:
        for m in (15, 20, 25, 30, 35, 40, 45, 50):
            sx = (19*60+m) - 10*60
            s.append(f'<line x1="{X(sx):.1f}" y1="{bottom-14}" x2="{X(sx):.1f}" y2="{bottom:.1f}" stroke="#ccc"/>')
            s.append(f'<text x="{X(sx):.1f}" y="{H-PB+14}" font-size="9" text-anchor="middle" fill="#444">19:{m:02d}</text>')
    return "\n".join(s)

panelstate = {"p": 0}
sections = []

sections.append(panel("P1  TM temperatures: TM1_2 (axle04, red) vs median(other5, blue)  [deg C]",
    [("TM1_2 axle04", "#c0392b", [d["tm12"] for d in data]),
     ("other-5 median", "#2471a3", [d["o5"] for d in data])],
    30, 75, "degC"))

sections.append(panel("P2  All six TM temperatures  [deg C]",
    [("TM1_1", "#7f8c8d", [d["tm11"] for d in data]),
     ("TM2_1", "#95a5a6", [d["tm21"] for d in data]),
     ("TM3_1", "#bdc3c7", [d["tm31"] for d in data]),
     ("TM1_2", "#c0392b", [d["tm12"] for d in data]),
     ("TM2_2", "#27ae60", [d["tm22"] for d in data]),
     ("TM3_2", "#16a085", [d["tm32"] for d in data])],
    30, 75, "degC"))

sections.append(panel("P3  Primary current (xiprim_1)  [A]",
    [("Ip", "#1a7d3c", [d["ip"] for d in data])],
    0, 90, "A"))

sections.append(panel("P4  Loco speed (xspeedloco)  [km/h]",
    [("v", "#2874a6", [d["v"] for d in data])],
    0, 45, "km/h"))

sections.append(panel("P5  Axle speeds: axle04(red) vs axle1/2/3/5(greys)  [km/h]",
    [("axle1", "#bdc3c7", [d["a1"] for d in data]),
     ("axle2", "#95a5a6", [d["a2"] for d in data]),
     ("axle3", "#7f8c8d", [d["a3"] for d in data]),
     ("axle04", "#e74c3c", [d["a04"] for d in data]),
     ("axle5", "#34495e", [d["a5"] for d in data])],
    0, 45, "km/h"))

sections.append(panel("P6  Notch(xangtrans) / LTEdemand / LBEdemand / MBCB / fault",
    [("xang/10", "#8e44ad", [d["xang"]/10 if d["xang"] is not None else None for d in data]),
     ("lte*40", "#16a085", [d["lte"]*40 if d["lte"] is not None else None for d in data]),
     ("lbe*40", "#e67e22", [d["lbe"]*40 if d["lbe"] is not None else None for d in data]),
     ("mvcb*20", "#2c3e50", [d["mvcb"]*20 if d["mvcb"] is not None else None for d in data]),
     ("fault*40", "#c0392b", [d["fault"]*40 if d["fault"] is not None else None for d in data])],
    0, 50, "scaled", xlabels=True))

svg = '\n'.join(sections)

# ---------------- table
def seg(t0s, t1s):
    lo = t0s - (19*3600+10*60); hi = t1s - (19*3600+10*60)
    sel = [d for d in data if lo <= sec_of(d["t"]) <= hi]
    def med(key):
        vals = sorted(v for v in (d[key] for d in sel) if v is not None)
        if not vals: return None
        n = len(vals)
        return (vals[n//2-1]+vals[n//2])/2 if n % 2 == 0 else vals[n//2]
    return sel, med

segs = {
    "Before 19:36": ((19*3600+15*60), (19*3600+35*60)),
    "19:36-19:46":  ((19*3600+36*60), (19*3600+46*60)),
    "After 19:46":  ((19*3600+46*60), (19*3600+50*60)),
}

def val(sel, med, key):
    v = med(key)
    if v is None:
        return "-"
    if key == "lte" or key == "lbe" or key == "mvcb":
        return f"{v:.0f}"
    return f"{v:.1f}"

rows_tbl = []
for nm, (t0s, t1s) in segs.items():
    sel, med = seg(t0s, t1s)
    rows_tbl.append((nm, sel, med))

table_html = ['<table><tr><th>Signal</th>']
for nm, _, _ in rows_tbl:
    table_html.append(f'<th>{nm}</th>')
table_html.append('</tr>')
sigdefs = [
    ("TM1_2 (axle04)", "tm12"),
    ("other-5 median", "o5"),
    ("dT (TM1_2-other5)", None),
    ("Primary current (A)", "ip"),
    ("Speed (km/h)", "v"),
    ("axle04 speed (km/h)", "a04"),
    ("Notch xangtrans", "xang"),
    ("LTEDemand", "lte"),
    ("LBEdemand", "lbe"),
    ("MVBC on", "mvcb"),
    ("faultnum", "fault"),
]
for lbl, key in sigdefs:
    table_html.append(f'<tr><td class="k">{lbl}</td>')
    for nm, sel, med in rows_tbl:
        if key is None:
            vals = sorted(v for v in ((d["tm12"]-d["o5"]) for d in sel) if v is not None)
            v = (vals[len(vals)//2] if vals else None)
            table_html.append(f'<td>{v if v is None else f"{v:+.1f}"}</td>')
        else:
            table_html.append(f'<td>{val(sel, med, key)}</td>')
    table_html.append('</tr>')
table_html.append('</table>')

# status column summary
status_note = """
<b>Status / control bits across the whole window (07/08 19:10-19:50):</b>
bbur1/2/3_off = 0, bstb1/2_off = 0, bflg1/2_off = 0, bslg1/2_off = 0,
bhbb1/2_off = 0, bbda1/2_off = 0 (all <b>0 = no isolation/cutout</b>),
mtrcctract1/2 = 0, mvcb_on = 1, faultnum = 0 throughout.
Only LTEDemand / LBEdemand / xangtrans (notch) change.

<b>KEY EVENT RECONSTRUCTION:</b>
<ul>
<li><b>19:15-19:35</b>: idle. v=0, all axle speeds 0, lte=0, xang=0,
    Ip~8-10 A (aux). TM1_2=39.4, other5=39.0 - all six drifting down together.
    19:27:42-19:27:55: brief 15-s shunt 0->2.5 km/h, ALL axles turn together
    (a1=a04=a5=1-2), no divergence. Stops 19:27:59.</li>
<li><b>19:36:42</b> FIRST LOADED RUN: v 14->33.6 km/h, xang rises to 50
    (full notch), Ip up to 81 A. <b>TM1_2 stays FLAT 38.8-39.0</b> while
    other5 rises 42.8->47.1. All axle speeds identical (no axle04 divergence).</li>
<li><b>19:38:12-19:39:27</b>: coast (xang=0, lte=0, Ip 7-10). other5 keeps
    climbing 44->46 (thermal inertia), TM1_2 flat.</li>
<li><b>19:39:29-19:40:45</b>: second throttle app (xang~26-36, Ip 8->45 A).
    other5 45.9->47.1, TM1_2 flat 38.7-38.9.</li>
<li><b>19:40:45 -> 19:46:09  TELEMETRY GAP (~5.4 min missing)</b>. At resume:
    v=36.1, lte=0, Ip=10.3 (coasting), TM1_2=38.7, <b>other5=54.6</b>.
    The other5 jump 47->55 happened INSIDE the gap (more loaded running).</li>
<li><b>19:46:09-19:46:55</b>: decel, lbe=1 (brake demand) 19:46:32-19:46:52.
    TM1_2 flat 38.7-38.8, other5 54.6->55.2.</li>
<li><b>19:46:55+</b>: v 28->23 km/h still decelerating; TM1_2 38.7, other5 55.4.
    bur3 (DC-link current conv3) oscillating 1-73 during decel (regenerative/
    dynamic behavior).</li>
</ul>

<b>INTERPRETATION vs the three hypotheses:</b>
<ul>
<li><b>H-A (sensor fault): NOT supported.</b> TM1_2 tracked ambient exactly
    during idle (39.4->38.7 in phase with other5 39.0->38.6), then held a
    flat ~38.8 through full-notch loaded runs - a live sensor reading a
    thermally unloaded motor, not a stuck/dead channel (compare axle-06
    speed=3276 or xtempmotor3_2 stuck at 76.0 for true dead channels).
    Also the same channel read 91.7 C that morning.</li>
<li><b>H-B (electrical/control isolation): no bit evidence, but consistent.</b>
    No isolation/cutout bit toggles in this feed, yet TM1_2's flatness under
    full-notch load + other-5 carrying the train is exactly what a
    motor-cut-out / no-contribution state looks like. The feed exposes no
    per-motor cutout bit, so absence of telemetry is NOT proof either way.</li>
<li><b>H-C (mechanical): the morning overheat (91.7 C) + current-positive
    residual fits rising friction; the flat-TM + normal-aggregate-current +
    still-rotating-axle fits a motor that has stopped contributing load.</li>
</ul>
<b>CONCLUSION (what changed at 19:36 / 19:46):</b> TM1_2 was ALREADY
thermally decoupled at the FIRST loaded run of this window (19:36) - it
never heated under load while the other five did. The "19:46 transition"
is a dT<-10 threshold crossing driven by the OTHER motors' temperature
reaching ~55 C (partly inside the 19:40-19:46 data gap), NOT a separate
axle-04 event. No status/control/fault bit changed in the window; axle-04
kept rotating at train speed throughout. The cleanest statement: after the
07/08 morning overheat, axle-04's motor stopped responding thermally to
traction load - a loss-of-thermal-contribution state, whose mechanism
(electrical cutout vs mechanical) cannot be separated with the signals
captured here.
"""

html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>TASK 7 - 07/08 19:15-19:50 transition</title>
<style>body{{font-family:Consolas,monospace;background:#fafafa;margin:20px;color:#222}}
h1{{font-size:17px}}h2{{font-size:14px;border-bottom:1px solid #ccc;padding-bottom:4px}}
.section{{background:#fff;border:1px solid #ddd;padding:14px;margin-bottom:16px;border-radius:6px}}
table{{border-collapse:collapse;font-size:12px}}td,th{{border:1px solid #ccc;padding:3px 8px;text-align:right}}
th{{background:#eef}} .k{{text-align:left}}
.note{{background:#f0f7ff;border:1px solid #bcd9f0;padding:12px;border-radius:6px;font-size:12px}}</style></head><body>
<h1>TASK 7 - 07/08 19:15 -> 19:50 state transition (event reconstruction)</h1>
<p>Ground truth 08/08 19:26 axle-04 lock. This window: 07/08 19:10-19:50. 462 rows (1 s).</p>
<div class="section"><h2>Aligned 6-panel plot (markers: green=19:36 first loaded run, red=19:46 dT&lt;-10)</h2>
<svg xmlns="http://www.w3.org/2000/svg" width="1150" height="720" viewBox="0 0 1150 720">
{svg}
</svg></div>
<div class="section"><h2>Before / During / After table (medians over each segment)</h2>
{''.join(table_html)}
</div>
<div class="section"><h2>Interpretation</h2>
<div class="note">{status_note}</div></div>
</body></html>"""

task7_section = f"""
<div style="page-break-before:always"></div>
<h1 style="font-size:17px;margin-top:30px">TASK 7 - 07/08 19:15 -> 19:50 state transition (event reconstruction)</h1>
<p>Ground truth 08/08 19:26 axle-04 lock. This window: 07/08 19:10-19:50. 462 rows (1 s).</p>
<div class="section"><h2>Aligned 6-panel plot (markers: green=19:36 first loaded run, red=19:46 dT&lt;-10)</h2>
<svg xmlns="http://www.w3.org/2000/svg" width="1150" height="720" viewBox="0 0 1150 720">
{svg}
</svg></div>
<div class="section"><h2>Before / During / After table (medians over each segment)</h2>
{''.join(table_html)}
</div>
<div class="section"><h2>Interpretation</h2>
<div class="note">{status_note}</div></div>
"""

target = "coupled_report_42728.html"
html_doc = open(target, encoding="utf-8").read()
html_doc = html_doc.rstrip()
assert html_doc.endswith("</html>"), "target must end with </html>"
html_doc = html_doc[:-len("</html>")] + task7_section + "\n</html>"
with open(target, "w", encoding="utf-8") as fh:
    fh.write(html_doc)
print("TASK 7 section injected into", target)
