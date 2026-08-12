"""Build deterministic multi-horizon telemetry extraction manifests from ground truth."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path

HORIZONS = (
    ("7d", 7 * 24, "Long-term degradation"),
    ("3d", 3 * 24, "Medium-term degradation"),
    ("24h", 24, "Short-term warning"),
    ("12h", 12, "Operational alert horizon"),
    ("6h", 6, "Immediate warning"),
    ("1h", 1, "Near-failure behaviour"),
)


def parse_failure_date(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%d/%m/%Y")


def load_overrides(path: Path | None) -> dict[str, datetime]:
    if not path or not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as file:
        return {
            row["FailureID"]: datetime.fromisoformat(row["FailureTimestamp"])
            for row in csv.DictReader(file)
            if row.get("FailureTimestamp")
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=Path("data/processed/ground_truth_failure_registry.csv"))
    parser.add_argument("--overrides", type=Path, default=Path("data/processed/failure_timestamp_overrides.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/manifests/telemetry_extraction_manifest.csv"))
    args = parser.parse_args()
    overrides = load_overrides(args.overrides)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.registry.open(newline="", encoding="utf-8-sig") as source, args.output.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=["FailureID", "Loco", "FailureDate", "FailureTimestamp", "TimestampPrecision", "Label", "Confidence", "Window", "HorizonHours", "WindowStart", "WindowEnd", "Purpose"])
        writer.writeheader()
        for event in csv.DictReader(source):
            timestamp = overrides.get(event["FailureID"], parse_failure_date(event["Date"]))
            precision = "EXACT" if event["FailureID"] in overrides else "DATE_ONLY_ASSUMED_MIDNIGHT"
            for window, hours, purpose in HORIZONS:
                writer.writerow({"FailureID": event["FailureID"], "Loco": event["Loco"], "FailureDate": event["Date"], "FailureTimestamp": timestamp.isoformat(sep=" "), "TimestampPrecision": precision, "Label": event["Label"], "Confidence": event["Confidence"], "Window": window, "HorizonHours": hours, "WindowStart": (timestamp - timedelta(hours=hours)).isoformat(sep=" "), "WindowEnd": timestamp.isoformat(sep=" "), "Purpose": purpose})


if __name__ == "__main__":
    main()
