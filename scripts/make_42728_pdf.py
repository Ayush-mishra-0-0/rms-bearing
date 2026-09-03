"""Build reports/42728_axle04_lock_report.pdf from case_42728/findings_42728.txt.
Stdlib + reportlab only. No new telemetry claims — reproduces frozen reference + rerun stats.
"""
from __future__ import annotations
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "42728_axle04_lock_report.pdf"

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceAfter=4)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=8.5, leading=11.5)
SMALL = ParagraphStyle("Small", parent=styles["Normal"], fontSize=7.5, leading=10)
CELL = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=7, leading=9)
HCELL = ParagraphStyle("HCell", parent=styles["Normal"], fontSize=7, leading=9, textColor=colors.white)

def P(t): return Paragraph(t, BODY)
def C(t): return Paragraph(str(t), CELL)
def H(t): return Paragraph(str(t), HCELL)

HDR = TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                  ("VALIGN", (0, 0), (-1, -1), "TOP"),
                  ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5fa")])])

def tbl(headers, rows, widths=None):
    t = Table([[H(h) for h in headers]] + [[C(c) for c in r] for r in rows],
              colWidths=widths, repeatRows=1)
    t.setStyle(HDR)
    return t

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.drawString(15 * mm, 12 * mm, "Loco 42728 Axle-04 — telemetry evidence (Equus 27-Jul→10-Aug 2026) — research detection, not a causal finding")
    canvas.drawRightString(A4[0] - 15 * mm, 12 * mm, f"p{doc.page}")
    canvas.restoreState()

story = []
story.append(Paragraph("Loco 42728 (WAG-9HC) — Axle-04 Lock, 08-Aug-2026<br/>Telemetry Evidence Report (Equus feed, 27-Jul → 10-Aug 2026)", H1))
story.append(P("Source: <b>dbo.Lotus_loco_process_signals_RDSOJson</b>, Vendor <b>Equus</b>, LocoId 42728. "
               "Rerun total <b>156,088 rows</b> (orig. 155,095 +993 late 10-Aug rows), 2026-07-27 10:30 → 2026-08-10 11:05. "
               "Reference: <b>case_42728/findings_42728.txt</b> (frozen) + <b>coupled_report_42728.html</b> (8 SVG charts). "
               "Physics-label rule: <b>loss-of-thermal-contribution state</b>; mechanism (cutout vs mechanical) is <b>not separable</b> from captured signals."))
story.append(P("<b>One-line finding:</b> TM1_2 (axle-04 motor) slightly hot 06/08, severe overheat to <b>91.7°C</b> 07/08, "
               "flat-cold on 08/08 while the other 5 motors carried the train at 60–74°C; reported lock <b>08/08 19:26</b> falls "
               "inside the <b>08/08 17:25 → 09/08 14:25 telemetry gap</b>; <b>faultnum=0</b>, zero fault-table rows."))

story.append(Paragraph("1. Official failure timeline (SinglePageFailureReport.xls)", H2))
story.append(tbl(["When", "What"],
    [["08/08 19:11", "arrived SBZ (NKE-CPJ, BSB/NER), WAG-9HC 42728 (BCNE), shed SYHE"],
     ["08/08 19:26", "starter given; LP reports AXLE LOCKED — 2nd bogie, 04 axle; train unable to move"],
     ["08/08 19:32", "starter put back"],
     ["09/08 00:35 / 04:20 / 04:45", "technician arrived / loco detached / handed over"],
     ["Type / last maint.", "ICMS/EPOTH; last minor SCH IA 16/05/2026; report generated 10-08-2026"]],
    [38 * mm, 135 * mm]))

