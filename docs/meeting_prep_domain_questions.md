# Meeting Prep — RMS Telemetry Gap Mystery & System Design Questions

**Date:** 31-Jul-2026
**Purpose:** One-page evidence brief + the exact questions to ask domain/system experts in the meeting. Pair with `data_audit_report.md` and `comprehensive_progress_report.md`.

---

## 1. The two established facts (bring these to the meeting)

### Fact 1 — Fleet mismatch
- Owner Failure dataset = **entire fleet** (122 failing locos). RMS telemetry = **845 master-listed locos; ~2,387 distinct locos in the authoritative `RMSLocoMap` fitment roster** (2,408 rows; LotusWireless 1072, ARC 525, Medha 457, Siemens 348, + others; ~281 junk entries).
- Only **10** of the failing locos are in `RMSLocoMap`; only **41** bearing events exist; only **2** have usable pre-failure telemetry (37282 dense, 30532 sparse).
- **Verified, stronger form:** of the 41 bearing-event locos, **35 have ZERO telemetry rows in the entire 2-year period** (whole-table membership check); only 6 have telemetry anywhere; only 5 are in `RMSLocoMap`.
- → Not enough confirmed positives for supervised training today. → **Open question: is there another telemetry source for these 35 locos?**

### 1.1 Per-table breakdown (which loco was found in which table)

Full membership grid for the **41 bearing-event locos**, checked against: `Lotus_loco_process_signals` (telemetry), `Lotus_LocoFaultData` (faults), and the three master/metadata tables `rmslocolist`, `LomNumber`, `Loco_Process_Signals_LocoNumber`, plus `RMSLocoMap`:

| Loco | Telemetry | Faults | rmslocolist | LomNumber | Loco_Process_Signals_LocoNumber | RMSLocoMap |
|---|---|---|---|---|---|---|
| 30751 | ✔ | ✔ | ✔ | – | ✔ | ✔ |
| 37282 | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| 37361 | ✔ | ✔ | – | ✔ | – | ✔ |
| 30514 | ✔ | ✔ | – | – | – | ✔ |
| 30532 | ✔ | ✔ | – | – | – | ✔ |
| 32134 | ✔ | ✔ | – | – | – | – |
| 37044 | – | ✔ | – | – | – | – |
| 30319, 30341, 30354, 30486, 30642, 30675, 31327, 32004, 32054, 32114, 32515, 32562, 33516, 33574, 33636, 33696, 33700, 33734, 37002, 37038, 37118, 37271, 37353, 37373, 37374, 37491, 37508, 37544, 37619, 39026, 39114, 41733, 43016, 43368 | – | – | – | – | – | – |

**Venn summary of the 41:**

| Combination | Count | Locos |
|---|---:|---|
| **In no table at all** | **34** | (the 34 above) |
| Telemetry + Faults + rmslocolist + LomNumber + LocoProcSigNo + RMSLocoMap (all) | 3 | 30751, 37282, 37361 |
| Telemetry + Faults + RMSLocoMap (not in master lists) | 2 | 30514, 30532 |
| Telemetry + Faults only (no master list, no RMSLocoMap) | 1 | 32134 |
| Faults only | 1 | 37044 |

**What the table membership teaches us:**
- The three "master lists" are **not consistent with each other** (37361 is in `LomNumber` but not in `rmslocolist`/`Loco_Process_Signals_LocoNumber`; 30751 is in `rmslocolist` + `Loco_Process_Signals_LocoNumber` but not `LomNumber`). They are overlapping, partially stale inventories — not one authoritative roster.
- `RMSLocoMap` is the only list that contains all 5 fitted locos (30751, 37282, 37361, 30514, 30532) → it is the best fitment source so far.
- **32134** has real telemetry + faults but is in **no** metadata table → orphaned/stale inventory entry (worth raising).
- **37044** has fault events but **zero telemetry** → FaultData and ProcessSignals are not produced identically (faults buffered/different channel, matching the 30751 December pattern).
- **34 of 41 are in no table at all** → these locos were never registered as RMS-fitted in this DB, which is the core of the fleet-coverage story.**

### Fact 2 — Telemetry gaps around incidents
- 30751: gap `11–17 Dec 2024`, incident day inside it; **fault events kept flowing** (bogie cut-out precursors 16 Dec).
- 37361: only 1 telemetry day in the 5-week window around its 03-Aug-2024 failure.
- 30532: sparse telemetry 01–07 Apr 2024 (its failure 04 Apr) then platform down.

