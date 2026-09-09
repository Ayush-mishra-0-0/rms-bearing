"""RMS Prometheus exporter — reuses the index-safe heartbeat checks.

Runs next to the SLAM DB (same Windows box that runs watch.py), exposes
Prometheus gauges on :8000/metrics. Prometheus scrapes it; the Streamlit
dashboard (monitoring/dashboard.py) reads Prometheus for history graphs.

Exposed metrics:
  rms_telemetry_lag_minutes / rms_telemetry_rows_24h / rms_telemetry_rows_recent
  rms_telemetry_max_unixtime
  rms_fault_age_minutes / rms_fault_rows_24h / rms_fault_max_unixtime
  rms_check_status{check}  (1 = failing, 0 = ok — mirrors watch.py thresholds)
  rms_scrape_ok (1 = DB reachable) / rms_scrape_duration_seconds

Usage:
  pip install prometheus_client
  python -m monitoring.exporter --once        # single update + print (test, no server)
  python -m monitoring.exporter               # daemon on :8000, updates every 60s
  python -m monitoring.exporter --port 8000 --interval 60

Prometheus scrape config: see monitoring/prometheus.yml.
The exporter is READ-ONLY: it never writes state.json / history.csv (watch.py owns those).
"""
import argparse
import sys
import time
from datetime import datetime

try:
    from prometheus_client import Gauge, start_http_server
except ImportError:  # friendly error when deps not installed
    print("missing dep: pip install prometheus_client", file=sys.stderr)
    raise

from . import checks
from .config import settings
from .state import estimated_skew, load_state

G = {
    "tele_lag": Gauge("rms_telemetry_lag_minutes", "Skew-corrected lag of live telemetry feed"),
    "tele_24h": Gauge("rms_telemetry_rows_24h", "Telemetry rows in last 24h"),
    "tele_recent": Gauge("rms_telemetry_rows_recent", "Telemetry rows in recent window"),
    "tele_max": Gauge("rms_telemetry_max_unixtime", "Max DeviceTime as unixtime"),
    "fault_age": Gauge("rms_fault_age_minutes", "Age of max clean faulttime"),
    "fault_24h": Gauge("rms_fault_rows_24h", "Clean faults in last 24h"),
    "fault_max": Gauge("rms_fault_max_unixtime", "Max faulttime as unixtime"),
    "status": Gauge("rms_check_status", "1=failing 0=ok", ["check"]),
    "scrape_ok": Gauge("rms_scrape_ok", "1 if last DB heartbeat succeeded"),
    "scrape_dur": Gauge("rms_scrape_duration_seconds", "Last heartbeat duration"),
}


def update_once(verbose=True):
    cfg = settings()
    state = load_state()
    skew = estimated_skew(state)
    t0 = time.time()
    try:
        conn = checks.connect()
        try:
            m = checks.heartbeat(conn)
        finally:
            conn.close()
    except Exception as e:  # DB down -> expose scrape_ok=0, keep old values
        G["scrape_ok"].set(0)
        G["scrape_dur"].set(time.time() - t0)
        if verbose:
            print("scrape failed: %s" % e, flush=True)
        return None

    now = m["server_now"]
    tele, fa = m["telemetry"], m["faults"]
    tele_lag = ((now - tele["max_device_time"]).total_seconds() + skew) / 60 if tele["max_device_time"] else 1e9
    fault_age = ((now - fa["max_fault_time"]).total_seconds() / 60) if fa["max_fault_time"] else 1e9

    G["tele_lag"].set(tele_lag)
    G["tele_24h"].set(tele["rows_24h"] or 0)
    G["tele_recent"].set(tele["rows_recent"] or 0)
    if tele["max_device_time"]:
        G["tele_max"].set(tele["max_device_time"].timestamp())
    G["fault_age"].set(fault_age)
    G["fault_24h"].set(fa["rows_24h"] or 0)
    if fa["max_fault_time"]:
        G["fault_max"].set(fa["max_fault_time"].timestamp())
    # threshold mirrors of watch.py (so Prometheus can alert too)
    G["status"].labels("telemetry_lag").set(1 if tele_lag > cfg["telemetry_stall_min"] else 0)
    G["status"].labels("fault_advance").set(
        1 if fault_age > cfg["fault_stall_min"] else 0)
    G["scrape_ok"].set(1)
    G["scrape_dur"].set(time.time() - t0)
    if verbose:
        print("ok tele_lag=%.1fmin tele_24h=%s fault_age=%.1fmin (%s)" % (
            tele_lag, tele["rows_24h"], fault_age, now.strftime("%H:%M:%S")), flush=True)
    return {"tele_lag": tele_lag, "tele_24h": tele["rows_24h"], "fault_age": fault_age}


def main(argv=None):
    ap = argparse.ArgumentParser(description="RMS Prometheus exporter")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--interval", type=int, default=60, help="seconds between heartbeats")
    ap.add_argument("--once", action="store_true", help="single update, print, exit (no server)")
    args = ap.parse_args(argv)
    if args.once:
        return 0 if update_once() else 1
    start_http_server(args.port)
    print("exporter on :%d/metrics, heartbeat every %ds" % (args.port, args.interval), flush=True)
    while True:
        update_once()
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
