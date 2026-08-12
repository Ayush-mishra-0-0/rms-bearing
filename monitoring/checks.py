"""Index-safe, read-only SQL checks against the SLAM/RMS database.

The live telemetry feed is `Lotus_loco_process_signals_RDSOJson` (indexed on
`DeviceTime`). The legacy relational tables (`Lotus_loco_process_signals`,
`Locoprocessdata`, ...) are lagged/archived and only used for info.

Every query:
  - uses WITH (NOLOCK) (read-only, no blocking),
  - is bounded to a recent window so it can use an index, never a full scan,
  - treats dirty/future timestamps correctly (DeviceTime/FaultTime are known
    to contain garbage rows with years up to 2044).
"""
import os
from datetime import datetime

import pyodbc

from .config import settings


class CheckError(RuntimeError):
    pass


def connect():
    s = settings()
    if not s["db_server"] or not s["db_name"]:
        raise CheckError("DB_SERVER / DB_NAME not set in .env")
    cs = (
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s;"
        "TrustServerCertificate=yes;" % (s["db_server"], s["db_name"], s["db_user"], s["db_password"])
    )
    try:
        return pyodbc.connect(cs, timeout=s["query_timeout"])
    except Exception as e:  # pragma: no cover - depends on live DB
        raise CheckError("cannot connect to %s\\%s: %s" % (s["db_server"], s["db_name"], e))


def _fetch(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur.fetchone()


def _fetchall(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur.fetchall()


def server_now(conn):
    return _fetch(conn, "SELECT GETDATE()")[0]


# ---------------------------------------------------------------------------
# Watcher heartbeat checks (all < ~2s using indexes)
# ---------------------------------------------------------------------------

def telemetry_heartbeat(conn):
    """Live telemetry feed freshness + volume (indexed on DeviceTime)."""
    max_dt = _fetch(
        conn,
        "SELECT MAX(DeviceTime) FROM dbo.Lotus_loco_process_signals_RDSOJson "
        "WITH (NOLOCK) WHERE DeviceTime <= DATEADD(day, 1, GETDATE())",
    )[0]
    rows_24h = _fetch(
        conn,
        "SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) "
        "WHERE DeviceTime >= DATEADD(day, -1, GETDATE()) AND DeviceTime <= DATEADD(day, 1, GETDATE())",
    )[0]
    rows_recent = _fetch(
        conn,
        "SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) "
        "WHERE DeviceTime >= DATEADD(hour, -?, GETDATE()) AND DeviceTime <= DATEADD(day, 1, GETDATE())",
        (settings()["recent_window_h"],),
    )[0]
    return {"max_device_time": max_dt, "rows_24h": rows_24h, "rows_recent": rows_recent}


def fault_heartbeat(conn):
    """Legacy fault table is sparse but indexed on faulttime -> cheap heartbeat."""
    max_ft = _fetch(
        conn,
        "SELECT MAX(faulttime) FROM dbo.Lotus_LocoFaultData WITH (NOLOCK) "
        "WHERE faulttime <= GETDATE() AND faulttime >= DATEADD(day, -90, GETDATE())",
    )[0]
    rows_24h = _fetch(
        conn,
        "SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData WITH (NOLOCK) "
        "WHERE faulttime >= DATEADD(day, -1, GETDATE()) AND faulttime <= GETDATE()",
    )[0]
    return {"max_fault_time": max_ft, "rows_24h": rows_24h}


def heartbeat(conn):
    return {
        "server_now": server_now(conn),
        "telemetry": telemetry_heartbeat(conn),
        "faults": fault_heartbeat(conn),
    }


# ---------------------------------------------------------------------------
# Daily-report checks (slow; run once/day only)
# ---------------------------------------------------------------------------

def telemetry_7d_daily(conn):
    """Row count per day over the last 7 days (~20s)."""
    return [
        (r[0], r[1])
        for r in _fetchall(
            conn,
            "SELECT CONVERT(date, DeviceTime) d, COUNT_BIG(*) n "
            "FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) "
            "WHERE DeviceTime >= DATEADD(day, -7, GETDATE()) "
            "GROUP BY CONVERT(date, DeviceTime) ORDER BY d",
        )
    ]


def telemetry_active_locos_24h(conn):
    """Distinct active locos in last 24h (~4 min)."""
    return _fetch(
        conn,
        "SELECT COUNT(DISTINCT LocoId) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) "
        "WHERE DeviceTime >= DATEADD(day, -1, GETDATE())",
    )[0]


def fault_json_metrics(conn):
    """Richer fault metrics from the live JSON fault table (slow, no time index)."""
    s = settings()
    out = {}
    out["max_fault_time"] = _fetch(
        conn,
        "SELECT MAX(FaultTime) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) "
        "WHERE FaultTime <= DATEADD(day, 1, GETDATE())",
    )[0]
    out["max_created_on"] = _fetch(
        conn,
        "SELECT MAX(CreatedOn) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)",
    )[0]
    out["rows_24h"] = _fetch(
        conn,
        "SELECT COUNT_BIG(*) FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK) "
        "WHERE FaultTime >= DATEADD(day, -1, GETDATE()) AND FaultTime <= DATEADD(day, 1, GETDATE())",
    )[0]
    return out


def fault_legacy_7d(conn):
    """Daily clean fault counts from the indexed legacy table (fast)."""
    return [
        (r[0], r[1])
        for r in _fetchall(
            conn,
            "SELECT CONVERT(date, faulttime) d, COUNT_BIG(*) n "
            "FROM dbo.Lotus_LocoFaultData WITH (NOLOCK) "
            "WHERE faulttime >= DATEADD(day, -7, GETDATE()) AND faulttime <= GETDATE() "
            "GROUP BY CONVERT(date, faulttime) ORDER BY d",
        )
    ]


def rmsloco_map(conn):
    """Fitment roster summary (small lookup table)."""
    row = _fetch(
        conn,
        "SELECT COUNT_BIG(*) total, SUM(CASE WHEN RMSFlag = 'Y' THEN 1 ELSE 0 END) fitted "
        "FROM dbo.RMSLocoMap WITH (NOLOCK)",
    )
    return {"total": row[0], "fitted": row[1]}


def mirror_tables(conn):
    """Informational max timestamps of the legacy/staging tables."""
    out = {}
    for t, ts in (
        ("Locoprocessdata", "devicetime"),
        ("Lotus_loco_process_signals_5", "devicetime"),
        ("Lotus_loco_process_signals_sma", "devicetime"),
    ):
        try:
            out[t] = _fetch(
                conn,
                "SELECT MAX([%s]) FROM dbo.[%s] WITH (NOLOCK) WHERE [%s] <= DATEADD(day, 1, GETDATE())"
                % (ts, t, ts),
            )[0]
        except Exception:
            out[t] = None
    try:
        out["temptoday_fault"] = _fetch(
            conn,
            "SELECT MAX(LFDSlamRecordDate) FROM dbo.temptoday_fault WITH (NOLOCK)",
        )[0]
    except Exception:
        out["temptoday_fault"] = None
    return out
