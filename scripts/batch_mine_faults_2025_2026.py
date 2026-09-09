"""BATCH 1 - Extensive fault mining for 2025/2026 bearing-like events.

Searches the RMS fault tables day-by-day (a full LIKE scan is too slow to run
in one go) and collects candidate axle-bearing fault events.

Sources (all read-only, WITH (NOLOCK)):
  * dbo.Lotus_LocoFaultData            (legacy feed, FaultText column)
  * dbo.Lotus_LocoFaultData_RDSOJson   (new feed from ~Jul-2026, fault text inside JsonPayload)
  * dbo.temptoday_fault                (small staging table, one-shot scan)

Resume: keeps a checkpoint file of finished days; re-running continues where
it stopped. Timeouts are logged as PENDING and retried on the next run.

Usage (from rms-bearing root):
  python scripts/batch_mine_faults_2025_2026.py --from 2025-01-01 --to 2026-09-09
  python scripts/batch_mine_faults_2025_2026.py --from 2026-08-08 --to 2026-08-10 --sources legacy
  python scripts/batch_mine_faults_2025_2026.py --help

Output:
  data/manifests/fault_candidates_2025_2026.csv  (loco,faulttime,code,text,evidence,source)
  data/manifests/fault_mine_log.csv              (per-day status + timings)
"""
from __future__ import annotations
import argparse, csv, os, sys, time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

KEYWORDS = ["seiz", "bearing", "locked axle", "axle lock", "labyrinth", "pinion cut"]

LEGACY_SQL = """SELECT faulttime, locoid, errorinfo2, FaultText
FROM dbo.Lotus_LocoFaultData WITH (NOLOCK)
WHERE faulttime>=? AND faulttime<? AND ({like})
ORDER BY faulttime"""

RDSO_SQL = """SELECT FaultTime, LocoId, Vendor, JsonPayload
FROM dbo.Lotus_LocoFaultData_RDSOJson WITH (NOLOCK)
WHERE FaultTime>=? AND FaultTime<? AND ({like})
ORDER BY FaultTime"""

STAGING_SQL = """SELECT faulttime, locoid, errorinfo2, FaultText
FROM dbo.temptoday_fault WITH (NOLOCK) WHERE ({like}) ORDER BY faulttime"""


def evidence_of(text: str) -> str:
    t = (text or "").lower()
    if "seiz" in t or "locked axle" in t or "axle lock" in t or "pinion cut" in t:
        return "PROBABLE"
    if any(k in t for k in ("axle", "bearing", "traction motor", "gear", "pinion",
                            "wheel heating", "hot axle", "smoke", "oil leak", "labyrinth")):
        return "POSSIBLE"
    return "KEYWORD_ONLY"


def get_conn(day_timeout: int, server: str = "", database: str = ""):
    import pyodbc
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    server = server or os.getenv("DB_SERVER")
    database = database or os.getenv("DB_NAME")
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};DATABASE={database};"
        f"UID={os.getenv('DB_USERNAME')};PWD={os.getenv('DB_PASSWORD')};"
        "TrustServerCertificate=yes;",
        timeout=30)
    conn.timeout = day_timeout
    return conn


def like_clause(col: str) -> str:
    return " OR ".join(f"{col} LIKE '%{k}%'" for k in KEYWORDS)


