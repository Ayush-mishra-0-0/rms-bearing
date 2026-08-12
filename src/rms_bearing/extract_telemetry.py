"""Extract an approved manifest window; DATE_ONLY windows require explicit opt-in."""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/telemetry_extraction_manifest.csv"))
    parser.add_argument("--failure-id", required=True)
    parser.add_argument("--window", required=True, choices=["7d", "3d", "24h", "12h", "6h", "1h"])
    parser.add_argument("--table", default="dbo.Lotus_loco_process_signals")
    parser.add_argument("--allow-date-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.manifest.open(newline="", encoding="utf-8-sig") as file:
        event = next((r for r in csv.DictReader(file) if r["FailureID"] == args.failure_id and r["Window"] == args.window), None)
    if not event:
        raise SystemExit("Event/window not found in manifest.")
    if event["TimestampPrecision"] != "EXACT" and not args.allow_date_only:
        raise SystemExit("Blocked: supply an exact incident time in failure_timestamp_overrides.csv, or explicitly use --allow-date-only.")
    import pyodbc  # Installed only where database extraction is authorised.
    connection = pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.environ['DB_SERVER']};DATABASE={os.environ['DB_NAME']};UID={os.environ['DB_USERNAME']};PWD={os.environ['DB_PASSWORD']};TrustServerCertificate=yes;")
    query = f"SELECT * FROM {args.table} WHERE CAST(locoid AS varchar(30))=? AND devicetime>=? AND devicetime<? ORDER BY devicetime"
    cursor = connection.cursor(); cursor.execute(query, event["Loco"], event["WindowStart"], event["WindowEnd"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out); writer.writerow([c[0] for c in cursor.description]); writer.writerows(cursor)
    connection.close()


if __name__ == "__main__":
    main()
