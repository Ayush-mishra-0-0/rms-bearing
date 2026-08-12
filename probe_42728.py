import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()


def conn():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        f"TrustServerCertificate=yes;",
        timeout=30,
    )


LOCO = "42728"

c = conn()
cur = c.cursor()
print("CONNECTED:", c.getinfo(pyodbc.SQL_DBMS_NAME))

print("\n--- 0. Locoid column types in candidate tables ---")
for t in ("dbo.Lotus_LocoFaultData", "dbo.Locoprocessdata",
          "dbo.Lotus_loco_process_signals", "dbo.Lotus_loco_process_signals_5",
          "dbo.Lotus_loco_process_signals_4L", "dbo.Lotus_loco_process_signals_sma"):
    cur.execute(f"SELECT TOP 0 * FROM {t}")
    cols = [d[0] for d in cur.description]
    lc = [x for x in cols if 'ocoid' in x.lower() or 'Loco' in x]
    dt = [x for x in cols if 'time' in x.lower() or 'Date' in x]
    print(f"  {t}: locoid-like={lc} time-like={dt}")

print("\n--- 1. Presence in RMSLocoMap ---")
cur.execute("SELECT LomNumber,RMSFlag,RMSMake,EntryDate FROM dbo.RMSLocoMap WHERE LomNumber=?", LOCO)
for r in cur.fetchall():
    print(" ", r)
print("  (empty = not in RMSLocoMap)")

print("\n--- 2. Presence in master lists ---")
for tbl in ("rmslocolist", "LomNumber", "Loco_Process_Signals_LocoNumber"):
    try:
        cur.execute(f"SELECT TOP 1 * FROM dbo.{tbl}")
        cols = [d[0] for d in cur.description]
        # find a loco-number-ish column
        cand = [x for x in cols if 'loc' in x.lower() or 'number' in x.lower() or 'no' == x.lower()]
        if cand:
            q = f"SELECT COUNT(*) FROM dbo.{tbl} WHERE {cand[0]} = ?"
            cur.execute(q, LOCO)
            print(f"  {tbl}: matched on col '{cand[0]}' count=", cur.fetchone()[0])
        else:
            print(f"  {tbl}: columns {cols}")
    except Exception as e:
        print(f"  {tbl}: error {e}")

print("\n--- 3. Telemetry table presence (any history) ---")
for t in ("dbo.Locoprocessdata", "dbo.Lotus_loco_process_signals",
          "dbo.Lotus_loco_process_signals_5", "dbo.Lotus_loco_process_signals_4L",
          "dbo.Lotus_loco_process_signals_sma"):
    try:
        cur.execute(f"SELECT COUNT_BIG(*), MIN(devicetime), MAX(devicetime) FROM {t} WITH (NOLOCK) WHERE locoid=?", LOCO)
        r = cur.fetchone()
        print(f"  {t}: rows={r[0]} min={r[1]} max={r[2]}")
    except Exception as e:
        print(f"  {t}: error {e}")

print("\n--- 4. Fault table presence + range ---")
cur.execute("SELECT COUNT_BIG(*), MIN(faulttime), MAX(faulttime) FROM dbo.Lotus_LocoFaultData WITH (NOLOCK) WHERE locoid=?", LOCO)
r = cur.fetchone()
print(f"  rows={r[0]} min={r[1]} max={r[2]}")

c.close()
