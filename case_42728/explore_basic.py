import csv
from datetime import datetime, timedelta

path = "telemetry_42728_raw.csv"

rows = []
with open(path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

print("Rows:", len(rows))

def parse(s):
    return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")

ts = [parse(r["devicetime"]) for r in rows]
ts.sort()

print("Time range:", ts[0], "->", ts[-1])
print()

# daily counts
from collections import Counter
daily = Counter(t.date() for t in ts)
print("=== Rows per day ===")
for d, n in sorted(daily.items()):
    print(f"  {d}  {n}")
print()

# gaps
gaps = [ts[i] - ts[i-1] for i in range(1, len(ts))]
big = [(ts[i], gaps[i-1]) for i in range(1, len(ts)) if gaps[i-1].total_seconds() > 300]
print("=== Gaps > 300s (start_ts, gap_min) ===")
for start, g in big:
    print(f"  {start}  gap {g.total_seconds()/60:.1f} min")
print("Total big gaps:", len(big))
