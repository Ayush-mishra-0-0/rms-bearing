# RMS Data-Flow Report  2026-08-12

Server now (DB clock): `2026-08-12 13:30:04`  |  Report generated: `2026-08-12T13:29:59`

## 1. Feed status (live)

| Feed | Last row | Age | 24h rows |
|---|---|---|---|
| Telemetry `Lotus_loco_process_signals_RDSOJson` | 2026-08-12 23:22:09 | 5 min | 5959420 |
| Faults `Lotus_LocoFaultData` (clean) | 2026-08-12 02:18:27 | 11.2 h | 7 |

## 3. Faults, last 7 days (clean, legacy table)

| Day | Clean faults |
|---|---|
| 2026-08-05 | 15 |
| 2026-08-06 | 11 |
| 2026-08-07 | 2 |
| 2026-08-09 | 19 |
| 2026-08-10 | 4 |
| 2026-08-11 | 25 |
| 2026-08-12 | 3 |

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

## 6. Recent alert log

    (none)

