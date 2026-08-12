"""RMS monitoring configuration.

Loads database + alerting settings from the repo-root .env file and exposes
monitoring thresholds with sane defaults. Every threshold can be overridden
through the environment (see README).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = Path(__file__).resolve().parent / ".env"
if not ENV_PATH.exists():  # fall back to repo-root .env
    ENV_PATH = REPO_ROOT / ".env"
load_dotenv(ENV_PATH)

REPORTS_DIR = REPO_ROOT / "reports"
STATE_DIR = Path(__file__).resolve().parent / "state"

STATE_FILE = STATE_DIR / "rms_monitor_state.json"
HISTORY_CSV = REPORTS_DIR / "history.csv"
ALERT_LOG = REPORTS_DIR / "alerts.log"

for _d in (REPORTS_DIR, STATE_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def _int(name, default):
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


def _float(name, default):
    try:
        return float(os.getenv(name, "") or default)
    except ValueError:
        return default


def _split_csv(name):
    return [x.strip() for x in os.getenv(name, "").split(",") if x.strip()]


def settings():
    return {
        # DB (from .env)
        "db_server": os.getenv("DB_SERVER"),
        "db_name": os.getenv("DB_NAME"),
        "db_user": os.getenv("DB_USERNAME"),
        "db_password": os.getenv("DB_PASSWORD"),
        "query_timeout": _int("MONITOR_QUERY_TIMEOUT", 90),
        # Watch cadence + thresholds
        "watch_interval_min": _int("MONITOR_WATCH_INTERVAL_MIN", 5),
        # Minutes without ANY new row in the live telemetry feed -> CRIT
        "telemetry_stall_min": _int("MONITOR_TELEMETRY_STALL_MIN", 10),
        # Minutes without a clean fault record (legacy indexed table, sparse) -> CRIT
        "fault_stall_min": _int("MONITOR_FAULT_STALL_MIN", 60),
        # Rolling window (hours) used for the recent-flow count in the watcher
        "recent_window_h": _float("MONITOR_RECENT_WINDOW_H", 3),
        # Volume drop % vs trailing baseline median before WARN
        "volume_drop_pct": _float("MONITOR_VOLUME_DROP_PCT", 50),
        # Active-loco drop % vs trailing baseline median before WARN (daily)
        "loco_drop_pct": _float("MONITOR_LOCO_DROP_PCT", 50),
        # Baseline needs at least this many history samples before volume alerts fire
        "baseline_min_samples": _int("MONITOR_BASELINE_MIN_SAMPLES", 3),
        # Re-alert every N minutes while an incident persists
        "realert_min": _int("MONITOR_REALERT_MIN", 60),
        # Alerting channel
        "smtp_host": os.getenv("SMTP_HOST", ""),
        "smtp_port": _int("SMTP_PORT", 587),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "smtp_from": os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "")),
        "mail_to": _split_csv("MAIL_TO"),
    }
