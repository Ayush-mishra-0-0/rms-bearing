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

temp_cols = ["xtempmotor1_1", "xtempmotor2_1", "xtempmotor3_1",
             "xtempmotor1_2", "xtempmotor2_2", "xtempmotor3_2"]
speed_mot = ["xvist_a1_1", "xvist_a2_1", "xvist_a3_1",
             "xvist_a1_2", "xvist_a2_2", "xvist_a3_2"]

# Which motor temp column hits 76 (clip) and when
print("=== Times when any motor temp == 76.0 (clipped) ===")
counts = Counter()
sample = []
for r in rows:
    t = parse(r["devicetime"])
    hot = [c for c in temp_cols if f(r[c]) == 76.0]
    if hot:
        counts.update(hot)
        if len(sample) < 60:
            sample.append((t, hot))
print("Per-column clip counts:")
for c, n in counts.most_common():
    print(f"  {c}: {n}")
print("First 30 clip events:")
for t, hot in sample[:30]:
    print(f"  {t}  {hot}")

# 6553 sentinel - which motor speed col
print("\n=== Sentinel (>=6550) speed values: per column, counts ===")
scounts = Counter()
samp2 = []
for r in rows:
    t = parse(r["devicetime"])
    sent = [c for c in speed_mot if f(r[c]) is not None and f(r[c]) >= 6550]
    if sent:
        scounts.update(sent)
        if len(samp2) < 60:
            samp2.append((t, sent))
for c, n in scounts.most_common():
    print(f"  {c}: {n}")
print("First 30 sentinel events:")
for t, s in samp2[:30]:
    print(f"  {t}  {s}")

# Detail window 12:30-13:00 on 14/10: all 6 motor speeds + temps + loco speed
print("\n=== DETAIL 14/10 12:30-13:00 (every row) ===")
for r in rows:
    t = parse(r["devicetime"])
    if t.day == 14 and t.hour == 12 and t.minute >= 30:
        ms = {c: f(r[c]) for c in speed_mot}
        mt = {c: f(r[c]) for c in temp_cols}
        ls = f(r["xspeedloco"])
        te = f(r["ltedemand"])
        print(f"{t}  spd={round(ls,1) if ls is not None else None} TE={te}  "
              + " ".join(f"{c.split('_')[1]}{c.split('_')[2]}={v if v is None else round(v,1)}"
                         for c, v in ms.items()) + " || "
              + " ".join(f"T{cn[11:]}={v if v is None else round(v,1)}" for cn, v in mt.items()))
