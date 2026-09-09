"""Build data/manifests/vendor_request_41.csv - vendor telemetry request list.

Every one of the 41 bearing events with its 7-day window [D-7, D+1),
pre-marked with what the legacy audit already proved, so the vendor/
DB team sees exactly which windows to pull and from where.
Status column is updated after the RDSOJson sweep (scripts/batch_...):
  KNOWN_HIT    - legacy ±5d telemetry proven by bearing_failure_events_audit.csv
  KNOWN_GAP    - 30751: telemetry exists but gap swallows the fault window
  UNKNOWN      - legacy ±5d = 0; RDSOJson sweep pending (server saturated 09/09)
  RDSO_HIT/... - filled after Batch 2 RDSO leg runs
"""
import csv
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = ROOT / "data/manifests/bearing_failure_events_audit.csv"
out = ROOT / "data/manifests/vendor_request_41.csv"

HITS = {"30532", "37282"}
rows = list(csv.DictReader(audit.open(encoding="utf-8-sig")))
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["sno", "loco", "fault_date", "failure_id", "defect",
                                      "window_start", "window_end", "status", "action"])
    w.writeheader()
    for i, r in enumerate(rows, 1):
        d = datetime.strptime(r["FailureDate"].strip(), "%d/%m/%Y")
        ws = (d - timedelta(days=7)).strftime("%Y-%m-%d")
        we = (d + timedelta(days=1)).strftime("%Y-%m-%d")
        if r["Loco"] in HITS:
            status, action = "KNOWN_HIT", "extract 7-day window now (Batch 2 --extract)"
        elif r["Loco"] == "30751":
            status, action = "KNOWN_GAP", "post-failure only in legacy; check RDSOJson too"
        else:
            status, action = "UNKNOWN", "RDSOJson sweep pending; else request from vendor"
        w.writerow({"sno": i, "loco": r["Loco"], "fault_date": r["FailureDate"],
                    "failure_id": r["FailureID"], "defect": r["Defect"],
                    "window_start": ws, "window_end": we, "status": status, "action": action})
print(f"wrote {len(rows)} rows -> {out}")
known = sum(1 for r in rows if r["Loco"] in HITS)
print(f"KNOWN_HIT={known} KNOWN_GAP=1 UNKNOWN={len(rows)-known-1}")
