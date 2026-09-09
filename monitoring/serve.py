"""RMS live status board — zero new dependencies (stdlib only).

Same data as the Streamlit dashboard (monitoring/dashboard.py) but runs on the
stock interpreter (pyodbc + python-dotenv only). Use this when pip/Streamlit is
unavailable. Also exposes a Prometheus scrape endpoint without prometheus_client.

Endpoints:
  /           HTML board (auto-refresh), stall incident banner front and center
  /api/status JSON with the same numbers
  /metrics    Prometheus text exposition (scrape with monitoring/prometheus.yml
              pointed at this port instead of :8000)

Run:
  python -m monitoring.serve            # http://localhost:8501
  python -m monitoring.serve --port 8501 --refresh 120
"""
import argparse
import html
import json
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import checks
from .config import REPORTS_DIR, settings
from .state import baseline_medians, estimated_skew, history_tail, load_state, recent_alert_log

_CACHE = {"at": 0.0, "data": None}
_LOCK = threading.Lock()


def _fmt(dt):
    if dt is None or dt == "":
        return "never"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def collect():
    """Fresh status dict; cheap heartbeat (<2s) + local files only."""
    cfg = settings()
    state = load_state()
    skew = estimated_skew(state)
    base = baseline_medians()
    out = {"checked_at": datetime.now().isoformat(timespec="seconds"),
           "skew_s": round(skew, 1), "thresholds": {
               "telemetry_stall_min": cfg["telemetry_stall_min"],
               "fault_stall_min": cfg["fault_stall_min"],
               "recent_window_h": cfg["recent_window_h"]},
           "live": None, "live_error": None,
           "history": history_tail(30), "alerts": recent_alert_log(10),
           "checks": state.get("checks", {})}
    try:
        conn = checks.connect()
        try:
            m = checks.heartbeat(conn)
        finally:
            conn.close()
        now, tele, fa = m["server_now"], m["telemetry"], m["faults"]
        tele_lag = ((now - tele["max_device_time"]).total_seconds() + skew) / 60 \
            if tele["max_device_time"] else float("inf")
        fault_age = ((now - fa["max_fault_time"]).total_seconds() / 60) \
            if fa["max_fault_time"] else float("inf")
        out["live"] = {
            "server_now": _fmt(now),
            "tele_max": _fmt(tele["max_device_time"]), "tele_lag_min": round(tele_lag, 1),
            "tele_24h": tele["rows_24h"], "tele_recent": tele["rows_recent"],
            "tele_baseline": base.get("telemetry_rows_24h"),
            "fault_max": _fmt(fa["max_fault_time"]), "fault_age_min": round(fault_age, 1),
            "fault_24h": fa["rows_24h"],
            "stalled": bool(tele_lag > cfg["telemetry_stall_min"] or tele["rows_24h"] == 0),
        }
    except Exception as e:
        out["live_error"] = str(e)
    md = sorted(REPORTS_DIR.glob("rms_report_*.md"))
    out["latest_report"] = md[-1].name if md else None
    return out


def cached(ttl=60):
    with _LOCK:
        if _CACHE["data"] is None or time.time() - _CACHE["at"] > ttl:
            _CACHE["data"] = collect()
            _CACHE["at"] = time.time()
        return _CACHE["data"]


