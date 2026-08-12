# RMS Bearing Early-Warning Project — Comprehensive Progress & Audit Report

**Date:** 31-Jul-2026
**Project:** Predictive detection of traction-motor bearing (axle-lock) failures in Indian Railways locomotives by fusing RMS continuous telemetry with SLAM/Owner failure reports
**Author:** Ayush Mishra

---

## 0. Purpose of this document

This report records, factually, everything that has been done to date on the project: the data sources, every investigation performed, every finding (with numbers), the bugs found and fixed, and the decisions taken based on evidence. It is intended for the reporting manager.

---

## 1. Project objective

Predict axle-bearing (traction-motor) failures in locomotives **before they happen**, by combining:

1. **RMS continuous telemetry** — per-second sensor data (169+ parameters) streamed from RMS-equipped locomotives (vendor: LotusWireless/ARC/Medha).
2. **SLAM / Owner Failure reports** — the official failure register ("1.1 IR Loco Asset Failure Report (Owner)") recording confirmed traction-motor failures.

The original plan (`plan.md`) proposed a Bronze→Silver→Gold→ML pipeline culminating in an XGBoost classifier and an LSTM-autoencoder health index.

---

## 2. Environment & access

| Item | Detail |
|---|---|
| DB server | `10.77.36.103` |
| DB name | `SLAM_RDS_DB_26.04.2024` (RMS + SLAM data) |
| Access | pyodbc 5.3.0, ODBC Driver 17 for SQL Server |
| Credentials | `.env` (DB_SERVER / DB_NAME / DB_USERNAME / DB_PASSWORD) |
| OS | Windows 11, PowerShell 5.1 |
| Working copy | `C:\Users\CRIS\Desktop\ayush\rms-bearing` |

**Operational note:** Long PowerShell `python -c "..."` strings break on quote nesting — all database work is done via standalone `.py` scripts under `src/rms_bearing/`.

---

## 3. Data sources

| Source | File / table | Contents | Size |
|---|---|---|---|
| Owner Failure Report | `docs/1.1 IR Loco Asset Failure Report(Owner).xlsx` | 135 events, 122 distinct locos, all "Traction Motor G9P7", dates 2024 (133) + 2026 (2) | 137 rows × 32 cols |
| Ground truth registry | `data/processed/ground_truth_failure_registry.csv` | 68 high-confidence events (50 LEVEL_1 + 18 LEVEL_2), all 2024 | 68 rows |
| Owner classification | `data/processed/owner_failure_classification.csv` | 135 events with REJECT/LEVEL_1/LEVEL_2 labels + confidence + reasoning | 135 rows |
| RMS signal dictionary | `docs/RMS data.xlsx` | Column ↔ parameter mapping (locoid, latitude, longitude, altitude, ...) | 169 params |
| Fault severity | `docs/RMS fault severity.xlsx` | 196 fault-text ↔ severity categories | 196 rows |
| RMS telemetry (DB) | `Lotus_loco_process_signals` | Continuous per-second process signals | **~5.31 B rows** |
| RMS faults (DB) | `Lotus_LocoFaultData` | Discrete fault events (FaultText, faulttime, lat/long, vendor) | **~405.6 M rows** |
| RMS loco lists (DB) | `rmslocolist` (615), `LomNumber` (70), `Loco_Process_Signals_LocoNumber` (671) | RMS-equipped loco registers | union **846** |
| Loco asset master (DB) | `LocoMaster` | Static asset data (wheel dia, dates, type) | 19,423 rows |
| Stubs (DB) | `Locofault`, `WheelData`, `LocoStatus`, `RMSAlerts`, `RMSGlobalAnalogEventData`, `RMSProcessEventData` | Lookup / stub tables | 0–5,161 rows |

---

## 4. Pipeline built to date

```
Owner Failure Excel ──► ground_truth_failure_registry.csv   (authoritative events)
                            │
                            ▼
              build_manifest.py ──► telemetry_extraction_manifest.csv
              (6 horizons: 7d / 3d / 24h / 12h / 6h / 1h per event; 408 rows)
                            │
                            ▼
              match_fault_timestamps.py ──► fault_time_reconciliation_candidates.csv
              (RMS fault-table timestamps near each event, for review)
                            │
                            ▼
              check_telemetry_availability.py ──► telemetry_health_manifest.csv
              (availability-only health report per table/window; never extracts rows)
                            │
                            ▼
              extract_telemetry.py ──► approved per-window CSV extraction
              (blocked unless timestamp is EXACT or operator opts into DATE_ONLY)
```

**Key design decision** (from `README.md`): an event with a date but no verified incident time is marked `DATE_ONLY_ASSUMED_MIDNIGHT`; extraction is blocked unless an exact timestamp override is supplied.

