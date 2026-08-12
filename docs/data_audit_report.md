# RMS Bearing Failure Prediction — Data Audit Report

**Project:** Predicting traction-motor bearing (axle-lock) failures in Indian Railways locomotives using RMS telemetry
**Date:** 31-Jul-2026
**Data sources:** Owner Failure Report (`docs/1.1 IR Loco Asset Failure Report(Owner).xlsx`), SLAM_RDS DB (LotusWireless RMS), master lists in the SLAM DB
**Artifacts:** `data/manifests/bearing_failure_events_audit.csv`, `data/manifests/telemetry_extraction_manifest.csv`, `data/processed/ground_truth_failure_registry.csv`

---

## 1. Executive summary

The Owner Failure dataset covers the **entire locomotive fleet**, while RMS telemetry exists for only a **subset of RMS-equipped locomotives**. The two populations barely overlap, and this — not an algorithm failure — is the reason very few confirmed bearing failures have usable pre-failure telemetry.

After **exhausting every available source of confirmed positives**, the fleet can support **at most 2–3 usable pre-failure telemetry windows** for axle-lock prediction. This is **insufficient for supervised classifier training**. The correct architecture is a **hybrid health-monitoring system** (data quality → health index → anomaly detection + rule engine → candidate events validated against ground truth), with the confirmed failures used for validation/calibration rather than training alone.

---

## 2. Data sources reviewed

| Source | Contents | Failure history? |
|---|---|---|
| `1.1 IR Loco Asset Failure Report(Owner).xlsx` | 135 events, 122 distinct locos, **all "Traction Motor G9P7"**, 2024 (133) + 2026 (2) | **Yes — the sole failure label source** |
| `RMS data.xlsx` | Signal dictionary (locoid, lat, long, altitude, ...) | No |
| `RMS fault severity.xlsx` | Fault-text severity categories (safety/energy/... 196 rows) | No |
| `LocoMaster` (DB, 19,423 rows) | Locomotive asset master (wheel dia, dates, type) — static | No |
| `LocoStatus`, `Locofault`, `WheelData`, `RMSAlerts` (DB) | Stub / lookup tables (Locofault = loco→count, WheelData = 2 rows) | No |
| `Lotus_loco_process_signals` (DB) | ~5.3B rows continuous telemetry | No (telemetry only) |
| `Lotus_LocoFaultData` (DB) | ~405.6M rows RMS fault events | Yes — but validation only (see §5) |

**No workshop / depot / job-card / overhaul history exists in any available source.**

---

## 3. Fleet coverage — the core finding

RMS master lists in the DB:

| Master list | Rows | Locos that appear |
|---|---|---|
| `rmslocolist` | 615 | 30751, 37282, 39117, 44092, ... |
| `LomNumber` | 70 | 30346, 37282, 37361, 39117, ... |
| `Loco_Process_Signals_LocoNumber` | 671 | 30751, 37282, 39117, 44092, ... |
| **Union (master lists)** | **846** | RMS locos in the three master lists (partial/stale — undercounts) |
| **RMSLocoMap (RMSFlag=Y)** | **2,408 rows / ~2,387 distinct** | **Authoritative fitment roster** (LotusWireless 1072, ARC 525, Medha 457, Siemens 348, + others; ~281 non-numeric junk entries) |

Cross-reference with failure datasets:

| Dataset | Events | Distinct locos | Locos in RMSLocoMap | Locos in master-union |
|---|---|---|---|---|
| Full owner classification | 135 | 122 | **10** (30346, 30451, 30514, 30532, 30751, 31444, 37282, 37361, 39117, 44092) | 6 (30346, 30751, 37282, 37361, 39117, 44092) |
| Ground-truth registry (LEVEL_1/2) | 68 | 66 | **6** (30514, 30532, 30751, 37282, 37361, 39117) | 4 (30751, 37282, 37361, 39117) |

**Interpretation:** ~122 distinct locomotives failed (owner report), and **10 of them are listed in the authoritative `RMSLocoMap` fitment roster** (6 in the smaller master-union). The other ~112 failed on locomotives that **never had RMS fitted** — so they have no telemetry **by design**, not by an error. Note: several of the 10 (e.g. 30451 fitted 2026-03-17, 30514 fitted 2026-03-13) were fitted *after* their failure date, and 31444/30451 are REJECT-classified (speed-sensor), not bearing failures.

---

## 4. Confirmed positive pool — exhaustive search

### 4.1 Bearing-failure events in the owner report

From the raw Excel `Failure/Defect` column, **41 events are bearing-related** (TM bearing seized, DE bearing seize, outer labyrinth displaced/rubbing, rotor labyrinth). These are the axle-lock positives.

### 4.2 Telemetry availability near each failure (within ±5 days)

Of the **41 confirmed bearing events**, only **3** have ANY telemetry within ±5 days:

| Loco | Failure date | Defect | Telemetry ±5d (rows) | Telemetry ±1d (rows) | Usable pre-failure window? |
|---|---|---|---|---|---|
| **30532** | 04/04/2024 | DE bearing seize | 8,076 | 3,908 | **YES (sparse)** — daily 317–2,901 rows on 01–04 Apr |
| **37282** | 10/12/2024 | TM bearing seized | 359,439 | 130,047 | **YES (dense)** — 21k–72k rows/day throughout early Dec |
| **30751** | 17/12/2024 | TM bearing seized | 52,546 | 4,395 | **NO** — gap 11–17 Dec; only post-failure (18 Dec+) telemetry |

All other 38 bearing events have **zero telemetry within ±5 days** (locomotives not RMS-equipped).