def render(d, refresh):
    e = html.escape
    if d["live"]:
        lv = d["live"]
        if lv["stalled"]:
            banner = ("<div class=banner style='background:#7f1d1d'>INCIDENT: telemetry feed STOPPED "
                      "&mdash; last row %s (%.1f h ago), %s rows in 24h. Faults still flowing, "
                      "so the DB is up; the break is upstream.</div>"
                      % (e(lv["tele_max"]), lv["tele_lag_min"] / 60, lv["tele_24h"]))
            status = "<span class=badge style='background:#dc2626'>STALLED</span>"
        else:
            banner = ("<div class=banner style='background:#14532d'>FLOWING &mdash; telemetry lag %.0f min, "
                      "faults %.1f h old (sparse by nature).</div>"
                      % (lv["tele_lag_min"], lv["fault_age_min"] / 60))
            status = "<span class=badge style='background:#16a34a'>FLOWING</span>"
        cards = (
            "<div class=grid>"
            "<div class=card><h3>Telemetry max DeviceTime</h3><p>%s</p><small>lag %.0f min</small></div>"
            "<div class=card><h3>Telemetry rows / 24h</h3><p>%s</p><small>baseline %s</small></div>"
            "<div class=card><h3>Telemetry rows / recent</h3><p>%s</p></div>"
            "<div class=card><h3>Fault max faulttime</h3><p>%s</p><small>%.1f h old, %s / 24h</small></div>"
            "</div><p><small>Server now (DB clock): %s &middot; skew %.0fs &middot; checked %s</small></p>"
            % (e(lv["tele_max"]), lv["tele_lag_min"], lv["tele_24h"],
               lv["tele_baseline"] if lv["tele_baseline"] else "?",
               lv["tele_recent"], e(lv["fault_max"]), lv["fault_age_min"] / 60,
               lv["fault_24h"], e(lv["server_now"]), d["skew_s"], e(d["checked_at"])))
    else:
        banner = "<div class=banner style='background:#713f12'>No live source: %s. Showing file cache below.</div>" % e(d["live_error"] or "?")
        status = "<span class=badge style='background:#ca8a04'>OFFLINE</span>"
        cards = ""
    hist = ""
    for r in reversed(d["history"][-14:]):
        hist += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            e(str(r.get("ts", ""))[:16]), e(str(r.get("telemetry_max_dt", ""))),
            e(str(r.get("telemetry_rows_24h", ""))), e(str(r.get("fault_max_ft", ""))),
            e(str(r.get("fault_rows_24h", ""))))
    alerts = "<br>".join(e(a) for a in d["alerts"][-10:]) or "(none)"
    return ("<!doctype html><html><head><meta charset=utf-8>"
            "<meta http-equiv=refresh content='%d'>"
            "<title>RMS data flow</title><style>"
            "body{font-family:Segoe UI,Arial,sans-serif;background:#111827;color:#e5e7eb;margin:0;padding:24px}"
            "h1{margin:0 0 4px}.banner{padding:14px 18px;border-radius:8px;font-size:18px;margin:16px 0}"
            ".badge{padding:4px 12px;border-radius:999px;font-weight:700}"
            ".grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}"
            ".card{background:#1f2937;border-radius:8px;padding:12px 16px}.card h3{margin:0 0 6px;font-size:13px;color:#9ca3af}"
            ".card p{margin:0;font-size:20px;font-weight:700}table{border-collapse:collapse;width:100%%;margin-top:8px}"
            "td,th{border:1px solid #374151;padding:6px 10px;font-size:13px;text-align:left}"
            "th{background:#1f2937}pre{background:#1f2937;padding:12px;border-radius:8px;overflow:auto;font-size:12px}"
            "small{color:#9ca3af}</style></head><body>"
            "<h1>RMS data flow %s</h1>"
            "<small>Live feed <code>Lotus_loco_process_signals_RDSOJson</code> &middot; "
            "Faults <code>Lotus_LocoFaultData</code> &middot; refresh %ss &middot; "
            "latest report <code>%s</code></small>"
            "%s%s<h2>Flow trend (reports/history.csv, latest first)</h2>"
            "<table><tr><th>Run</th><th>tele_max</th><th>tele_24h</th><th>fault_max</th><th>fault_24h</th></tr>%s</table>"
            "<h2>Recent alerts</h2><pre>%s</pre>"
            "</body></html>" % (refresh, status, refresh, e(d["latest_report"] or "none"),
                                banner, cards, hist, alerts))


def metrics_text(d):
    L = []
    lv = d["live"] or {}
    def g(k, v, h):
        L.append("# HELP %s %s\n# TYPE %s gauge\n%s %s" % (k, h, k, k, v if v == v else 0))
    import math
    for k in ("tele_lag_min", "tele_24h", "tele_recent", "fault_age_min", "fault_24h"):
        v = lv.get(k)
        g("rms_" + k, 0 if v is None or (isinstance(v, float) and math.isinf(v)) else v, k)
    g("rms_scrape_ok", 0 if d["live"] is None else 1, "scrape ok")
    g("rms_stalled", 1 if (lv.get("stalled")) else 0, "feed stalled")
    return "\n".join(L) + "\n"


class H(BaseHTTPRequestHandler):
    refresh = 120

    def log_message(self, *a):
        pass

    def do_GET(self):
        try:
            if self.path.startswith("/api/status"):
                body, ctype = json.dumps(cached(), default=str).encode(), "application/json"
            elif self.path.startswith("/metrics"):
                body, ctype = metrics_text(cached()).encode(), "text/plain; version=0.0.4"
            else:
                body, ctype = render(cached(), self.refresh).encode(), "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(("error: %s" % e).encode())


def main(argv=None):
    ap = argparse.ArgumentParser(description="RMS zero-dependency status board")
    ap.add_argument("--port", type=int, default=8501)
    ap.add_argument("--refresh", type=int, default=120)
    args = ap.parse_args(argv)
    H.refresh = args.refresh
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), H)
    print("RMS board on http://localhost:%d/  (Ctrl+C to stop)" % args.port, flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
