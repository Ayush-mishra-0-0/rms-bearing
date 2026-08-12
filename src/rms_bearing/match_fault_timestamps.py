"""Produce reviewable RMS-fault timestamp candidates for Owner-report events."""
from __future__ import annotations
import argparse, csv, os
from pathlib import Path
from dotenv import load_dotenv

def main() -> None:
    load_dotenv()
    p=argparse.ArgumentParser(); p.add_argument('--registry',type=Path,default=Path('data/processed/ground_truth_failure_registry.csv')); p.add_argument('--output',type=Path,default=Path('data/processed/fault_time_reconciliation_candidates.csv')); args=p.parse_args()
    import pyodbc
    rows=list(csv.DictReader(args.registry.open(newline='',encoding='utf-8-sig')))
    c=pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.environ['DB_SERVER']};DATABASE={os.environ['DB_NAME']};UID={os.environ['DB_USERNAME']};PWD={os.environ['DB_PASSWORD']};TrustServerCertificate=yes;")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',newline='',encoding='utf-8') as out:
        w=csv.writer(out); w.writerow(['FailureID','Loco','FailureDate','FaultTime','FaultText','FaultCode','Processor','Vendor'])
        cur=c.cursor(); c.timeout=60
        for event in rows:
            day=event['Date'].split('/'); start=f'{day[2]}-{day[1]}-{day[0]}'
            cur.execute("""SELECT LFDId,locoid,faulttime,FaultText,errorinfo2,processorid,Vendor FROM dbo.Lotus_LocoFaultData WITH (NOLOCK)
WHERE locoid=? AND faulttime>=DATEADD(day,-1,?) AND faulttime<DATEADD(day,2,?) ORDER BY faulttime""",event['Loco'],start,start)
            for _,loco,faulttime,text,code,processor,vendor in cur.fetchall():
                w.writerow([event['FailureID'],loco,event['Date'],faulttime,text,code,processor,vendor])
    c.close()
if __name__=='__main__': main()
