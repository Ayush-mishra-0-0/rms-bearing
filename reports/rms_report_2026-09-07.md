# RMS Data-Flow Report  2026-09-07

Server now (DB clock): `2026-09-07 10:31:24`  |  Report generated: `2026-09-07T10:31:10`

## 1. Feed status (live)

| Feed | Last row | Age | 24h rows |
|---|---|---|---|
| Telemetry `Lotus_loco_process_signals_RDSOJson` | 2026-09-05 06:00:22 | 62.5 h | 0 |
| Faults `Lotus_LocoFaultData` (clean) | 2026-09-07 06:54:23 | 3.6 h | 7 |

## 3. Faults, last 7 days (clean, legacy table)

| Day | Clean faults |
|---|---|
| 2026-08-31 | 2 |
| 2026-09-01 | 1 |
| 2026-09-02 | 7 |
| 2026-09-03 | 100 |
| 2026-09-04 | 311 |
| 2026-09-05 | 32 |
| 2026-09-06 | 8 |
| 2026-09-07 | 2 |

## 4. Context

- RMSLocoMap fitment roster: **2408** total, **2408** fitted (RMSFlag=Y)
- Clock skew (DeviceTime ahead of server clock): **35800 s**
- Mirror / staging tables (informational):
  - `Locoprocessdata` max ts: `2025-03-31 23:57:03`
  - `Lotus_loco_process_signals_5` max ts: `2025-07-30 23:59:59`
  - `Lotus_loco_process_signals_sma` max ts: `2026-05-29 23:59:59`
  - `temptoday_fault` max ts: `2026-02-27 15:06:52`

## 5. Recent history (from reports/history.csv)

| Run | tele_max | tele_24h | fault_max | fault_24h |
|---|---|---|---|---|
| 2026-08-12T13:25 | 2026-08-12 23:22:09 | 5976041 | 2026-08-12 02:18:27 | 7 |
| 2026-08-12T13:27 | 2026-08-12 23:22:09 | 5972036 | 2026-08-12 02:18:27 | 7 |
| 2026-08-12T13:30 | 2026-08-12 23:22:09 | 5959420 | 2026-08-12 02:18:27 | 7 |
| 2026-09-07T10:30 | 2026-09-05 06:00:22 | 0 | 2026-09-07 06:54:23 | 7 |

## 6. Recent alert log

    2026-08-12T13:30:02  ALERT RMS Daily Digest 2026-08-12
        WARN: |   Telemetry Advance (since ?) in RMS feeds |   Telemetry Lag (since ?) in RMS feeds |   Fault Advance (since ?) in RMS feeds |   Telemetry Volume (since ?) in RMS feeds |   Fault Volume (since ?) in RMS feeds

