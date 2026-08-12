"""Persistent state for the RMS monitor.

- Incident state per check (ok/alert, since, last alerted, last known stream maxes).
- Rolling history CSV used both for trend reports and for baseline thresholds.
"""
import csv
import json
from datetime import datetime
from pathlib import Path

from .config import ALERT_LOG, HISTORY_CSV, STATE_FILE

HISTORY_FIELDS = [
    "ts", "server_now", "telemetry_max_dt", "telemetry_rows_24h", "telemetry_rows_recent",
    "fault_max_ft", "fault_rows_24h", "active_locos_24h", "fault_json_rows_24h",
]


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    return {
        "checks": {},
        "skew_samples": [],  # max_device_time - server_now, in seconds
        "last_telemetry_max": None,
        "last_fault_max": None,
        "telemetry_no_advance_since": None,
        "fault_no_advance_since": None,
        "last_advance_seen": None,
    }


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    tmp.replace(STATE_FILE)


def record_skew(state, server_now, max_device_time):
    """Learn how far ahead DeviceTime runs vs server clock (auto-calibration)."""
    if max_device_time is None:
        return state
    skew = (max_device_time - server_now).total_seconds()
    state["skew_samples"].append(round(skew, 1))
    state["skew_samples"] = state["skew_samples"][-500:]
    return state


def estimated_skew(state):
    s = sorted(state.get("skew_samples", []))
    if not s:
        return 0.0
    n = len(s)
    return s[n // 2]  # median


def baseline_medians():
    """Median recent values from history for volume-drop checks."""
    if not HISTORY_CSV.exists():
        return {"telemetry_rows_24h": None, "fault_rows_24h": None, "active_locos_24h": None}
    vals = {"telemetry_rows_24h": [], "fault_rows_24h": [], "active_locos_24h": []}
    with open(HISTORY_CSV, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for k in vals:
                if row.get(k):
                    try:
                        vals[k].append(float(row[k]))
                    except ValueError:
                        pass
    out = {}
    for k, v in vals.items():
        v = [x for x in v if x > 0][-500:]
        if v:
            v.sort()
            out[k] = v[len(v) // 2]
        else:
            out[k] = None
    return out


def append_history(measure, slow=None):
    """Append one measurement row to the rolling CSV."""
    write_header = not HISTORY_CSV.exists()
    slow = slow or {}
    row = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "server_now": str(measure.get("server_now", "")),
        "telemetry_max_dt": str(measure.get("telemetry", {}).get("max_device_time", "")),
        "telemetry_rows_24h": measure.get("telemetry", {}).get("rows_24h", ""),
        "telemetry_rows_recent": measure.get("telemetry", {}).get("rows_recent", ""),
        "fault_max_ft": str(measure.get("faults", {}).get("max_fault_time", "")),
        "fault_rows_24h": measure.get("faults", {}).get("rows_24h", ""),
        "active_locos_24h": slow.get("active_locos_24h", ""),
        "fault_json_rows_24h": slow.get("fault_json_rows_24h", ""),
    }
    with open(HISTORY_CSV, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HISTORY_FIELDS)
        if write_header:
            w.writeheader()
        w.writerow(row)


def log_alert(line):
    with open(ALERT_LOG, "a", encoding="utf-8") as fh:
        fh.write("%s  %s\n" % (datetime.now().isoformat(timespec="seconds"), line))


def recent_alert_log(n=20):
    if not ALERT_LOG.exists():
        return []
    lines = ALERT_LOG.read_text(encoding="utf-8").splitlines()
    return lines[-n:]


def history_tail(n=14):
    if not HISTORY_CSV.exists():
        return []
    with open(HISTORY_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows[-n:]
