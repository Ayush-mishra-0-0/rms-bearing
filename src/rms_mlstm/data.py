"""Read-only DB extraction. Never writes to DB. Aggregates are indexed (locoid, devicetime)."""
from __future__ import annotations
import os
from dotenv import load_dotenv

WINDOW_COLS = ("locoid,devicetime,Vendor,latitude,longitude,gpsspeed,xspeedloco,"
 "xiprim_1,xuprim_1,ltedemand,lbedemand,mtrcctract1,"
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
