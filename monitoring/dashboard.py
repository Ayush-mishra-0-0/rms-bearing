"""RMS data-flow board (Streamlit).

One status, one KPI row, one main chart — no duplicated panels.
Data paths (sidebar -> Source): Live DB -> Prometheus -> watcher snapshots
(`reports/history.csv`) -> daily backfill chart (`reports/telemetry_daily.csv`).
Everything degrades gracefully, so the board also runs on Streamlit Cloud
where the private DB is unreachable.

Local:
    streamlit run monitoring/dashboard.py
Cloud:
    repo + main file monitoring/dashboard.py; optional PROM_URL secret.
"""
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root (also on Cloud)

import altair as alt
import pandas as pd
import streamlit as st

from monitoring import checks
from monitoring.config import REPORTS_DIR, settings
from monitoring.state import baseline_medians, estimated_skew, history_tail, load_state, recent_alert_log

STALL_ROWS = 1000  # daily rows below this count as stalled (collapse days have <= 66)


def _fmt(dt):
    if dt is None or dt == "":
        return "never"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _parse(dt):
    if dt is None or dt == "":
        return None
    if isinstance(dt, datetime):
        return dt
    try:
        return datetime.fromisoformat(dt)
    except ValueError:
        return None


@st.cache_data(ttl=60)  # fast heartbeat queries: refresh every minute
def live_heartbeat():
    try:
        conn = checks.connect()
        try:
            return checks.heartbeat(conn), None
        finally:
            conn.close()
    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=300)  # watcher runs every 5 min; no need to re-read more often
def load_snapshots():
    rows = history_tail(500)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    for c in ("telemetry_rows_24h", "telemetry_rows_recent", "fault_rows_24h"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["ts"] = pd.to_datetime(df.get("ts"), errors="coerce")
    return df.sort_values("ts").reset_index(drop=True)


@st.cache_data(ttl=3600)  # slow-changing files: backfills + daily report output
def load_daily_csv(name, date_col):
    p = REPORTS_DIR / name
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, parse_dates=[date_col])
    return df.sort_values(date_col).reset_index(drop=True)


