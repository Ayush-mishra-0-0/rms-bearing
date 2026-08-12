"""RMS monitor watcher.

Runs every few minutes (Windows Task Scheduler) and:
  1. takes cheap index-safe heartbeats (telemetry + faults),
  2. compares against thresholds / learned baseline,
  3. alerts on transitions (and re-alerts every N minutes while unresolved),
  4. logs measurements to reports/history.csv.

Usage:
    python -m monitoring.watch            # real run (emails alerts)
    python -m monitoring.watch --dry-run  # print would-be alerts, no email
"""
import argparse
import sys
from datetime import datetime, timedelta

from . import checks, notify
from .config import settings
from .state import (
    append_history,
    baseline_medians,
    estimated_skew,
    load_state,
    log_alert,
    record_skew,
    save_state,
)


def _fmt(dt):
    if dt is None:
        return "never"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _iso(dt):
    if dt is None:
        return None
    return dt.isoformat() if isinstance(dt, datetime) else str(dt)


def _evaluate_advance(state, current_max, last_key, since_key, stall_min):
    """Detect 'no new rows' robustly and skew-insensitively.

    Returns (healthy, since_raw): healthy is False only once the stream max has
    been stuck for >= stall_min minutes."""
    last = state[last_key]
    last_dt = None
    if last is not None:
        try:
            last_dt = datetime.fromisoformat(str(last))
        except ValueError:
            last_dt = None
    advanced = current_max is not None and (last_dt is None or current_max > last_dt)
    if advanced:
        state[since_key] = None
    elif state[since_key] is None and current_max is not None:
        state[since_key] = _iso(datetime.now())
    if current_max is not None:
        state[last_key] = _iso(current_max)
    since_raw = state[since_key]
    if since_raw is None:
        return True, None, advanced
    since = datetime.fromisoformat(str(since_raw))
    minutes = (datetime.now() - since).total_seconds() / 60
    return minutes < stall_min, since_raw, advanced