---

## 2. New evidence (just measured — the "why the gap" answer)

### 2.1 There are (at least) TWO platform-wide telemetry outages
Daily global row counts from `Lotus_loco_process_signals`:

| Window | Global rows/day | Verdict |
|---|---|---|
| 2024-06-01..06-03 | 25k → 80k | RMS ramp-up (RMS started ~Apr 2024) |
| 2024-06-04..07-04 | ~3.5–4.5M/day | Normal |
| **2024-07-05..07-27** | **~0–132k/day (0 on 17 & 21 Jul)** | **PLATFORM OUTAGE** |
| 2024-07-28..08-30 | ~3.5–4.4M/day | Normal |
| 2024-10-01..10-09 | ~3.6–4.6M/day | Normal |
| **2024-10-10..10-17** | **862k → 0,0,0 → 44 rows** | **PLATFORM OUTAGE** |
| 2024-10-18..2025-01-30 | ~3–4.5M/day | Normal |
| 2025-01-31 | ~4.1M rows | Normal (2025-01-16 also normal ~3.9M — earlier draft wrongly flagged it) |

**Verified zero-global days (exact): 2024-07-17, 2024-07-21, 2024-10-11, 2024-10-12, 2024-10-13** (`sql/audit/03_global_daily_rows.sql`).

### 2.2 The gaps are synchronized across locos
30751, 39085 (a **healthy** loco), and 37282 all went silent on **05–27 Jul 2024** simultaneously — proof that July's gap is platform-wide, not loco-specific.

