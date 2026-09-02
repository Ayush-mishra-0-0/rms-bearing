# RMS Bearing Early-Warning — Executive Brief (One Page)

**For:** Senior / Director review &nbsp;|&nbsp; **Project:** Predictive detection of axle-bearing (traction-motor) failures &nbsp;|&nbsp; **Status:** Phase 1 complete

---

## The Goal

Predict traction-motor bearing failures **before they happen** by fusing **RMS continuous telemetry** (169 parameters/second, ~845 locos) with the **Owner failure registry**. Success = early warning that lets maintenance shift from reactive (failure, then repair) to predictive (flag, then inspect).

## Where We Went — Data Foundation (Done)

- **Ground-truth failure registry built:** 135 raw failure events → rigorously classified → 68 high-confidence → **41 confirmed bearing-specific events**.
- **Integrity-checked extraction pipeline:** manifest → timestamp reconciliation → telemetry-availability health check → approved extraction. Data quality issues (garbage timestamps, date-only events) are detected and blocked, never silently accepted.
- **Forensic audits completed:** flagship failure case (Loco 30751), fleet-wide telemetry coverage, and root-cause analysis of telemetry gaps around incidents.

## The Pivotal Finding

Only **6 of 122 failing locos are RMS-fitted**, and only **2 have usable pre-failure telemetry**. Therefore:

> **Supervised ML ("train on past failures") is not viable today.** We proved this rigorously with data audits — before wasting months on modeling that could not succeed.

This is a **coverage fact, not an algorithm failure** — and it redirected our architecture toward a design that works with the data we actually have.

## Why the Future Is Promising

1. **845 locos of healthy telemetry** — a large unlabeled dataset ideal for anomaly detection (no failure labels needed).
2. **RMS is a live feed** — every future failure on an RMS-equipped loco automatically grows our labeled dataset.
3. **Research-backed model path exists** — physics-informed features → XGBoost baseline → LSTM-autoencoder health index → hybrid failure prediction.

## How We Get There — Roadmap

| Phase | What | Value |
|---|---|---|
| **Now** | Anomaly detection on healthy fleet + rule engine for multi-signal precursor sequences (validated against our 2 confirmed cases) | Early-warning capability with today's data |
| **As failures accrue** | Closed-loop learning: each confirmed failure retrains the models | System gets smarter automatically |
| **Maturity** | Supervised hybrid models, per-loco Health Index, maintenance decision support | Predictive maintenance at scale |

## Decisions / Support Requested

1. **Alternate telemetry sources?** 35 of 41 bearing-failure locos have zero telemetry in this database — is data available elsewhere?
2. **Compute access** (GPU) for deep-learning phases.
3. **Endorsement of the anomaly-first architecture** given the evidence in the data audit.

---

**One-line summary:** *We built a rigorous data foundation, discovered the honest data reality before it burned us, and designed a system that starts delivering value today and gets smarter with every future failure.*

*Evidence: `docs/data_audit_report.md`, `docs/comprehensive_progress_report.md`, `plan.md`.*