def run(dry_run=False):
    cfg = settings()
    state = load_state()

    try:
        conn = checks.connect()
        measure = checks.heartbeat(conn)
        conn.close()
    except checks.CheckError as e:
        # connection failure is itself an incident
        log_alert("ALERT CONNECT_FAIL WHERE: SLAM_RDS DB\n    %s" % e)
        if not dry_run:
            notify.send(
                "CRIT: RMS DB unreachable",
                notify.incident_body("DB connection failed", "check start", "server %s db %s" % (cfg["db_server"], cfg["db_name"]), detail=str(e)),
            )
        return 1

    now = measure["server_now"]
    tele = measure["telemetry"]
    fa = measure["faults"]

    baseline = baseline_medians()

    def update(check_key, status, since, severity, where, detail=""):
        """Record status, dedupe and escalate alerts (transition + re-alert)."""
        cur = state["checks"].setdefault(check_key, {})
        prev = cur.get("status", "ok")
        if status == "ok":
            if prev != "ok":
                cur.update(status="ok", since=None, last_alerted=None)
                if dry_run:
                    print("[DRY-RUN] WOULD SEND: RESOLVED %s (%s)" % (check_key.replace("_", " ").title(), where))
                else:
                    notify.send("RESOLVED: %s" % check_key.replace("_", " ").title(), notify.recovery_body(check_key, where))
            return False
        # incident is active
        if prev != "ok":
            cur.setdefault("since", _iso(since) or _iso(datetime.now()))
        else:
            cur["since"] = _iso(since) or _iso(datetime.now())
        cur.update(status=status, severity=severity, where=where)
        last_alerted = cur.get("last_alerted")
        first = prev == "ok" or not last_alerted
        realert = last_alerted and (datetime.now() - datetime.fromisoformat(last_alerted)) >= timedelta(minutes=cfg["realert_min"])
        if first or realert:
            cur["last_alerted"] = datetime.now().isoformat()
            subject = "%s: %s" % (severity, check_key.replace("_", " ").title())
            body = notify.incident_body(detail or check_key, _fmt(cur["since"]), where)
            if dry_run:
                print("[DRY-RUN] WOULD SEND: %s\n%s\n" % (subject, body))
            else:
                notify.send(subject, body)
            return True
        return False

    # 1. telemetry advance (the 10-min rule); learn skew only while advancing
    healthy_tele, since, advanced_tele = _evaluate_advance(
        state, tele["max_device_time"], "last_telemetry_max",
        "telemetry_no_advance_since", cfg["telemetry_stall_min"])
    if advanced_tele:
        record_skew(state, now, tele["max_device_time"])
    skew = estimated_skew(state)
    state["last_advance_seen"] = now.isoformat()
    update(
        "telemetry_advance", "ok" if healthy_tele else "failing",
        since, "CRIT",
        "Lotus_loco_process_signals_RDSOJson",
        "no new telemetry rows for >= %d min (max DeviceTime stuck at %s)" % (cfg["telemetry_stall_min"], _fmt(tele["max_device_time"])) if not healthy_tele else "",
    )

    # 2. telemetry recent-window flow (absolute backstop, skew-corrected)
    if tele["max_device_time"] is not None:
        lag_min = ((now - tele["max_device_time"]).total_seconds() + skew) / 60
        update(
            "telemetry_lag", "ok" if lag_min <= cfg["telemetry_stall_min"] else "failing",
            None, "CRIT",
            "Lotus_loco_process_signals_RDSOJson",
            "DeviceTime lag = %.0f min (> limit %.0f min)" % (lag_min, cfg["telemetry_stall_min"]) if lag_min > cfg["telemetry_stall_min"] else "",
        )

    # 3. telemetry volume vs baseline
    if baseline.get("telemetry_rows_24h"):
        drop = (1 - tele["rows_24h"] / baseline["telemetry_rows_24h"]) * 100
        update(
            "telemetry_volume", "ok" if drop <= cfg["volume_drop_pct"] else "failing",
            None, "WARN",
            "Lotus_loco_process_signals_RDSOJson",
            "24h rows = %d vs median %.0f (drop %.0f%%)" % (tele["rows_24h"], baseline["telemetry_rows_24h"], drop) if drop > cfg["volume_drop_pct"] else "",
        )

    # 4. fault advance
    healthy_f, since_f, _ = _evaluate_advance(
        state, fa["max_fault_time"], "last_fault_max",
        "fault_no_advance_since", cfg["fault_stall_min"])
    update(
        "fault_advance", "ok" if healthy_f else "failing",
        since_f, "CRIT",
        "Lotus_LocoFaultData (clean faulttime)",
        "no clean fault rows for >= %d min (max faulttime stuck at %s)" % (cfg["fault_stall_min"], _fmt(fa["max_fault_time"])) if not healthy_f else "",
    )

    # 5. fault volume vs baseline
    if baseline.get("fault_rows_24h"):
        drop = (1 - fa["rows_24h"] / baseline["fault_rows_24h"]) * 100
        update(
            "fault_volume", "ok" if drop <= cfg["volume_drop_pct"] else "failing",
            None, "WARN",
            "Lotus_LocoFaultData",
            "24h clean faults = %d vs median %.0f (drop %.0f%%)" % (fa["rows_24h"], baseline["fault_rows_24h"], drop) if drop > cfg["volume_drop_pct"] else "",
        )

    append_history(measure)
    save_state(state)

    # summary line
    print(
        "OK now=%s tele_max=%s tele_24h=%d fault_max=%s fault_24h=%d skew=%.0fs"
        % (now, _fmt(tele["max_device_time"]), tele["rows_24h"],
           _fmt(fa["max_fault_time"]), fa["rows_24h"], skew)
    )
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="RMS data-flow watcher")
    ap.add_argument("--dry-run", action="store_true", help="do not send emails")
    args = ap.parse_args(argv)
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