def main() -> None:
    p = argparse.ArgumentParser(description="Day-chunked 2025/2026 bearing-fault mining.")
    p.add_argument("--from", dest="dfrom", default="2025-01-01")
    p.add_argument("--to", dest="dto", default="2026-09-09")
    p.add_argument("--sources", default="legacy,rdso,staging",
                   help="comma list: legacy,rdso,staging")
    p.add_argument("--out", default="data/manifests/fault_candidates_2025_2026.csv")
    p.add_argument("--log", default="data/manifests/fault_mine_log.csv")
    p.add_argument("--ckpt", default="data/manifests/fault_mine_ckpt.txt")
    p.add_argument("--day-timeout", type=int, default=600)
    p.add_argument("--server", default="", help="override DB server")
    p.add_argument("--database", default="", help="override DB name")
    a = p.parse_args()

    d0 = datetime.strptime(a.dfrom, "%Y-%m-%d")
    d1 = datetime.strptime(a.dto, "%Y-%m-%d")
    sources = [s.strip() for s in a.sources.split(",")]
    out_p, log_p, ckpt_p = Path(a.out), Path(a.log), Path(a.ckpt)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    done: set[str] = set()
    if ckpt_p.exists():
        done = set(x.strip() for x in ckpt_p.read_text().splitlines() if x.strip())

    if not out_p.exists():
        with out_p.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=["fault_date", "loco", "faulttime", "code",
                                          "text", "evidence", "source"]).writeheader()
    log_new = not log_p.exists()
    logf = log_p.open("a", newline="", encoding="utf-8")
    logw = csv.DictWriter(logf, fieldnames=["day", "source", "status", "hits", "seconds", "note"])
    if log_new:
        logw.writeheader()

    conn = get_conn(a.day_timeout, a.server, a.database)
    cur = conn.cursor()
    legacy_like, rdso_like, staging_like = like_clause("FaultText"), like_clause("JsonPayload"), like_clause("FaultText")

    # one-shot staging table
    if "staging" in sources and "STAGING" not in done:
        t = time.time()
        try:
            cur.execute(STAGING_SQL.format(like=staging_like))
            n = write_rows(cur, out_p, "temptoday_fault")
            logw.writerow({"day": "STAGING", "source": "temptoday_fault", "status": "OK",
                           "hits": n, "seconds": round(time.time() - t, 1), "note": ""})
            done.add("STAGING")
        except Exception as e:  # noqa: BLE001
            logw.writerow({"day": "STAGING", "source": "temptoday_fault", "status": "ERROR",
                           "hits": 0, "seconds": round(time.time() - t, 1), "note": str(e)[:160]})
        logf.flush(); save_ckpt(ckpt_p, done)

    day = d0
    while day <= d1:
        ds = day.strftime("%Y-%m-%d")
        nxt = (day + timedelta(days=1)).strftime("%Y-%m-%d")
        for src in sources:
            if src == "staging":
                continue
            key = f"{ds}|{src}"
            if key in done:
                continue
            t = time.time()
            try:
                if src == "legacy":
                    cur.execute(LEGACY_SQL.format(like=legacy_like), ds, nxt)
                    n = write_rows(cur, out_p, "Lotus_LocoFaultData")
                elif src == "rdso":
                    cur.execute(RDSO_SQL.format(like=rdso_like), ds, nxt)
                    n = write_rows(cur, out_p, "Lotus_LocoFaultData_RDSOJson")
                else:
                    raise ValueError(f"unknown source {src}")
                logw.writerow({"day": ds, "source": src, "status": "OK", "hits": n,
                               "seconds": round(time.time() - t, 1), "note": ""})
                done.add(key)
                print(f"{ds} {src}: OK hits={n} ({time.time()-t:.0f}s)", flush=True)
            except Exception as e:  # noqa: BLE001 - log timeouts, keep going
                logw.writerow({"day": ds, "source": src, "status": "PENDING", "hits": 0,
                               "seconds": round(time.time() - t, 1), "note": str(e)[:160]})
                print(f"{ds} {src}: PENDING ({str(e)[:80]})", flush=True)
            logf.flush(); save_ckpt(ckpt_p, done)
        day += timedelta(days=1)
    logf.close()
    conn.close()
    print(f"DONE. candidates -> {out_p} | log -> {log_p}")


def write_rows(cur, out_p: Path, source: str) -> int:
    n = 0
    with out_p.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fault_date", "loco", "faulttime", "code",
                                          "text", "evidence", "source"])
        for ft, loco, code, text in cur.fetchall():
            if source == "Lotus_LocoFaultData_RDSOJson":
                import json
                try:
                    obj = json.loads(text or "{}")
                except Exception:  # noqa: BLE001
                    obj = {}
                code = obj.get("errorinfo2", "")
                text = obj.get("faulttext", "") or obj.get("FaultText", "") or (text or "")[:500]
                ft = obj.get("faulttime", "") or (str(ft)[:19] if ft else "")
            fts = str(ft)[:19] if ft else ""
            w.writerow({"fault_date": fts[:10], "loco": str(loco or "").strip(),
                        "faulttime": fts, "code": str(code or ""),
                        "text": str(text or "")[:500],
                        "evidence": evidence_of(str(text or "")), "source": source})
            n += 1
    return n


def save_ckpt(ckpt_p: Path, done: set[str]) -> None:
    ckpt_p.write_text("\n".join(sorted(done)) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
