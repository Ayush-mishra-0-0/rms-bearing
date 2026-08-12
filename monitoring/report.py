"""RMS daily deep report.

Runs once per day (Windows Task Scheduler). Writes a full Markdown report to
reports/YYYY-MM-DD.md, appends the slow daily metrics to history.csv, and can
email a terse digest listing only current issues (WHAT / SINCE / WHERE).

Usage:
    python -m monitoring.report            # full run (may take ~8-10 min)
    python -m monitoring.report --skip-slow  # skip 4-min distinct-loco query
    python -m monitoring.report --no-email   # no digest email
"""
import argparse
import sys
from datetime import datetime

from . import checks, notify
from .config import REPORTS_DIR, settings
from .state import append_history, estimated_skew, history_tail, load_state, recent_alert_log


def _fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "never"


def _age(dt, now, skew=0.0):
    if not dt:
        return "n/a"
    secs = (now - dt).total_seconds() + skew
    if abs(secs) < 3600:
        return "%.0f min" % (secs / 60)
    return "%.1f h" % (secs / 3600)


def run(skip_slow=False, no_email=False):
    cfg = settings()
    now_local = datetime.now()
    conn = checks.connect()

    print("connecting... (slow checks may take minutes)", flush=True)
    hb = checks.heartbeat(conn)
    now = hb["server_now"]
    tele = hb["telemetry"]
    fa = hb["faults"]

    slow = {}
    if skip_slow:
        slow = {"active_locos_24h": None, "fault_json_rows_24h": None, "skip_slow": True}
        daily_tele = None
        fault_json = None
    else:
        print("  telemetry 7d daily...", flush=True)
        daily_tele = checks.telemetry_7d_daily(conn)
        print("  active locos 24h (~4 min)...", flush=True)
        slow["active_locos_24h"] = checks.telemetry_active_locos_24h(conn)
        print("  fault JSON metrics...", flush=True)
        fault_json = checks.fault_json_metrics(conn)
        slow["fault_json_rows_24h"] = fault_json["rows_24h"]
    fault_legacy_7d = checks.fault_legacy_7d(conn)
    rmsloco = checks.rmsloco_map(conn)
    mirrors = checks.mirror_tables(conn)
    conn.close()

    hist = history_tail(14)
    alerts = recent_alert_log(30)
    state = load_state()
    skew = estimated_skew(state)

    L = []
    add = L.append
    add("# RMS Data-Flow Report  %s" % now_local.strftime("%Y-%m-%d"))
    add("")
    add("Server now (DB clock): `%s`  |  Report generated: `%s`" % (_fmt(now), now_local.isoformat(timespec="seconds")))
    add("")

    add("## 1. Feed status (live)")
    add("")
    add("| Feed | Last row | Age | 24h rows |")
    add("|---|---|---|---|")
    add("| Telemetry `Lotus_loco_process_signals_RDSOJson` | %s | %s | %s |" % (
        _fmt(tele["max_device_time"]), _age(tele["max_device_time"], now, skew), tele["rows_24h"]))
    add("| Faults `Lotus_LocoFaultData` (clean) | %s | %s | %s |" % (
        _fmt(fa["max_fault_time"]), _age(fa["max_fault_time"], now), fa["rows_24h"]))
    if not skip_slow:
        add("| Faults `..._RDSOJson` (json) | %s (created %s) | | %s |" % (
            _fmt(fault_json["max_fault_time"]), _fmt(fault_json["max_created_on"]), fault_json["rows_24h"]))
    add("")

    if not skip_slow and daily_tele:
        add("## 2. Telemetry volume, last 7 days")
        add("")
        add("| Day | Rows |")
        add("|---|---|")
        for d, n in daily_tele:
            add("| %s | %s |" % (d, n))
        add("")
        add("Active locos in last 24h: **%s**" % slow.get("active_locos_24h"))
        add("")

    add("## 3. Faults, last 7 days (clean, legacy table)")
    add("")
    add("| Day | Clean faults |")
    add("|---|---|")
    for d, n in fault_legacy_7d:
        add("| %s | %s |" % (d, n))
    add("")

    add("## 4. Context")
    add("")
    add("- RMSLocoMap fitment roster: **%s** total, **%s** fitted (RMSFlag=Y)" % (rmsloco["total"], rmsloco["fitted"]))
    add("- Clock skew (DeviceTime ahead of server clock): **%.0f s**" % skew)
    add("- Mirror / staging tables (informational):")
    for t, mx in mirrors.items():
        add("  - `%s` max ts: `%s`" % (t, _fmt(mx)))
    add("")

    add("## 5. Recent history (from reports/history.csv)")
    add("")
    if hist:
        add("| Run | tele_max | tele_24h | fault_max | fault_24h |")
        add("|---|---|---|---|---|")
        for r in hist[-7:]:
            add("| %s | %s | %s | %s | %s |" % (r.get("ts", "")[:16], r.get("telemetry_max_dt", ""), r.get("telemetry_rows_24h", ""), r.get("fault_max_ft", ""), r.get("fault_rows_24h", "")))
    add("")

    add("## 6. Recent alert log")
    add("")
    if alerts:
        for a in alerts:
            add("    %s" % a)
    else:
        add("    (none)")
    add("")

    fname = "rms_report_%s.md" % now_local.strftime("%Y-%m-%d")
    path = REPORTS_DIR / fname
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote %s" % path)

    append_history(hb, slow)

    # optional terse digest email (issues only)
    if no_email:
        return 0
    crit, warn = [], []
    for ck, cur in state.get("checks", {}).items():
        if cur.get("status") != "ok":
            line = "%s (since %s) in %s" % (ck.replace("_", " ").title(), cur.get("since", "?"), "RMS feeds")
            (crit if cur.get("severity") == "CRIT" else warn).append(line)
    body = notify.digests([], warn, crit)
    notify.send("RMS Daily Digest %s" % now_local.strftime("%Y-%m-%d"), body)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="RMS daily deep report")
    ap.add_argument("--skip-slow", action="store_true", help="skip the slow (~4 min) distinct-loco query")
    ap.add_argument("--no-email", action="store_true", help="do not send the digest email")
    args = ap.parse_args(argv)
    return run(skip_slow=args.skip_slow, no_email=args.no_email)


if __name__ == "__main__":
    sys.exit(main())
