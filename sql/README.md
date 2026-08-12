# SQL / Reproducibility Index

This index maps **every claim** in the audit reports to the exact query or artifact
that reproduces it. If a manager or senior asks "how do you know X?", go to the
query/artifact listed here and run it. All SQL is read-only.

**DB:** `SLAM_RDS_DB_26.04.2024` at `10.77.36.103` (see `.env`). Run in SSMS.
**Authoritative roster note:** `RMSLocoMap` is the fitment roster (~2,387 distinct
locos); the three "master lists" (`rmslocolist` 615 / `LomNumber` 70 /
`Loco_Process_Signals_LocoNumber` 671, union 846) are partial/stale and must not
be used alone for coverage claims.

---

## Audit scripts (`sql/audit/`) — the headline facts

| # | Script | Reproduces | Expected key result |
|---|---|---|---|
| 01 | `01_fleet_coverage.sql` | Master-list counts + union (846); RMSLocoMap total + make distribution | `rmslocolist`=615, `LomNumber`=70, `Loco_Process_Signals_LocoNumber`=671, union=846; RMSLocoMap=2,408 rows/2,387 distinct; LotusWireless 1072, ARC 525, Medha 457, Siemens 348, CRIS 3, Equus 2, LRail 1 |
| 02 | `02_bearing41_membership.sql` | The 41 bearing-event locos: per-loco presence in telemetry / faults / each master list / RMSLocoMap | 6 with telemetry anywhere, 7 with faults, 5 RMSLocoMap-fitted, **35 with zero telemetry**, 34 in no table |
| 03 | `03_global_daily_rows.sql` | Global telemetry outage calendar (daily rows) | **Jul 05–27 2024** outage (0 on 17 & 21 Jul); **Oct 10–17 2024** outage (0 on 11–13 Oct); June-2024 ramp-up; ~3.5–4.5M/day baseline. **Exact zero days: 2024-07-17, 07-21, 10-11, 10-12, 10-13** (2025-01-16 is NOT zero) |
| 04 | `04_per_loco_gap.sql` | Per-loco gaps around incidents (30751, 37361, 30532, 37282, 30514, 32134) | 30751: 0 rows 11–17 Dec 2024 (platform healthy) with faults flowing; 37361: 1 day in 15-Jul→20-Aug; 30532: sparse 01–07 Apr; 30514: none before 2026-03-13; 32134: single 2022 row |
| 05 | `05_rmsloco_map.sql` | RMSLocoMap fitment dates for the fitted bearing-event locos | 30532 ARC 2024-04-01; 30514 Medha 2026-03-13; 30751/37282 LotusWireless 2024-04-30; 37361 ARC 2024-04-15 |
| 06 | `06_30751_faults.sql` | 30751 fault events through the Dec telemetry gap (precursor sequence) | 16-Dec 17:29/17:30 STB1:0009 + FLG1:0094, repeated 20:38/20:39 |
| 07 | `07_fault_codes_top.sql` | Top-25 fault codes across RMS-fitted locos | No bearing-specific code in top ranks (ACP/Train Part 124k, Earth fault control circuit 43k, Power on MCE 23k, Lifesign ACI1 14.5k, ...) |
| 08 | `08_healthy_control_gap.sql` | Healthy loco (39085) telemetry gaps (control) | Same 23-day Jul-2024 gap as 30751 → platform-wide, not failure-linked |

## Extraction / pipeline scripts (`sql/extraction/`, `sql/feature_store/`, `sql/validation/`)

- `extraction/extract_*.sql` — row-level windows for positives and controls (telemetry + faults).
- `feature_store/*.sql` — event windows, rolling statistics, health features, telemetry alignment.
- `validation/validate_*.sql` — sampling rate, timestamp quality, positive/control overlap, missingness.

## Exploration scripts (`sql/exploration/`)

- `00_inventory.sql` — schema of all telemetry/fault tables.
- `01_table_sizes.sql` — row counts (~5.3B telemetry, ~405.6M faults).
- `02_rms_availability_timeline.sql`, `09_fault_timeline.sql`, `05_loco_inventory.sql`, etc.

## Reproducible generators (`src/rms_bearing/`) — data-artifact creators

| Script | Purpose | Artifact |
|---|---|---|
| `check_telemetry_availability.py` | Batch availability report per manifest window (never extracts rows) | `data/manifests/telemetry_health_manifest.csv` (run: `python src/rms_bearing/check_telemetry_availability.py --manifest data/manifests/telemetry_extraction_manifest.csv`) |
| `export_bearing_audit.py` | The **41 bearing events** + telemetry ±5d/±1d counts | `data/manifests/bearing_failure_events_audit.csv` |
| `forensic_audit.py` | Single-loco forensic audit (which table, how many rows, min/max ts, hourly continuity) | console |
| `build_manifest.py` | 408 candidate event windows (positives + controls) | `data/manifests/telemetry_extraction_manifest.csv` |
| `match_fault_timestamps.py` | Fault-time reconciliation candidates | `data/processed/fault_time_reconciliation_candidates.csv` |
| `extract_telemetry.py` | Pulls telemetry windows from the manifest | `data/processed/*.csv` (feature/training inputs) |

## Static source data (frozen, do not edit)

| File | Content |
|---|---|
| `docs/1.1 IR Loco Asset Failure Report(Owner).xlsx` | Owner failure report (135 events) — **source of truth for failures** |
| `data/processed/owner_failure_classification.csv` | Extracted + labelled owner rows (135) |
| `data/processed/ground_truth_failure_registry.csv` | Confirmed registry (68 LEVEL_1/2 events) |
| `data/manifests/bearing_failure_events_audit.csv` | 41 bearing events + telemetry coverage |
| `data/manifests/telemetry_extraction_manifest.csv` | 408 event windows (positives + controls) |

## How to answer the top "challenge" questions

**"How do you know only 3 of 41 bearing events have telemetry near the failure?"**
→ `sql/audit/02_bearing41_membership.sql` (membership anywhere) +
`export_bearing_audit.py` (±5d counts) + `data/manifests/bearing_failure_events_audit.csv`.

**"How do you know there were platform-wide outages?"**
→ `sql/audit/03_global_daily_rows.sql` — global rows collapse to ~0 on 17 & 21 Jul 2024
and 11–13 Oct 2024, while ~3.5–4.5M/day is normal. Same gap seen on healthy loco 39085
(`sql/audit/08_healthy_control_gap.sql`).

**"How do you know 30751's December gap is per-loco, not a date mismatch?"**
→ `sql/audit/04_per_loco_gap.sql` (0 rows 11–17 Dec while global healthy) +
`sql/audit/06_30751_faults.sql` (fault channel kept flowing through the gap) +
`sql/audit/05_rmsloco_map.sql` (owner date aligns with RMS timestamps; no offset).

**"How do you know the failing fleet is mostly not RMS-equipped?"**
→ `sql/audit/01_fleet_coverage.sql` (RMSLocoMap ~2,387 fitted vs 122 failing; only 10
of the 122 are in RMSLocoMap) + `sql/audit/02_bearing41_membership.sql` (35/41 with
zero telemetry anywhere).

**"Which table did you find loco X in?"**
→ `sql/audit/02_bearing41_membership.sql` for the 41 bearing locos, or
`src/rms_bearing/forensic_audit.py --loco <X> --day <failure-day>` for any loco.