@st.cache_data(ttl=300)
def prom_instant(base, query, timeout=8):
    q = urllib.parse.urlencode({"query": query, "time": time.time()})
    req = urllib.request.Request(base.rstrip("/") + "/api/v1/query?" + q,
                                 headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        import json
        res = json.loads(r.read().decode("utf-8")).get("data", {}).get("result", [])
    if not res:
        raise RuntimeError("no data for %s" % query)
    return float(res[0]["value"][1])


def resolve_status(source, prom_url, cfg, skew):
    """Single source of truth -> (kpis, source_label, note). Never raises."""
    if source in ("Auto", "Live DB"):
        m, _ = live_heartbeat()
        if m is not None:
            now, tele, fa = m["server_now"], m["telemetry"], m["faults"]
            lag = ((now - tele["max_device_time"]).total_seconds() + skew) / 60 \
                if tele["max_device_time"] else float("inf")
            fage = ((now - fa["max_fault_time"]).total_seconds() / 60) \
                if fa["max_fault_time"] else float("inf")
            return {"tele_max": tele["max_device_time"], "lag_min": lag,
                    "rows_24h": tele["rows_24h"], "rows_recent": tele["rows_recent"],
                    "fault_max": fa["max_fault_time"], "fault_age_min": fage,
                    "fault_24h": fa["rows_24h"], "server_now": now}, "Live DB", ""
    if source in ("Auto", "Prometheus"):
        try:
            k = {"tele_max": None, "server_now": None, "rows_recent": None,
                 "lag_min": prom_instant(prom_url, "rms_telemetry_lag_minutes"),
                 "rows_24h": prom_instant(prom_url, "rms_telemetry_rows_24h"),
                 "fault_age_min": prom_instant(prom_url, "rms_fault_age_minutes"),
                 "fault_max": None,
                 "fault_24h": prom_instant(prom_url, "rms_fault_rows_24h")}
            return k, "Prometheus", ""
        except Exception as e:
            note = "Prometheus unreachable (%s). " % str(e)[:100]
            if source == "Prometheus":
                return None, "Prometheus", note
        else:
            note = ""
    else:
        note = ""
    snap = load_snapshots()
    if not snap.empty:
        last = snap.iloc[-1]
        tmax, fmax = _parse(last.get("telemetry_max_dt")), _parse(last.get("fault_max_ft"))
        now = datetime.now()
        lag = ((now - tmax).total_seconds() + skew) / 60 if tmax else float("inf")
        fage = ((now - fmax).total_seconds() / 60) if fmax else float("inf")
        return {"tele_max": tmax, "lag_min": lag, "rows_24h": last.get("telemetry_rows_24h"),
                "rows_recent": last.get("telemetry_rows_recent"), "fault_max": fmax,
                "fault_age_min": fage, "fault_24h": last.get("fault_rows_24h"),
                "server_now": None}, "Snapshot cache", \
            note + "Showing last watcher run %s." % _fmt(last.get("ts"))
    return None, "none", note + "No live source and no snapshots yet."


def main():
    st.set_page_config(page_title="RMS Data-Flow", layout="wide")
    cfg = settings()
    skew = estimated_skew(load_state())

    try:
        prom_default = os.getenv("PROM_URL") or st.secrets.get("PROM_URL", "") or "http://localhost:9090"
    except Exception:
        prom_default = os.getenv("PROM_URL", "http://localhost:9090")

    st.sidebar.title("RMS monitor")
    source = st.sidebar.selectbox("Source", ["Auto", "Live DB", "Prometheus", "Snapshot cache"])
    prom_url = ""
    if source in ("Auto", "Prometheus"):
        prom_url = st.sidebar.text_input("Prometheus URL", prom_default)
    refresh = st.sidebar.slider("Refresh (s)", 30, 3600, 3600, step=30)
    st.sidebar.caption("Page reloads on this timer, but slow data is cached: "
                       "live 1 min · snapshots 5 min · daily files 1 h.")
    loco = load_daily_csv("loco_daily.csv", "day")
    st.sidebar.divider()
    st.sidebar.subheader("Locos")
    if not loco.empty:
        last = loco.iloc[-1]
        fitted = int(last["fitted"]) if pd.notna(last["fitted"]) else 0
        active = int(last["active_locos"]) if pd.notna(last["active_locos"]) else 0
        cov = (100.0 * active / fitted) if fitted else 0
        st.sidebar.metric("Active locos", "%d" % active, "of %d fitted" % fitted)
        st.sidebar.caption("Coverage **%.0f%%** · day %s" % (cov, str(last["day"])[:10]))
    else:
        st.sidebar.caption("No loco data yet.")
    with st.sidebar.expander("Thresholds"):
        st.code("TELEMETRY_STALL_MIN=%d\nFAULT_STALL_MIN=%d\nVOLUME_DROP_PCT=%.0f"
                % (cfg["telemetry_stall_min"], cfg["fault_stall_min"], cfg["volume_drop_pct"]))
    st.query_params["rerun"] = refresh
    st.markdown("<meta http-equiv='refresh' content='%d'>" % refresh, unsafe_allow_html=True)

    kpis, src_label, note = resolve_status(source, prom_url, cfg, skew)
    base = baseline_medians()

    st.title("RMS data flow")
    st.caption("`Lotus_loco_process_signals_RDSOJson` (telemetry) · `Lotus_LocoFaultData` (faults) · "
               "source: **%s**" % src_label)
    if note:
        st.info(note)
    if kpis is None:
        st.warning("Nothing to show — run `python -m monitoring.watch` once to seed a snapshot.")
        return

    rows_24h = kpis["rows_24h"] or 0
    stalled = rows_24h < STALL_ROWS or kpis["lag_min"] > cfg["telemetry_stall_min"]
    if stalled:
        st.error("**STOPPED** — last telemetry row **%s** (%.1f h ago), **%s rows / 24h**. "
                 "Faults still flowing, so the DB is up; the break is upstream."
                 % (_fmt(kpis["tele_max"]), kpis["lag_min"] / 60, rows_24h))
    else:
        st.success("**FLOWING** — telemetry lag %.0f min · %s rows / 24h · faults %.1f h old."
                   % (kpis["lag_min"], rows_24h, kpis["fault_age_min"] / 60))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Telemetry lag", "%.0f min" % kpis["lag_min"], _fmt(kpis["tele_max"]))
    c2.metric("Rows / 24h", "%d" % rows_24h,
              ("baseline %.0f" % base["telemetry_rows_24h"]) if base.get("telemetry_rows_24h") else None)
    c3.metric("Fault age", "%.1f h" % (kpis["fault_age_min"] / 60), _fmt(kpis["fault_max"]))
    c4.metric("Faults / 24h", "%s" % (kpis["fault_24h"] if kpis["fault_24h"] is not None else "?"))

    st.subheader("Telemetry volume by day")
    snap = load_snapshots()
    ddf = load_daily_csv("telemetry_daily.csv", "day")
    if not ddf.empty:
        st.altair_chart(
            alt.Chart(ddf).mark_bar().encode(
                x=alt.X("day:T", title="Day"), y=alt.Y("rows:Q", title="Rows"),
                color=alt.condition("datum.rows < %d" % STALL_ROWS,
                                    alt.value("#f43f5e"), alt.value("#38bdf8")),
                tooltip=[alt.Tooltip("day:T", title="Day"), alt.Tooltip("rows:Q", title="Rows")],
            ).properties(height=320), use_container_width=True)
        st.caption("Straight from the DB — red days are the stall (collapsed Sep 2, last row Sep 5).")
    elif not snap.empty:
        st.line_chart(snap, x="ts", y="telemetry_rows_24h")

    if not snap.empty and snap["fault_rows_24h"].notna().any():
        st.subheader("Fault flow")
        st.altair_chart(
            alt.Chart(snap).mark_line(point=True).encode(
                x=alt.X("ts:T", title="Watcher run"), y=alt.Y("fault_rows_24h:Q", title="Faults / 24h"),
                tooltip=[alt.Tooltip("ts:T", title="Run"), alt.Tooltip("fault_rows_24h:Q", title="Faults")],
            ).properties(height=200), use_container_width=True)

    if not loco.empty:
        st.subheader("Active locos by day")
        half = int(loco["fitted"].iloc[-1] // 2) if pd.notna(loco["fitted"].iloc[-1]) else 500
        st.altair_chart(
            alt.Chart(loco).mark_bar().encode(
                x=alt.X("day:T", title="Day"), y=alt.Y("active_locos:Q", title="Locos"),
                color=alt.condition("datum.active_locos < %d" % half,
                                    alt.value("#f43f5e"), alt.value("#38bdf8")),
                tooltip=[alt.Tooltip("day:T", title="Day"),
                         alt.Tooltip("active_locos:Q", title="Active"),
                         alt.Tooltip("fitted:Q", title="Fitted")],
            ).properties(height=240), use_container_width=True)
        st.caption("Distinct locos sending telemetry per day vs %d fitted (RMSLocoMap). "
                   "Grows daily via the 08:00 full report." % loco["fitted"].iloc[-1])

    with st.expander("Incidents, alerts, latest report"):
        state = load_state()
        bad = [(k, v) for k, v in state.get("checks", {}).items() if v.get("status") != "ok"]
        if bad:
            st.table([{"check": k, "severity": v.get("severity", "-"),
                       "since": _fmt(v.get("since"))} for k, v in bad])
        else:
            st.caption("No active incidents recorded.")
        alerts = recent_alert_log(10)
        st.code("\n".join(alerts[-10:]) if alerts else "(no alerts)")
        md = sorted(REPORTS_DIR.glob("rms_report_*.md"))
        if md:
            st.markdown(md[-1].read_text(encoding="utf-8")[:5000])


if __name__ == "__main__":
    main()