story.append(Paragraph("2. Database reality + critical gap", H2))
story.append(tbl(["Check", "Result"],
    [["Fault tables", "Lotus_LocoFaultData / RDSOJson / Locofault → 0 rows for 42728 (fleet has 712,435 rows 07–10 Aug)"],
     ["faultnum in telemetry", "0 in ALL extracted rows — no fault byte captured around the lock"],
     ["Old feed", "Oct-2025 LotusWireless = commissioning baseline only, NOT evidence for 08/08/2026"],
     ["Gap (critical)", "08/08 ends 17:25:10 → resumes 09/08 14:25:11. 19:26 lock + 00:35–04:45 detach ALL inside gap"],
     ["08/08 coverage", "15:49:10–17:25:10 only (1416 rows); max GPS 40.2 km/h slow freight; 09/08 max 8.5, 10/08 max 8.2"]],
    [38 * mm, 135 * mm]))

story.append(Paragraph("3. Thermal progression — TM1_2 = axle-04 motor (axles 1–3 bogie 1, 4–6 bogie 2)", H2))
story.append(tbl(["Stage", "TM1_2 behaviour"],
    [["06/08 14:00–15:00", "+9 to +10°C above other 5 (mean delta +10.1/+9.3). First abnormal loading, 2 days prior. Also +16.7/+14.3/+9.5 episodes 14:30–15:00"],
     ["07/08 10:13–10:34", "OVERHEAT: 83.5 → crest 91.4–91.7 (10:20–10:27, dT +19.7) → 78.5 by 10:34 → ~71 by 10:38. Only 6-motor anomaly"],
     ["07/08 19:36–19:46", "TRANSITION: first loaded run after overheat — other 5 warm 42→55°C, TM1_2 flat 38.7–38.9°C. Cold state (dT&lt;−10) sustained from ~19:46"],
     ["08/08 15:49–17:25", "FLAT-COLD 36.6–40.2°C while other 5 run 60–74°C (median dT −27.7, min −33.7). Axle-04 already unloaded pre-lock"],
     ["09/08 14:25+", "Crawl ≤8.5 km/h; TM1_2 39–42°C vs others 49–58°C — dragging/binding move post-detach"]],
    [38 * mm, 135 * mm]))
story.append(Spacer(1, 2 * mm))
story.append(tbl(["Hour", "dT", "Hour", "dT", "Hour", "dT"],
    [["06/13 +4.7", "06/14 +10.1", "06/15 +9.3", "07/07 +0.5", "07/08 +0.1", "07/09 +1.2"],
     ["07/10 +9.5 (event hr)", "07/20 −13.7", "08/16 −21.9", "08/17 −29.6 (pre-fail)", "09/15 −9.5", "09/18 −18.1"]],
    [29 * mm] * 6))

story.append(Paragraph("4. Matched-condition tests (do NOT claim bearing cause from temperature alone)", H2))
story.append(tbl(["Test", "Method → result"],
    [["C — axle speed (top priority)", "xvist_a1_2 = axle-04. 08/08 pre-gap tracks axles 1/2/3/5 EXACTLY (still rotating, not seized). 09/08 = 3276 dead sentinel all 2392 rows (signal died post-incident). Axle-06 xvist_a3_2 = 3276 all days = artifact"],
     ["B — current residual vs own f(v,a) baseline (27Jul–03Aug, lte=1)", "Median I_excess: 06-Aug high bins UP (+41.1 @v40–50); 07-Aug UP across bins (+20.4/+8.3/+21.2); 08-Aug NOT elevated (−13.6/−21.7/−17.6) → load redistributed, not harder running. Small-n bins caveat"],
     ["E — load redistribution (speed&gt;20, lte=1)", "07/08: TM1_2 RISES with Ip (60–80→68.2°C dT+6.5; 80–120→84.9°C dT+15.9, still coupled). 08/08: FLAT 38–40°C at EVERY Ip bucket, others 57–72°C (dT −19…−32, decoupled). Baseline dT +0.8…+2.5"],
     ["D — current→temp lag 07/08 09:30–11:30", "corr(dT04,Ip): τ=0 +0.667 → τ=+60s +0.853, above dT autocorr 0.849 → current leads temp (directional only; both series smooth)"]],
    [38 * mm, 135 * mm]))
