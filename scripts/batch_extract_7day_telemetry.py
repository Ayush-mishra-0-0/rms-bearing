"""BATCH 2 - 7-day telemetry availability + extraction per fault candidate.

For each fault (loco + fault date) builds the window [D-7 00:00, D+1 00:00)
and counts telemetry rows per day in BOTH feeds (each count is an indexed
seek, so this is fast):
  * dbo.Lotus_loco_process_signals            (legacy feed, to 08/07/2026, locoid/devicetime)
  * dbo.Lotus_loco_process_signals_RDSOJson   (new feed, LocoId/DeviceTime)

No hardcoded cutover date: days with data win, outage days show 0.

Usage (from rms-bearing root):
  # availability only (default, fast)
  python scripts/batch_extract_7day_telemetry.py --input data/manifests/fault_candidates_2025_2026.csv
  python scripts/batch_extract_7day_telemetry.py --loco 42728 --date 08/08/2026
  python scripts/batch_extract_7day_telemetry.py --fallback30
  # full row extraction for usable windows only
  python scripts/batch_extract_7day_telemetry.py --input ... --extract

Input CSV columns: loco,fault_date  (fault_date DD/MM/YYYY or YYYY-MM-DD;
extra columns failure_id,evidence,source are carried through when present.)

Output:
  data/manifests/telemetry_7day_availability.csv  (one row per loco/day + verdict)
  data/raw/batch_7day/<loco>_<date>_legacy.csv | _rdso.csv   (only with --extract)

Verdict per loco: USABLE (>=50000 rows/7d) | SPARSE (>0 rows) | EMPTY (0 rows).
"""
from __future__ import annotations
import argparse, csv, os, sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

USABLE_THRESHOLD = 50000

LEGACY_DAY = """SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals WITH (NOLOCK)
WHERE locoid=? AND devicetime>=? AND devicetime<?"""
RDSO_DAY = """SELECT COUNT_BIG(*) FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK)
WHERE LocoId=? AND DeviceTime>=? AND DeviceTime<?"""


def parse_date(s: str) -> datetime:
    s = s.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:10] if fmt != "%Y-%m-%d %H:%M:%S" else s[:19], fmt)
        except ValueError:
            continue
    raise ValueError(f"bad date: {s}")


def get_conn(a) -> "conn":
    import pyodbc
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    server = a.server or os.getenv("DB_SERVER")
    database = a.database or os.getenv("DB_NAME")
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={server};DATABASE={database};"
        f"UID={os.getenv('DB_USERNAME')};PWD={os.getenv('DB_PASSWORD')};"
        "TrustServerCertificate=yes;",
        timeout=30)
    conn.timeout = a.query_timeout
    return conn


def load_targets(a) -> list[dict]:
    if a.loco and a.date:
        return [{"loco": a.loco, "fault_date": a.date, "failure_id": "", "evidence": "", "source": "manual"}]
    if a.fallback30:
        p = ROOT / "data/manifests/fallback_30_locos_2024.csv"
        if not p.exists():
            sys.exit("fallback file missing - run scripts/make_fallback_30.py first")
        rows = list(csv.DictReader(p.open(encoding="utf-8-sig")))
        return [{"loco": r["loco"], "fault_date": r["fault_date"], "failure_id": r.get("failure_id", ""),
                 "evidence": "", "source": "fallback30"} for r in rows]
    rows = list(csv.DictReader(Path(a.input).open(encoding="utf-8-sig")))
    out = []
    for r in rows:
        loco = (r.get("loco") or r.get("Loco") or "").strip()
        fd = (r.get("fault_date") or r.get("FailureDate") or r.get("faulttime") or "").strip()
        if loco and fd:
            out.append({"loco": loco, "fault_date": fd, "failure_id": r.get("failure_id", r.get("FailureID", "")),
                        "evidence": r.get("evidence", ""), "source": r.get("source", "")})
    # dedupe, keep first
    seen, uniq = set(), []
    for t in out:
        k = (t["loco"], t["fault_date"][:10])
        if k not in seen:
            seen.add(k); uniq.append(t)
    return uniq


