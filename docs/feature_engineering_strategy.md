# Physics-Informed Feature Engineering Strategy
**Project:** Predictive Diagnostics for Locomotive Axle Bearings
**Date:** 2026-07-28

---

## 1. Introduction: The Need for Physics-Informed Machine Learning (PIML)
Recent industry research (2024-2025) demonstrates that applying purely data-driven machine learning models to railway telemetry often results in high false-alarm rates. This occurs because pure ML models struggle to distinguish between normal operational extremes (e.g., a locomotive pulling a heavy load up a steep incline in summer) and actual mechanical degradation.

By embedding the **laws of physics and thermodynamics** into the feature engineering process, we can guide the machine learning model (whether XGBoost or an LSTM-Autoencoder) to focus on structural anomalies rather than environmental fluctuations. This strategy outlines how we will transform the raw 169-parameter RMS data into physics-informed features.

---

## 2. RMS Telemetry vs Mechanical Reality
The RMS (Remote Monitoring System) provides 1-second resolution data for 169 parameters, including electrical, thermal, kinematics, and subsystem statuses. While we lack direct high-frequency vibration sensors (the traditional metric for bearing analysis), we can use the thermal and electrical signatures in the RMS data as proxies for mechanical friction and bearing lock.

---

## 3. Proposed Physics-Based Features

### 3.1 Thermal Differential Features (Symmetrical Component Analysis)
**The Physics:** 
According to thermodynamics, bearings on the same axle or bogie, operating under identical load and ambient conditions, should dissipate heat equally. Absolute temperatures fluctuate with the weather, but the *differential* between symmetrical components should remain near zero.
**Feature Extraction:**
*   **Delta-T (Bogie vs Bogie):** Calculate the absolute difference between symmetrical temperature sensors.
    *   `Temp_Diff_Motor_1` = `|xtempmotor1_1 - xtempmotor1_2|`
    *   `Temp_Diff_Motor_2` = `|xtempmotor2_1 - xtempmotor2_2|`
*   *Note: Recent standards (e.g., Indian Railways LHB coach guidelines) indicate that a >20°C differential is a critical threshold for axle box health.*

### 3.2 Heat Generation Rate vs. Dissipation (Cooling Constraints)
**The Physics:** 
Heat generation in a bearing is a function of friction and speed, while dissipation is controlled by convection (blowers). If a bearing's temperature rises *despite* the cooling system operating at full capacity, it violates normal cooling curves and indicates abnormal internal friction.
**Feature Extraction:**
*   **Cooling Inefficiency Score:** Combine the temperature gradient (dT/dt) with the blower status over a rolling window.
    *   `Gradient_Motor1` = Rate of change of `xtempmotor1_1` over 15 minutes.
    *   `Cooling_Inefficiency_Motor1` = `Gradient_Motor1 / (mmcbblotm1 + 0.1)` (Adding 0.1 avoids division by zero; `mmcbblotm1` is the blower status flag [0,1]).

### 3.3 Load-Normalized Temperature (Coupled Dynamics)
**The Physics:** 
Bearings naturally generate more heat when subjected to higher mechanical workloads. To prevent false positives during heavy haulage, the thermal metrics must be normalized against the locomotive's physical output.
**Feature Extraction:**
*   **Thermal-Mechanical Ratio:** Divide thermal metrics by the mechanical work (Speed $\times$ Tractive Effort).
    *   `Normalized_Temp_Motor1` = `xtempmotor1_1 / (xspeedloco * xte_be_loco)`
    *   This isolates "unexplained" heat that cannot be justified by the locomotive's current workload.

### 3.4 Electrical "Ripple" as a Proxy for Vibration
**The Physics:** 
Mechanical vibrations, grinding, and bearing locks induce torque ripples on the traction motor shaft. These torque ripples reflect back into the electrical system as micro-fluctuations in the motor current.
**Feature Extraction:**
*   **Current Micro-Volatility:** Measure the high-frequency volatility of the electrical currents over short windows.
    *   `Current_Volatility` = Rolling Standard Deviation (e.g., 1-minute window) of primary current (`xiprim_1`) or filter currents (`xaifilts_1`).
    *   High volatility serves as an electrical proxy for mechanical vibration.

### 3.5 Cumulative Stress (Fatigue Tracking)
**The Physics:** 
Bearing failure (spalling, flaking) is fundamentally a fatigue mechanism, meaning it results from accumulated stress over time rather than a single instantaneous event.
**Feature Extraction:**
*   **Rolling Fatigue Integrals:**
    *   **Thermal Fatigue:** The cumulative time (in minutes) the motor temperature has spent above a critical threshold (e.g., 85°C) over the preceding 72-hour window.
    *   **Mechanical Stress Integral:** The integral (sum) of the Tractive Effort (`xte_be_loco`) over the last 24 hours, representing the total workload the bearing has endured.

---

## 4. Summary & Implementation
By applying these physics-informed transformations, we reduce the high-dimensional, noisy 169-parameter dataset into a highly concentrated set of ~20-30 meaningful features. 

This dimension reduction is crucial for Phase 2 (XGBoost Baseline) and Phase 3 (LSTM-Autoencoder) of the implementation plan, as it ensures the models learn the fundamental mechanical degradation patterns of the locomotive rather than overfitting to environmental noise.