**Whole-period membership check** (does the loco appear ANYWHERE in the 2-year window, not just near the failure)? Verified against `Lotus_loco_process_signals`, `Lotus_LocoFaultData`, the three master lists, and `RMSLocoMap`:

| Check | Count (of 41) | Locos |
|---|---|---|
| Telemetry **anywhere** in the period | **6** | 30514, 30532, 30751, 32134, 37282, 37361 |
| Fault events anywhere | **7** | the 6 above + 37044 |
| In RMS master lists | **3** | 30751, 37282, 37361 |
| In `RMSLocoMap` (fitted) | **5** | 30514, 30532, 30751, 37282, 37361 |
| **Zero telemetry anywhere** | **35** | all the rest |

**Interpretation:** 35 of 41 bearing-event locos sent **zero telemetry rows ever** to this DB. They were either never RMS-fitted or their data never reached this database. Note the master lists undercount fitment vs `RMSLocoMap` (which adds 30514, 30532); even taking `RMSLocoMap` as authoritative, only **5 of 41** are RMS-fitted. The question "is there another data source / telemetry system for these locos?" is for the domain experts — within this DB they have no signal.

### 4.3 Telemetry gaps around incidents

Several RMS-equipped locos show per-loco telemetry outages exactly around incidents (a per-loco device/uplink issue, not a platform outage):

- **30751**: 0 rows 2024-12-11 → 2024-12-18 17:05; platform globally healthy on 16 Dec (3.9M rows / 121 locos). Fault events continued through the gap.
- **37361**: telemetry exists (Apr 2024–May 2026) but **only one day (23-Jul-2024, 4,639 rows) in the whole 15-Jul→20-Aug 2024 window** around its 03-Aug-2024 failure → also unusable.
- **30532**: telemetry present but sparse (daily 317–2,901 rows, 01–07 Apr 2024) around its 04-Apr-2024 failure → usable but low-density.

### 4.3b Note on "68 confirmed events" vs "41 bearing events"

- The ground-truth registry (68 events) counts **all confirmed traction-motor failures** — including bearing seizures, winding flashes, labyrinth displacement, pinion/speed-sensor defects, etc.
- The **41 bearing events** are the *bearing-specific* subset (TM bearing seized / DE bearing seize / labyrinth) — these are the true axle-lock candidates. Of those 41, only 3 have any telemetry within ±5 days, and only 2 have usable pre-failure windows.

### 4.4 Conclusion on positive pool

| Category | Count |
|---|---|
| Bearing events in owner report | 41 |
| ...on RMS-master-listed locos | 3 |
| ...with any telemetry within ±5 days | 3 |
| **...with usable pre-failure telemetry** | **2** (30532 sparse, 37282 dense) |

**A supervised classifier cannot be trained on 2–3 positive windows.** This is the definitive, evidence-backed answer to whether we have "enough data".

---

## 5. Fault table (Lotus_LocoFaultData) — validation only

The RMS fault table is **not** a reliable timestamp anchor on its own:

- **37282**: fault events have garbage timestamps spanning 1901–2037; effectively no valid fault events around 10-Dec-2024.
- **39117**: only "Emergency brake pressure sw." events near incident — not bearing-related.
- **30532**: zero fault events around 04-Apr-2024.
- **30751**: fault events DO give a valuable precursor sequence — 16-Dec 17:29/17:30 "STB1:0009 Rotary switch bogie 1 cut out" + "FLG1:0094 SS02 traction bogie1 off", repeated 20:38/20:39 — matching the reported bogie-cutout pattern. **Useful for validation / precursor mining, not for timestamp recovery.**

Correct pipeline anchor: **Owner Report → Continuous Telemetry (primary) → Fault Table (validation only).**

---

## 6. Recommended architecture (given the data reality)

```
Continuous RMS Telemetry (845 locos)
        |
        v
Data Quality
        |
        v
Health Index
   |          |
   v          v
Anomaly    Rule Engine
Detection   (fault precursors)
   |          |
   v----------v
Candidate Mechanical Events
        |
        v
Validated Against Ground Truth (2–4 confirmed cases)
```

- **Anomaly detection** models normal behaviour across the 845-loco RMS fleet (large healthy pool).
- **Rule engine** mines multi-signal precursor sequences (e.g., temperature-difference + bogie-off + TM-isolated + repeated occurrence + withdrawal within 24h) — never a single alarm.
- The **small confirmed-failure set** (30532, 37282, and 30751's fault sequence) is used for **validation and calibration**, not training alone.
- RMS telemetry is a **live feed** — future axle-lock events on RMS-equipped locos will grow the positive set over time, making supervised/hybrid training increasingly viable.

---

## 7. Key facts for reference

- DB: `SLAM_RDS_DB_26.04.2024` at `10.77.36.103`; RMS deployment effectively starts **Apr 2024** (no pre-2024 telemetry; 30751's 1910 dates are dirty timestamps).
- Telemetry scale: `Lotus_loco_process_signals` ≈ 5.3B rows; per-loco indexed access is ~0.04 s; full-table scans time out.
- 845/846 RMS-master-listed locos have telemetry (master-union roster); **the authoritative `RMSLocoMap` roster is ~2,387 locos** — full per-loco telemetry membership across it was not computed (DISTINCT/timeout limits), only the master-union (846) membership was. 442 master-listed locos have both telemetry AND fault events.
- Of the 41 bearing events, only 3 have any telemetry within ±5 days (30532, 37282, 30751); only **2 have usable pre-failure windows** (30532 sparse, 37282 dense). 30751's window is post-failure only; 37361 (despite having telemetry overall) has a gap around its 03-Aug-2024 failure; 39117 is a *winding* failure (LEVEL_2), not a bearing failure.
