# RMS Data-Flow Monitor

Detects when RMS data stops flowing into the SLAM database and produces a daily
deep report. Runs on Windows via Task Scheduler using short Python invocations.

## What it monitors

The **live** RMS feed is the JSON telemetry table
`Lotus_loco_process_signals_RDSOJson` (indexed on `DeviceTime`, ~6M rows/day,
1319 active locos). Faults are tracked from `Lotus_LocoFaultData`
(indexed on `faulttime`). The legacy relational tables
(`Lotus_loco_process_signals`, `Locoprocessdata`, `signals_5`, `signals_sma`)
are **archived/lagged** — reported for information only.

Important: `DeviceTime`/`FaultTime` columns contain dirty rows with years up to
2044/2038. Every query is therefore **bounded to a recent window** (`<= now+1d`)
and only uses indexed columns, so a 5-minute cycle costs < 1 s.

## Layout

| File | Purpose |
|---|---|
| `monitoring/checks.py` | index-safe SQL checks (heartbeat + daily) |
| `monitoring/state.py` | incident state, dedupe/escalation, history CSV |
| `monitoring/notify.py` | SMTP email + free SMS gateways |
| `monitoring/watch.py` | the 5-min watcher |
| `monitoring/report.py` | the daily deep report |
| `reports/` | reports (`rms_report_YYYY-MM-DD.md`), `history.csv`, `alerts.log` |

## Setup

1. Ensure dependencies: `pip install pyodbc python-dotenv` (already used elsewhere in this repo).
2. Edit `monitoring/.env` (the database credentials and all monitor settings live here):
   - `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` — a **free** mail account.
     - Gmail: `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, and an **App Password** (enable 2-step verification → Google account → Security → App passwords). Free.
     - Outlook: `SMTP_HOST=smtp.office365.com`, `SMTP_PORT=587`.
   - `MAIL_TO` — comma-separated recipients.
   - **Free SMS** (best-effort, carrier-dependent) via email-to-SMS gateways,
     same SMTP account:
     - Reliance Jio: `9198XXXXXXXX@jio.com`
     - Airtel: `9198XXXXXXXX@airtelindia.com`
     - BSNL: `9194XXXXXXXX@bsnlmsg.in`
     Keep at least one normal email in `MAIL_TO` as the reliable copy.
3. Leave `SMTP_*` blank to run in **log-only** mode (alerts go to `reports/alerts.log`).

## Thresholds (in `monitoring/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `MONITOR_TELEMETRY_STALL_MIN` | 10 | no new telemetry row for this many minutes → CRIT |
| `MONITOR_FAULT_STALL_MIN` | 60 | faults are sparse by nature, so the default is higher |
| `MONITOR_WATCH_INTERVAL_MIN` | 5 | watcher cadence |
| `MONITOR_VOLUME_DROP_PCT` | 50 | 24h volume < median − this % → WARN |
| `MONITOR_LOCO_DROP_PCT` | 50 | active-loco count drop → WARN (daily) |
| `MONITOR_REALERT_MIN` | 60 | re-notify every N min while an incident persists |

## Calibration (recommended before going live)

The watcher compares against a rolling baseline learned from `reports/history.csv`,
so it never fires on normal feed behaviour. Run it in `--dry-run` for a few days
to seed history and watch the printed summary:

```
python -m monitoring.watch --dry-run
```

Once you are happy with the printed OK line, enable email and install the tasks.

## Install scheduled tasks (elevated PowerShell)

```
powershell -ExecutionPolicy Bypass -File setup_tasks.ps1
```

Creates `RMS_Monitor_Watch` (every 5 min) and `RMS_Monitor_Daily` (08:00).

## Manual runs

```
python -m monitoring.watch --dry-run    # test, no emails
python -m monitoring.watch              # real watcher run
python -m monitoring.report --skip-slow # daily report (~1 min, skips the 4-min query)
python -m monitoring.report             # full daily report (~8-10 min)
```

## What an alert email looks like

```
WHAT : No new telemetry rows for >= 10 min (max DeviceTime stuck at 2026-08-12 23:22:09)
SINCE: 2026-08-12 12:40
WHERE: Lotus_loco_process_signals_RDSOJson
```

The full detail lives in `reports/rms_report_YYYY-MM-DD.md`; the daily digest
email contains only the one-line issue list.
