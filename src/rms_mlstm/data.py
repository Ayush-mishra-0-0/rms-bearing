"""Read-only DB extraction. Never writes to DB. Aggregates are indexed (locoid, devicetime)."""
from __future__ import annotations
import os
from dotenv import load_dotenv

WINDOW_COLS = ("locoid,devicetime,Vendor,latitude,longitude,gpsspeed,xspeedloco,"
 "xiprim_1,xuprim_1,ltedemand,lbedemand,mtrcctract1,mvcb_on,"
 "bbur1_off,bbur2_off,bbur3_off,bstb1_off,bstb2_off,bflg1_off,bflg2_off,"
 "bur1_opcurrent,bur2_opcurrent,bur3_opcurrent,"
 "bg1tm1_ipvoltage,bg1tm2_ipvoltage,bg1tm3_ipvoltage,bg2tm1_ipvoltage,bg2tm2_ipvoltage,bg2tm3_ipvoltage,"
 "sr1_ipvoltage,sr2_ipvoltage,faultnum,"
 "xtempmotor1_1,xtempmotor2_1,xtempmotor3_1,xtempmotor1_2,xtempmotor2_2,xtempmotor3_2")

def fetch_window(loco: str, start: str, end: str, table: str, timeout: int = 120):
    load_dotenv()
    import pyodbc
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={os.environ['DB_SERVER']};DATABASE={os.environ['DB_NAME']};"
        f"UID={os.environ['DB_USERNAME']};PWD={os.environ['DB_PASSWORD']};"
        "TrustServerCertificate=yes;", timeout=timeout)
    q = f"SELECT {WINDOW_COLS} FROM {table} WITH (NOLOCK) WHERE locoid=? AND devicetime>=? AND devicetime<? ORDER BY devicetime OPTION (RECOMPILE)"
    import pandas as pd
    df = pd.read_sql(q, conn, params=[loco, start, end])
    conn.close()
    return df
