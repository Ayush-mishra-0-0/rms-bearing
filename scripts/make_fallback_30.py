"""Build data/manifests/fallback_30_locos_2024.csv - the 30 fallback locos.

Same 30 as reports/30_bearing_failure_locos_request_v2.xlsx sheet 1:
flagship 42728 (2026) + 29 LEVEL_1 registry events (usable-telemetry first,
then most recent). Consumed by scripts/batch_extract_7day_telemetry.py --fallback30.
"""
import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = ROOT / "data/manifests/bearing_failure_events_audit.csv"
out = ROOT / "data/manifests/fallback_30_locos_2024.csv"

rows = [r for r in csv.DictReader(audit.open(encoding="utf-8-sig")) if r["RegistryLabel"] == "LEVEL_1"]
for r in rows:
    r["_dt"] = datetime.strptime(r["FailureDate"].strip(), "%d/%m/%Y")
has_tel = sorted([r for r in rows if r["TelemetryNearFailure"] == "Y"], key=lambda x: x["_dt"], reverse=True)
no_tel = sorted([r for r in rows if r["TelemetryNearFailure"] != "Y"], key=lambda x: x["_dt"], reverse=True)
selected = [{"loco": "42728", "fault_date": "08/08/2026", "failure_id": "42728-20260808",
             "note": "flagship 2026 SLAM case"}]
for r in (has_tel + no_tel)[:29]:
    selected.append({"loco": r["Loco"], "fault_date": r["FailureDate"], "failure_id": r["FailureID"],
                     "note": "LEVEL_1 registry, telemetry_near=" + r["TelemetryNearFailure"]})
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["loco", "fault_date", "failure_id", "note"])
    w.writeheader(); w.writerows(selected)
print(f"wrote {len(selected)} rows -> {out}")