---

## 5. The forensic audit of Loco 30751 (advisory task #1)

The audit focused on the reference case: Loco **30751**, FailureID **4649392**, TM bearing seized, owner report date **17/12/2024**, with fault events on 16/12/2024. Tool: `src/rms_bearing/forensic_audit.py`.

### 5.1 Findings

- Telemetry exists for 30751: **13,623,099 rows**, vendor **LotusWireless**.
- **Telemetry gap: `2024-12-10 06:03:10` → `2024-12-18 17:05:23`. Zero rows 11–17 Dec 2024.** The incident day (16 Dec) falls inside the gap.
- The gap is **per-loco, not platform-wide**: globally the platform was healthy on 16 Dec 2024 (**3,902,008 rows, 121 distinct locos**).
- **Fault events continued through the gap** (328 events 11–16 Dec; daily counts 132, 28, 57, 45, 41, 25; 0 on 17 Dec; 36 on 18 Dec) — the loco was running, but its process-signal stream was silent.
- No `30751*` spelling appears in ANY table during 15–16 Dec (checked all candidate tables).
- **Fault precursor sequence on 16 Dec 2024** in `Lotus_LocoFaultData` (matches the reference sequence):
  - 02:19:58 FLG1:0092 Alarm chain pulling
  - 09:32:29 FLG1:0037 S/R interlock
  - 16:08:43 FLG1:0117 Power off of MCE
  - 17:29:48 STB1:0009 Rotary switch bogie 1 cut out
  - 17:30:19 FLG1:0094 SS02 traction bogie 1 off
  - 20:38:59 / 20:39:02 (sequence repeated)
- 30751's `MIN(devicetime)` = **1910-06-16** — dirty/out-of-range timestamps exist in the tables.

### 5.2 Interpretation

30751 **cannot** be the golden end-to-end example for telemetry-based prediction, because its pre-failure telemetry window is swallowed by the gap. Its fault sequence remains valuable for **validating fault-matching logic**, not for telemetry modeling.

---

## 6. Fleet-wide telemetry coverage audit (advisory task #2)

### 6.1 The core finding: fleet mismatch

- The **Owner Failure dataset spans the entire fleet** (122 distinct locos failed).
- **RMS telemetry covers only a subset** of locos (846 RMS-master-listed).
- **Only 6 of the 122 failing locos are RMS-fitted** (30346, 30751, 37282, 37361, 39117, 44092).
- The other ~116 failing locos **have no telemetry by design** — they are not RMS-equipped. **This is a fleet-coverage fact, not an algorithm failure.**

Cross-reference:

| Dataset | Events | Distinct locos | Locos also RMS-listed |
|---|---|---|---|
| Full owner classification | 135 | 122 | **6** |
| Ground-truth registry (LEVEL_1/2) | 68 | 66 | **4** |

### 6.2 Bearing-event positive pool (the "41")

From the raw Excel `Failure/Defect` column, **41 events are bearing-related** (TM bearing seized, DE bearing seize, outer labyrinth displaced/rubbing, rotor labyrinth). These are the true axle-lock candidates.

**Of 41 bearing events, only 3 have ANY telemetry within ±5 days:**

| Loco | Failure date | Defect | Telemetry ±5d | Telemetry ±1d | Pre-failure window usable? |
|---|---|---|---|---|---|
| 37282 | 10/12/2024 | TM bearing seized | 359,439 | 130,047 | **YES — dense** (21k–72k rows/day) |
| 30532 | 04/04/2024 | DE bearing seize | 8,076 | 3,908 | **YES — sparse** (317–2,901 rows/day) |
| 30751 | 17/12/2024 | TM bearing seized | 52,546 | 4,395 | **NO — gap swallows pre-failure window** |

All other 38 bearing events have **zero telemetry within ±5 days**.

### 6.3 Telemetry gaps around incidents (per-loco outages)

- **30751**: gap 11–17 Dec 2024 (platform healthy). Unusable.
- **37361** (03/08/2024): telemetry exists overall (Apr 2024–May 2026) but **only 1 day (23-Jul-2024) in the whole 15-Jul→20-Aug window** → also unusable.
- **30514** (04/07/2024): telemetry begins 2026-03-13 (Medha fitted later) → none at failure time.
- **32134** (25/05/2024): telemetry is a single row on 2022-01-15 → none at failure time.

### 6.4 Answer to "is there enough data to train a supervised model?"

**No.** Confirmed positives with usable pre-failure telemetry = **2** (37282 dense, 30532 sparse). Supervised classification is not viable on 2–3 positive windows.

---

## 7. Date-mismatch hypothesis — tested and answered

**Question raised:** the gap might be due to a date mismatch — e.g., the failure website's date differs from the RMS table's date.