story.append(Spacer(1, 2 * mm))
story.append(P("<b>Residual-distribution rerun (03-Sep-2026, stdlib only, baseline f(v,a) medians 27Jul–03Aug lte=1):</b> r<sub>t</sub>=I<sub>obs</sub>−Î(v,a), traction-active only."))
story.append(tbl(["Period", "n", "med", "p10–p90", "IQR", "P(|r|>30)", "KS_D", "dT"],
    [["BASE 27J–03A", "26340", "+0.0", "−23.4…+39.3", "21.3", "0.205", "—", "+0.7"],
     ["06-Aug", "1751", "+1.2", "−19.2…+30.3", "18.4", "0.140", "0.062", "+0.9"],
     ["07-Aug", "893", "+8.1", "−5.4…+26.6", "22.4", "0.075", "0.277", "+0.5"],
     ["07/08 10–11 (event)", "333", "+22.0", "+4.1…+27.6", "5.9", "0.075", "0.563", "+15.5"],
     ["07/08 14–20 (post)", "374", "−0.5", "−11.2…+14.4", "12.2", "0.021", "0.176", "−4.7"],
     ["08/08 15–17 (pre-fail)", "968", "−4.9", "−21.5…+9.8", "20.5", "0.054", "0.203", "−21.8"]],
    [30 * mm, 14 * mm, 14 * mm, 28 * mm, 14 * mm, 20 * mm, 14 * mm, 14 * mm]))
story.append(P("Reading: shift is brief/localized to 07/08 10–11h with matching thermal +15.5°C, resets post-event, cold pre-fail −21.8°C. Supports coupled-change claims, not mechanism/generality."))

story.append(Paragraph("5. Coupled signals 07–08 Aug (traction-active medians; bg2tm* ≈1713 V = shared DC-link, NOT per-axle)", H2))
story.append(tbl(["Slice", "n", "Ip med (p90)", "TM1_2", "other5", "dT"],
    [["07/08 30–40 km/h", "69", "65.7 (74.5)", "67.5", "61.3", "+6.2 (hot+coupled)"],
     ["BASE 30–40", "2415", "58.8 (127.7)", "57.0", "56.1", "+0.9"],
     ["08/08 40–50", "13", "120.6 (126.7)", "39.9", "69.3", "−29.5 (cold, 5 carry; small-n)"],
     ["BASE 40–50", "2435", "60.1 (154.8)", "59.7", "57.5", "+2.2"],
     ["07/08 10–11 event hr", "—", "61.0 (70.3)", "66.9", "61.0", "+5.9"],
     ["08/08 15–17 pre-fail", "—", "23.2 (58.3)", "39.1", "64.8", "−25.7"]],
    [32 * mm, 14 * mm, 28 * mm, 22 * mm, 22 * mm, 55 * mm]))
story.append(P("07/08 10:01–10:34 aligned: 12–57 km/h, Ip 42–92 A, TM1_2 63→86→91.7°C; peak 10:27 with speed sag to ~40 km/h, Ip ~10 A; 10:34 stopped (v=0, DC-link ~1520 V). "
               "08/08 15:49–17:25: TM1_2 flat 36.6→40.2 whole session; others 38→74; accel to 60–73 km/h, Ip 130–144 A peak. Energy counter rate climbs directionally "
               "(05/08 1.0× → 06/08 2.1× → 07/08 1.55× → 08/08 4.3× on 87 running-min; cumulative counter, units unverified — no 12665 kWh/min quote)."))