### 2.3 But 30751's December gap is genuinely per-loco
Global rows on 11–17 Dec 2024 were healthy (~3.9–4.3M/day). Only 30751 stopped. And its **fault channel kept working** through the gap. → This is the "telemetry dead, faults alive" pattern (advisor's Hypothesis A).

---

## 3. Hypothesis ranking for the December per-loco gap (30751)

| # | Hypothesis | Support |
|---|---|---|
| A | **Separate comm channels** — telemetry modem vs event logger are independent paths; telemetry dropped but fault events still transmitted/buffered | **Strongest.** Faults flowed through the gap; only process-signals stopped. Also matches 37044 (faults but zero telemetry). |
| B | **Upload stops on serious fault / MCE-off** — logger still records discrete alarms | Possible. Bogie cut-out faults on 16 Dec coincide with the incident. |
| C | **Archived elsewhere** — continuous telemetry redirected during severe failure | Checked: no rows in any of 9+ candidate tables. Unlikely. |
| D | **Date/timestamp mismatch** — owner report date ≠ actual incident | **Refuted.** Owner date aligns with RMS; a 1-day reporting offset does not explain a 7-day gap. |

---

## 3.1 External verification (web) — is RMS fitted on every loco?

Public sources confirm RMS is **not** fleet-wide; it is a **progressively fitted subsystem** on a subset of locomotives:

| Source | Finding |
|---|---|
| **ARC (Advanced Rail Controls) product page** — `arc.net.in` / `irfleetmonitor.in` | "Remote Monitoring System" (RDS/RMS): MVB-based, fitted on **WAP5/WAP7/WAG9 classes only**, roof unit with GSM/CDMA modems + GPS, transmits status + faults in real time. This matches the DB (`Lotus_loco_process_signals`, `Lotus_LocoFaultData`). |
| **PIB (Govt of India) 12-Dec-2013** | REMMLOT (diesel-loco equivalent) fitted on only **594 diesel locomotives**; "fitment is taken up by Production Units & Railways as per sanctions of Railway Board and availability of fund." |
| **RDSO / CLW spec `CLW/C-D&D/ES/3/0554` (Apr 2024)** | Technical specification for **Data Retrieval and Analytic System for Three-Phase Locomotives** — the RMS upgrade; still being tendered in 2026 (e.g., Vatva shed, tender `M-ELS-VTA-26-27-RMS`, opening 07-May-2026). |
| **Peer-reviewed REMMLOT study (Feb 2026, Research Square)** | Uses a MEDHA-propulsion WAP-7/WAG-9 from a fleet of **138 REMMLOT-equipped locos in SER zone**; confirms onboard VCU generates telemetry (60 params, 1 Hz) + fault logs. |

**Bottom line for the meeting:** the observation that **35 of 41 bearing-event locos have zero telemetry** is *expected* if RMS fitment is partial and phased. Our DB's `RMSLocoMap` already lists **~2,387 fitted locos** across five vendors (LotusWireless 1072, ARC 525, Medha 457, Siemens 348, CRIS/Equus/LRail 6) — a large but still partial share of ~5,500 electric locos. It does **not** prove a hidden second data source, but it should be confirmed by asking **question 7/8/9** — because if a loco class/shed *is* RMS-fitted yet absent from our DB, that would indicate an ingestion gap we must close.

**Per-loco note:** we could not verify an *individual* loco number's RMS fitment from public sources (no public per-loco registry exists). The per-loco check must come from the DB (`RMSLocoMap`) + the shed telemetry portal — this is exactly what questions 7–9 and 12 ask.

---

## 4. Questions for the domain/system experts (ask these, not model questions)

### Data architecture
1. What is the complete telemetry flow from onboard RMS → SQL Server? (Sensors → onboard logger → comms → DB.)
2. Are `Lotus_loco_process_signals` and `Lotus_LocoFaultData` produced by the **same** onboard unit?
3. Are telemetry and fault events transmitted over **separate channels**? (This is the key one.)
4. Under what conditions does continuous telemetry stop **while fault events continue**? (MCE-off? modem failure? shed parking? storage full?)
5. Is there **another archive or retention policy** for continuous telemetry during severe failures?
6. What was the cause of the **Jul-2024 and Oct-2024 platform-wide outages**? Will they recur / how are they detected?

### Fleet coverage
7. Is `RMSLocoMap` **current or historical**? It currently lists **2,408 rows / ~2,387 distinct locos** (LotusWireless 1072, ARC 525, Medha 457, Siemens 348, + others; ~281 non-numeric junk entries) — is that the full ever-fitted set, and why do the three master lists (`rmslocolist` 615, `LomNumber` 70, `Loco_Process_Signals_LocoNumber` 671) disagree so strongly with it?
8. Was the RMS-equipped fleet **changed/expanded over time**? (This explains June ramp-up and post-outage growth.)
9. Are there separate telemetry systems for **other vendors** (Medha, ARC) beyond LotusWireless?

### Labels (future positives)
10. Is there any **workshop / depot / job-card / overhaul database** outside the Owner report?
11. How are axle-lock / bearing-seizure cases **officially recorded** (fault codes, text)?
12. Can future confirmed failures be **automatically linked** to RMS data (loco + time)?

---

## 5. Proposed system direction (to present)

Build a **Closed-Loop Learning System** (not a one-off ML pipeline):

```
 Live RMS Stream
        │
        ▼
 Raw Telemetry Lake ──► Data Validation & QC ──► Feature Store (time-series)
                                                        │
                                       ┌────────────────┴────────────────┐
                                       ▼                                 ▼
                               Health Index Engine                  Rule Engine
                                       │                                 │
                                       └───────────────┬─────────────────┘
                                                       ▼
                                             Candidate Events Queue
                                                       │
                                                       ▼
                                            Maintenance / Owner Feedback
                                                       │
                                      Confirmed Bearing Failure? (No → loop)
                                                       │ Yes
                                                       ▼
                                              Ground Truth Registry
                                                       │
                                                       ▼
                                            Continual Learning Pipeline
                                                       │
                                                       ▼
                                            Updated Health Models
```

- Anomaly detection over the **healthy RMS fleet** (845 master-listed locos with telemetry); rule engine mines **multi-signal precursor sequences** (temperature-diff + bogie-off + TM-isolated + repetition + withdrawal within 24 h).
- Confirmed failures (2–4 today) used for **validation/calibration**; every new confirmed case **grows the registry** and retrains.
- As the fleet grows and RMS is live, the system naturally evolves: anomaly → weakly-supervised → fully-supervised → digital twin.

---

## 6. One-line framing for the meeting

> "The RMS platform has had documented outages and per-loco comm failures; the failure registry and RMS fleet barely overlap today, so I'm building a **closed-loop, continually learning health-monitoring platform** that starts with anomaly detection + rule engine, validates against the confirmed failures we have, and keeps learning as new telemetry and confirmed cases arrive."