def main() -> None:
    p = argparse.ArgumentParser(description="7-day telemetry availability + extraction.")
    p.add_argument("--input", default="data/manifests/fault_candidates_2025_2026.csv")
    p.add_argument("--loco", default="")
    p.add_argument("--date", default="")
    p.add_argument("--fallback30", action="store_true")
    p.add_argument("--days-before", type=int, default=7)
    p.add_argument("--days-after", type=int, default=1)
    p.add_argument("--extract", action="store_true", help="dump full row CSVs for non-empty windows")
    p.add_argument("--out", default="data/manifests/telemetry_7day_availability.csv")
    p.add_argument("--server", default="", help="override DB server (for the post-Jul-2026 database)")
    p.add_argument("--database", default="", help="override DB name (for the post-Jul-2026 database)")
    p.add_argument("--query-timeout", type=int, default=600)
    p.add_argument("--tables", default="legacy,rdso",
                   help="comma list: legacy,rdso (use legacy only for a fast test)")
    a = p.parse_args()
    tables = [s.strip() for s in a.tables.split(",")]

    targets = load_targets(a)
    print(f"targets: {len(targets)}", flush=True)
    avail_p = Path(a.out)
    avail_p.parent.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    if avail_p.exists():
        with avail_p.open(encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if (r.get("day_offset") or "").strip() == "verdict":
                    done.add((r["loco"], (r.get("fault_date") or "")[:10]))

    conn = get_conn(a)
    cur = conn.cursor()
    new_file = not avail_p.exists()
    af = avail_p.open("a", newline="", encoding="utf-8")
    aw = csv.DictWriter(af, fieldnames=["loco", "failure_id", "fault_date", "day_offset", "day",
                                        "legacy_rows", "rdso_rows", "day_total", "evidence", "source"])
    if new_file:
        aw.writeheader()

    for t in targets:
        key = (t["loco"], t["fault_date"][:10])
        if key in done:
            print(f"skip {t['loco']} {t['fault_date']} (done)", flush=True)
            continue
        try:
            fd = parse_date(t["fault_date"])
        except ValueError as e:  # noqa: BLE001
            print(f"skip: {e}", flush=True)
            continue
        w0 = (fd - timedelta(days=a.days_before)).strftime("%Y-%m-%d")
        tot_leg = tot_rdso = 0
        for i in range(a.days_before + a.days_after):
            day = (fd - timedelta(days=a.days_before) + timedelta(days=i)).strftime("%Y-%m-%d")
            nxt = (fd - timedelta(days=a.days_before) + timedelta(days=i + 1)).strftime("%Y-%m-%d")
            nl = nr = 0
            if "legacy" in tables:
                try:
                    cur.execute(LEGACY_DAY, t["loco"], day, nxt)
                    nl = int(cur.fetchone()[0])
                except Exception:  # noqa: BLE001
                    nl = -1
            if "rdso" in tables:
                try:
                    cur.execute(RDSO_DAY, t["loco"], day, nxt)
                    nr = int(cur.fetchone()[0])
                except Exception:  # noqa: BLE001
                    nr = -1
            nl = max(nl, 0); nr = max(nr, 0)
            tot_leg += nl; tot_rdso += nr
            aw.writerow({"loco": t["loco"], "failure_id": t["failure_id"], "fault_date": t["fault_date"],
                         "day_offset": f"D-{a.days_before - i}", "day": day, "legacy_rows": nl,
                         "rdso_rows": nr, "day_total": nl + nr,
                         "evidence": t["evidence"], "source": t["source"]})
        total = tot_leg + tot_rdso
        verdict = "verdict:" + ("USABLE" if total >= USABLE_THRESHOLD else ("SPARSE" if total > 0 else "EMPTY"))
        aw.writerow({"loco": t["loco"], "failure_id": t["failure_id"], "fault_date": t["fault_date"],
                     "day_offset": "verdict", "day": f"{w0}..{fd.strftime('%Y-%m-%d')}",
                     "legacy_rows": tot_leg, "rdso_rows": tot_rdso, "day_total": total,
                     "evidence": verdict, "source": t["source"]})
        af.flush()
        print(f"{t['loco']} {t['fault_date']}: legacy={tot_leg} rdso={tot_rdso} total={total} -> {verdict}", flush=True)
        if a.extract and total > 0:
            extract_window(cur, t, fd, a)
    af.close(); conn.close()
    print(f"DONE -> {avail_p}")


def extract_window(cur, t: dict, fd: datetime, a) -> None:
    dest = ROOT / "data/raw/batch_7day"
    dest.mkdir(parents=True, exist_ok=True)
    w0 = fd - timedelta(days=a.days_before)
    w1 = fd + timedelta(days=a.days_after)
    tag = f"{t['loco']}_{fd.strftime('%Y%m%d')}"
    try:
        cur.execute("SELECT * FROM dbo.Lotus_loco_process_signals WITH (NOLOCK) WHERE locoid=? AND devicetime>=? AND devicetime<?",
                    t["loco"], w0.strftime("%Y-%m-%d"), w1.strftime("%Y-%m-%d"))
        cols = [d[0] for d in cur.description]
        path = dest / f"{tag}_legacy.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(cols)
            while True:
                batch = cur.fetchmany(5000)
                if not batch:
                    break
                w.writerows(batch)
        print(f"  wrote {path}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"  legacy extract failed: {str(e)[:120]}", flush=True)
    try:
        cur.execute("SELECT Id, LocoId, DeviceTime, Vendor, JsonPayload FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK) WHERE LocoId=? AND DeviceTime>=? AND DeviceTime<?",
                    t["loco"], w0.strftime("%Y-%m-%d"), w1.strftime("%Y-%m-%d"))
        path = dest / f"{tag}_rdso.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Id", "LocoId", "DeviceTime", "Vendor", "JsonPayload"])
            while True:
                batch = cur.fetchmany(2000)
                if not batch:
                    break
                w.writerows(batch)
        print(f"  wrote {path}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"  rdso extract failed: {str(e)[:120]}", flush=True)


if __name__ == "__main__":
    main()
