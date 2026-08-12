import os
from dotenv import load_dotenv
import pyodbc
import json
import csv

load_dotenv()
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USERNAME')};"
    f"PWD={os.getenv('DB_PASSWORD')}",
    timeout=300,
)
cur = conn.cursor()

cur.execute("""
SELECT Id, DeviceTime, Vendor, JsonPayload
FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK)
WHERE LocoId='42728' AND DeviceTime BETWEEN '2026-07-25' AND '2026-08-12'
ORDER BY DeviceTime
""")

# discover union of keys
keys = set()
rows = []
n = 0
while True:
    batch = cur.fetchmany(5000)
    if not batch:
        break
    for (rid, dt, vendor, payload) in batch:
        try:
            obj = json.loads(payload)
        except Exception:
            obj = {}
        keys.update(obj.keys())
        rows.append((rid, dt, vendor, obj))
        n += 1
print("parsed rows:", n)

keeps = ["locoid","latitude","longitude","gpsspeed","devicetime","mvcb_on","mprswpan1","mprswpan2",
         "bbur1_off","bbur2_off","bbur3_off","bstb1_off","bstb2_off","bflg1_off","bflg2_off",
         "bslg1_off","bslg2_off","bhbb1_off","bhbb2_off","bbda1_off","bbda2_off",
         "ltedemand","lbedemand","xu_battery","xspeedloco","xangtrans","xuprim_1","xiprim_1",
         "xvist_a1_1","xvist_a2_1","xvist_a3_1","xvist_a1_2","xvist_a2_2","xvist_a3_2",
         "xtempmotor1_1","xtempmotor2_1","xtempmotor3_1","xtempmotor1_2","xtempmotor2_2","xtempmotor3_2",
         "xatmp1oeltr_1","xatmp1oeltr_2","xatmp1oelsr_1","xatmp1oelsr_2",
         "xatmp2oeltr_1","xatmp2oeltr_2","xatmp2oelsr_1","xatmp2oelsr_2",
         "sr1_ipvoltage","sr2_ipvoltage",
         "bg1tm1_ipvoltage","bg1tm2_ipvoltage","bg1tm3_ipvoltage",
         "bg2tm1_ipvoltage","bg2tm2_ipvoltage","bg2tm3_ipvoltage",
         "bur_ipvoltage","bur_ipcurrent","bur1_opcurrent","bur2_opcurrent","bur3_opcurrent",
         "faultnum","odometerK","odometerM","odometerG",
         "xenergymwh_ec","xenergygwh_ec","xenergymwh_er","xenergyfwh_er",
         "xuun_bur1","xuun_bur2","xuun_bur3","xuuz1_bur1","xuuz1_bur2","xuuz1_bur3",
         "xuiz1_bur1","xuiz1_bur2","xuiz1_bur3","mtrcctract1","mtrcctract2","xaibur",
         "bur_1_xufwr","bur_2_xufwr","bur_3_xufwr","xadrucktr_1","xadrucktr_2","xadrucksr_1","xadrucksr_2"]

out = "telemetry_42728_2026_rds.json.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(keeps)
    for (rid, dt, vendor, obj) in rows:
        w.writerow([obj.get(k, "") for k in keeps])
print("wrote", out)
conn.close()
