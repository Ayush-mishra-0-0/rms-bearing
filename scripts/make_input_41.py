"""Build data/manifests/input_41_bearing_locos.csv from the bearing audit.

All 41 bearing events (38 LEVEL_1 + 2 REJECT + 1 LEVEL_2) with loco + fault
date, for the 41-loco presence sweep (legacy + RDSOJson) in
scripts/batch_extract_7day_telemetry.py.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = ROOT / "data/manifests/bearing_failure_events_audit.csv"
out = ROOT / "data/manifests/input_41_bearing_locos.csv"

rows = list(csv.DictReader(audit.open(encoding="utf-8-sig")))
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["loco", "fault_date", "failure_id", "defect",
                                      "registry_label", "audit_telemetry_5d"])
    w.writeheader()
    for r in rows:
        w.writerow({"loco": r["Loco"], "fault_date": r["FailureDate"], "failure_id": r["FailureID"],
                    "defect": r["Defect"], "registry_label": r["RegistryLabel"] or r["Classification"],
                    "audit_telemetry_5d": r["TelemetryRows_plus_minus5d"]})
print(f"wrote {len(rows)} rows -> {out}")