**Answer: NO — the mismatch is not a date problem.** Evidence:

1. **Telemetry table itself is authoritative.** For each bearing event we queried `Lotus_loco_process_signals` for rows in `[failure_date − 5d, +5d]`. For 38 of 41 events the count is **zero** — the loco simply has no telemetry anywhere near those dates (not RMS-equipped).
2. **For the 3 that do have telemetry**, the owner-report date and RMS timestamps align (e.g., 37282: dense telemetry through 10/12; owner date 10/12). No offset is needed.
3. **The one genuine timing nuance**: the owner report date is the *reporting* date, which can differ by ~1 day from the actual mechanical event (30751 reported 17/12; precursor faults on 16/12). But this does **not** explain the telemetry absence — the gap spans a full week regardless of the exact incident day.
4. **RMSLocoMap entry dates confirm RMS fitment timing**, not date mismatch: e.g., 30514 (Medha) entered 2026-03-13 — after its 2024 failure, so no telemetry existed yet.

**Conclusion:** the "gaps" are explained by (a) most failing locos being non-RMS, and (b) genuine per-loco telemetry outages on the few that are RMS-equipped — not by a date mismatch between systems.

---



## 9. Fault table (Lotus_LocoFaultData) — validation only

The fault table is **not** a reliable timestamp anchor on its own:

- **37282**: fault events have **garbage timestamps spanning 1901–2037**; no valid events near its 10/12/2024 incident.
- **39117**: only "Emergency brake pressure sw." events near its incident — not bearing-related.
- **30532**: zero fault events near its 04/04/2024 incident.
- **30751**: fault events give a valuable precursor sequence (see §5.1) — **useful for validation/precursor mining, not timestamp recovery**.

**Pipeline anchor decision (evidence-based):**
**Owner Report → Continuous Telemetry (primary) → Fault Table (validation only).**

---

## 10. Key reference facts & numbers

| Fact | Value |
|---|---|
| Telemetry table size | ~5.31 B rows |
| Fault table size | ~405.6 M rows |
| RMS-master-listed locos | 846 |
| RMS locos with telemetry | 845 |
| RMS locos with telemetry AND faults | 442 |
| Bearing events in owner report | 41 |
| Bearing events with telemetry within ±5d | 3 |
| Usable pre-failure telemetry windows | 2 (37282, 30532) |
| Global telemetry on 16-Dec-2024 (healthy) | 3,902,008 rows / 121 locos |
| Indexed per-loco query | 0.04 s |
| `DISTINCT locoid` on main table | times out (>5 min) |
| RMS deployment start | effectively Apr 2024 (DB `SLAM_RDS_DB_26.04.2024`) |

---

## 11. Recommended next steps (evidence-based)

1. **Do NOT pivot to supervised classification yet** (2 positives).
2. Adopt the **hybrid health-monitoring architecture** (as recommended by the domain advisor):
   ```
   Continuous RMS Telemetry (845 locos)
        │
        ▼
   Data Quality → Health Index
        │                │
        ▼                ▼
   Anomaly Detection   Rule Engine (multi-signal precursors)
        │                │
        └────────┬───────┘
                 ▼
   Candidate Mechanical Events
                 │
                 ▼
   Validated Against Ground Truth (2–4 confirmed cases)
   ```
3. **Anomaly detection** models normal behaviour across the 845-loco fleet (large healthy pool).
4. **Rule engine** mines multi-signal precursor sequences (temperature-difference + bogie-off + TM-isolated + repeated occurrence + withdrawal within 24 h) — never a single alarm.
5. The small confirmed-failure set is used for **validation and calibration**, not training alone.
6. **RMS is a live feed** — future axle-lock events on RMS-equipped locos will grow the positive set, making supervised/hybrid training increasingly viable.

---

## 12. Artifacts produced

| Artifact | Path |
|---|---|
| Full audit report (this document) | `docs/data_audit_report.md` |
| Bearing-event audit (41 rows, per-event telemetry coverage) | `data/manifests/bearing_failure_events_audit.csv` |
| Ground truth registry | `data/processed/ground_truth_failure_registry.csv` |
| Owner classification | `data/processed/owner_failure_classification.csv` |
| Extraction manifest (408 windows) | `data/manifests/telemetry_extraction_manifest.csv` |
| Fault timestamp candidates | `data/processed/fault_time_reconciliation_candidates.csv` |
| Forensic audit tool | `src/rms_bearing/forensic_audit.py` |
| Batch availability health report | `src/rms_bearing/check_telemetry_availability.py` |
| Manifest builder | `src/rms_bearing/build_manifest.py` |
| Timestamp matcher | `src/rms_bearing/match_fault_timestamps.py` |
| Approved extraction | `src/rms_bearing/extract_telemetry.py` |
