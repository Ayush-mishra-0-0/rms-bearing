"""Batch telemetry health report: availability only, never extracts telemetry rows.

Strategy (informed by the 30751 forensic audit):
  * Lotus_loco_process_signals (~5.3B rows) has a (locoid, devicetime) index, so
    per-window aggregates are milliseconds.  A DISTINCT-locoid probe on it is a
    full scan and times out, so it is skipped when the table is indexed.
  * The alternate tables are unindexed heaps; per-window aggregates would each be
    a full scan.  They are probed once via DISTINCT locoid; if they hold none of
    the manifest locomotives they are reported empty without per-window work.
"""
from __future__ import annotations
import argparse, csv, os
from pathlib import Path
from dotenv import load_dotenv

TABLES=('dbo.Lotus_loco_process_signals','dbo.Locoprocessdata','dbo.Lotus_loco_process_signals_5','dbo.Lotus_loco_process_signals_sma')
def main() -> None:
    load_dotenv()
    p=argparse.ArgumentParser(); p.add_argument('--manifest',type=Path,default=Path('data/manifests/telemetry_extraction_manifest.csv')); p.add_argument('--output',type=Path,default=Path('data/manifests/telemetry_health_manifest.csv')); p.add_argument('--timeout',type=int,default=120); args=p.parse_args()
    events=list(csv.DictReader(args.manifest.open(newline='',encoding='utf-8-sig')))
    want_loco=set(e['Loco'] for e in events)
    import pyodbc
    c=pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.environ['DB_SERVER']};DATABASE={os.environ['DB_NAME']};UID={os.environ['DB_USERNAME']};PWD={os.environ['DB_PASSWORD']};TrustServerCertificate=yes;")
    c.timeout=args.timeout
    cur=c.cursor()
    results=[]
    for table in TABLES:
        cur.execute(f"SELECT COUNT(*) FROM sys.indexes WHERE object_id=OBJECT_ID('{table}') AND type=2 AND name LIKE '%Loco%'")
        has_loco_index=cur.fetchone()[0]>0
        present=None
        if not has_loco_index:
            cur.execute(f"SELECT DISTINCT locoid FROM {table} WITH (NOLOCK)")
            present=set(str(r[0]) for r in cur.fetchall())
            hit=sorted(l for l in want_loco if l in present)
            print(f"{table}: unindexed heap, {len(present)} distinct locos, {len(hit)} manifest overlap: {hit}",file=__import__('sys').stderr)
            if not hit:
                for e in events:
                    results.append({'FailureID':e['FailureID'],'Loco':e['Loco'],'WindowName':e['Window'],'WindowStart':e['WindowStart'],'WindowEnd':e['WindowEnd'],'TimestampPrecision':e['TimestampPrecision'],'telemetry_table':table,'samples':0,'earliest_timestamp':'','latest_timestamp':'','vendor':'','missing_pct':''})
                continue
        for e in events:
            if present is not None and e['Loco'] not in present:
                results.append({'FailureID':e['FailureID'],'Loco':e['Loco'],'WindowName':e['Window'],'WindowStart':e['WindowStart'],'WindowEnd':e['WindowEnd'],'TimestampPrecision':e['TimestampPrecision'],'telemetry_table':table,'samples':0,'earliest_timestamp':'','latest_timestamp':'','vendor':'','missing_pct':''})
                continue
            q=f"""SELECT COUNT_BIG(t.LPSDId),MIN(t.devicetime),MAX(t.devicetime),MAX(t.Vendor),
CAST(100.0*SUM(CASE WHEN t.LPSDId IS NOT NULL AND (t.xtempmotor1_1 IS NULL OR t.xtempmotor2_1 IS NULL OR t.xtempmotor3_1 IS NULL OR t.xtempmotor1_2 IS NULL OR t.xtempmotor2_2 IS NULL OR t.xtempmotor3_2 IS NULL OR t.xspeedloco IS NULL) THEN 1 ELSE 0 END)/NULLIF(COUNT_BIG(t.LPSDId),0) AS decimal(6,2))
FROM {table} t WITH (NOLOCK) WHERE t.locoid=? AND t.devicetime>=? AND t.devicetime<?
OPTION (RECOMPILE)"""
            cur.execute(q,e['Loco'],e['WindowStart'],e['WindowEnd'])
            samples,first_ts,last_ts,vendor,missing=cur.fetchone()
            results.append({'FailureID':e['FailureID'],'Loco':e['Loco'],'WindowName':e['Window'],'WindowStart':e['WindowStart'],'WindowEnd':e['WindowEnd'],'TimestampPrecision':e['TimestampPrecision'],'telemetry_table':table,'samples':samples,'earliest_timestamp':first_ts,'latest_timestamp':last_ts,'vendor':vendor,'missing_pct':missing})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fields=['FailureID','Loco','WindowName','WindowStart','WindowEnd','TimestampPrecision','telemetry_table','samples','earliest_timestamp','latest_timestamp','vendor','missing_pct']
    with args.output.open('w',newline='',encoding='utf-8') as out: w=csv.DictWriter(out,fieldnames=fields); w.writeheader(); w.writerows(results)
    c.close()
    print(f"Wrote {len(results)} rows to {args.output}")
if __name__=='__main__': main()
