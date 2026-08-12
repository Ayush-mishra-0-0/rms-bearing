# Integrated Predictive Diagnostics Framework for Indian Railways Locomotives

This plan details a phased, "pyramid" approach to predicting axle bearing failures by combining RMS telemetry data (169 parameters/second) with SLAM failure reports. We will start with establishing a baseline using robust machine learning techniques and iteratively move towards state-of-the-art deep learning architectures (LSTM Autoencoders) as identified in recent 2024-2025 research.

> **Data reality (updated by the audit):** RMS telemetry exists for 846 RMS-equipped locos; the Owner failure registry spans the whole fleet, and only ~2 confirmed bearing failures have usable pre-failure telemetry today. The design below therefore targets a **closed-loop, continually learning health-monitoring platform** that starts with anomaly detection + rule engine and evolves into supervised prediction as the live RMS feed and confirmed-failure registry grow.

## User Review Required

> [!IMPORTANT]
> **Data Integration Strategy**: The biggest initial hurdle is linking the RMS telemetry (1 second resolution) with SLAM reports (event-based). We need to clearly define the failure timestamp from SLAM and extract a specific "lookback window" (e.g., 24, 48, or 72 hours) from RMS to form our dataset. Please confirm if this approach aligns with your expectations. Note: audit evidence shows the fault table is **validation only** — the correct anchor is Owner Report → Continuous Telemetry → Fault Table.

## Open Questions

> [!WARNING]
> 1. **SLAM Data Schema**: We have explored the RMS data, but what is the exact schema and format of the SLAM reports you currently have (e.g., CSV, SQL dump)?
> 2. **Failure Definition**: In SLAM, how specifically is an "axle bearing failure" or "axle lock" recorded? Are there specific fault codes or text descriptions we need to filter for?
> 3. **Computational Resources**: Deep learning models (like LSTM Autoencoders) are resource-intensive. Do we have access to GPUs for training, or should we optimize strictly for CPU environments initially?
> 4. **Telemetry upload architecture**: Are telemetry and fault events transmitted over separate channels? Under what conditions does continuous telemetry stop while fault events continue? (Relevant to the observed 30751 December gap.)

## Proposed Architecture & Phased Implementation

### Phase 0: Closed-Loop System Backbone
*Established by the data audit; drives all later phases.*

```
Live RMS Stream (845 locos today → grows)
      │
      ▼
Raw Telemetry Lake → Data Validation & QC → Feature Store (time-series)
                                              │
                        ┌─────────────────────┴──────────────────────┐
                        ▼                                            ▼
               Health Index Engine                            Rule Engine
               (anomaly detection)                 (multi-signal precursor sequences)
                        │                                            │
                        └───────────────────┬────────────────────────┘
                                            ▼
                                    Candidate Events Queue
                                            │
                                            ▼
                                 Maintenance / Owner Feedback
                                            │
                        Confirmed Bearing Failure?  (No → loop)
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

- **Anomaly detection** models normal behaviour across the 845-loco healthy fleet (no labels needed today).
- **Rule engine** mines multi-signal precursors (temperature-difference + bogie-off + TM-isolated + repetition + withdrawal within 24 h) — never a single alarm.
- Confirmed failures (37282, 30532, and 30751's fault sequence) are used for **validation/calibration**; every new confirmed case grows the registry and retrains.

### Phase 1: Foundation (Data Engineering & Synchronization)
*Establishing the Bronze and Silver Layers.*

- **Data Ingestion (Bronze)**: Load raw RMS data (169 columns) and SLAM failure logs.
- **Data Synchronization (Silver)**:
  - Standardize timestamps between RMS and SLAM.
  - Handle missing values (e.g., forward fill for sensor data).
  - Detect and flag platform outages (Jul-2024, Oct-2024) and per-loco gaps as **data-quality signals**, not failures.
  - Filter and normalize RMS fault codes using the Severity mapping.
- **Label Generation**: Create the target labels from the confirmed-failure registry. For a locomotive that failed on day $D$, label the data from $D-1$ as `Degrading` and $D-3$ as `Healthy`. For locomotives with no SLAM failure records, label as `Healthy`.

### Phase 2: Feature Engineering & Baseline Modeling
*Establishing the Gold Layer and initial benchmarks.*

- **Window-based Feature Engineering**: Convert the 1-second telemetry into meaningful aggregations over sliding windows (e.g., 1-hour or 4-hour chunks).
  - Extract: Rolling mean, standard deviation, moving maximum (especially for temperatures and currents).
  - Calculate gradients (rate of change in temperature/current).
  - Count alarm frequencies from the categorized fault severity data.
- **Baseline Model (XGBoost)**:
  - Recent research shows XGBoost is highly effective for tabular, engineered features. We will train a baseline XGBoost classifier to predict `Failure within 24h` vs `Healthy`.
  - This provides an immediate proof-of-concept and a benchmark metric (F1-score, Precision, Recall).
  - *Given only ~2 confirmed positives today, this baseline is validated against the confirmed cases rather than trained on them.*

### Phase 3: Advanced Anomaly Detection (Research Tier)
*Moving towards state-of-the-art predictive maintenance.*

- **Unsupervised Anomaly Detection (LSTM Autoencoder)**:
  - Instead of relying solely on failure labels (which might be sparse), we will train an LSTM Autoencoder exclusively on `Healthy` telemetry data.
  - The model will learn the "normal" operational signature.
  - When fed telemetry from a degrading bearing, the model's reconstruction error will spike, acting as a **Health Index / Anomaly Score**.
- **Hybrid Approach**: Use the anomaly score from the Autoencoder as a feature fed into an Attention-based LSTM or XGBoost model to predict the Remaining Useful Life (RUL) or imminent failure probability.

### Phase 4: Continual Learning & Decision Support (Future Scope)
*The closed loop closes here.*

- **Continual/online learning**: retrain health models as new confirmed failures enter the registry (weakly-supervised → fully-supervised as positives grow).
- Convert risk scores into actionable recommendations: `Continue Monitoring`, `Schedule Inspection`, `Immediate Maintenance`.
- Lay the groundwork for a Digital Twin dashboard where telemetry updates the health state of each locomotive in real-time.

---

## Verification Plan

### Automated/Statistical Tests
- **Cross-Validation**: Use Time-Series Split cross-validation to ensure the model isn't "looking into the future."
- **Metrics**: Evaluate models strictly on Precision, Recall, and F1-score (especially focusing on Recall to minimize false negatives/missed failures).

### Manual Verification
- **Case Studies**: Manually plot the generated Health Index/Anomaly Score against the raw telemetry for 2-3 known failure events to visually verify that the model detects degradation hours before the SLAM failure timestamp.