story.append(Paragraph("6. Task-7 reconstruction 07/08 19:15→19:50 (462 rows, 1-s; faultnum=0, all cutout bits 0)", H2))
story.append(tbl(["Segment", "TM1_2", "other5", "dT", "Ip", "v"],
    [["Before 19:36 (idle)", "39.1", "38.8", "+0.3", "9.8", "0"],
     ["19:36–19:46 (loaded)", "38.9", "44.9", "−6.1", "20.4", "27.6"],
     ["After 19:46", "38.7", "55.1", "−16.5", "9.6", "29.3"]],
    [38 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm, 47 * mm]))
story.append(P("19:15–19:35 idle (all six drift 39.4→39.0; 15-s shunt 19:27:42–55, all axles together). 19:36:42 first loaded run (xang→50, Ip→81 A): "
               "others 42.8→47.1, TM1_2 flat. 19:40:45→19:46:09 ~5.4-min gap (others 47→55 inside gap). 19:46:32–52 brake demand. Axle-04 rotates at train speed throughout. "
               "H-A sensor fault NOT supported (tracks ambient at idle, read 91.7 that morning, smooth ~38.8 under load — live unloaded channel, unlike 3276/76.0 stuck artifacts). "
               "H-B cutout consistent but no bit evidence (feed exposes no per-motor bit). H-C friction fits morning overheat + residual. "
               "“19:46 dT&lt;−10” is others reaching ~55°C, not a second axle-04 event — decoupling present from 19:36."))

story.append(Paragraph("7. What we can / cannot claim + artifacts", H2))
story.append(tbl(["#", "Claim", "Verdict"],
    [["1", "Thermal precursor (06 +9–10, 07 91.7 dT+19.7, 08 dT−27.7 cold)", "YES"],
     ["2", "Electrical/thermal coupling change (E: follows 07/08, flat 08/08)", "YES"],
     ["3", "Aggregate electrical abnormality (B: elevated 06+07 at matched v,a)", "YES"],
     ["4", "Early-warning potential (~1 day; transition 07/08 19:36–19:46)", "YES"],
     ["5", "Causal mechanism (cutout vs mechanical)", "NO — bits never changed; failure in gap"],
     ["6", "Bearing-specific signature (BPFO/BPFI)", "NO — no kHz waveform"],
     ["7", "General predictive capability", "NO — n=1; needs other cases + healthy controls"]],
    [10 * mm, 120 * mm, 43 * mm]))
story.append(P("Exclusions: xvist_a3_2 = 3276 all days; xtempmotor3_2 = 76.0°C clip ~100% (both axle-06 artifacts, excluded from means); "
               "bg1tm*/bg2tm*/bur* only from 05-Aug; Oct-2025 = baseline only. Negative results retained: bbur/bstb = 0 on 08/08 run; "
               "aggregate current not monotonic; per-axle current not recorded — inference rests on per-axle temp + aggregate current/speed/energy."))

story.append(Paragraph("8. Conclusion & next step", H2))
story.append(P("42728 shows a measurable pre-lock thermal + aggregate-electrical behavioural change with TM1_2 decoupling ~1 day before the reported lock — "
               "an <b>electrical/thermal precursor hypothesis</b>, not a bearing diagnosis. Chain (Shang as principle, not algorithm): expected electrical behaviour → residual → "
               "thermal response → cross-motor deviation. Next: run this exact TM-abnormality → excursion → load-response pattern on the other 2025 axle-lock cases and healthy controls. "
               "Case analysis DONE; predictive conclusion OPEN (closeout 03-Sep-2026)."))
story.append(P("Sources: SinglePageFailureReport.xls; telemetry_42728_2026_rds.json.csv (Equus); scripts verify_axle4/timeline_check/analyze_2026_*/test_B_plus/test_E/test_F_transition/coupled_analysis/make_coupled_report/task7_window/task7_report/extract_42728_full+resume/residual_distribution_42728.py; "
               "charts: coupled_report_42728.html."))

doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=16 * mm,
                        title="42728 Axle-04 — Telemetry Evidence Report", author="rms-bearing")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"Wrote {OUT}")
