import os, csv, json, time
import pyodbc
from dotenv import load_dotenv
load_dotenv('C:/Users/CRIS/Desktop/ayush/rms-bearing/monitoring/.env')
OUT = 'C:/Users/CRIS/Desktop/ayush/rms-bearing/case_42728/telemetry_42728_2026_rds.json.csv'
LOG = 'C:/Users/CRIS/Desktop/ayush/rms-bearing/case_42728/extract_2026_rerun.log'
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
days = ["2026-08-01","2026-08-02","2026-08-03","2026-08-05","2026-08-06",
        "2026-08-07","2026-08-08","2026-08-09","2026-08-10"]
log = open(LOG, "a", encoding="utf-8")
def logmsg(s):
    print(s, flush=True)
    log.write(s + "\n"); log.flush()
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USERNAME')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "TrustServerCertificate=yes;",
    timeout=120,
)
conn.timeout = 600
cur = conn.cursor()
# current total from existing file
total = 86217
logmsg(f"RESUME from 2026-08-01, starting cumulative {total}")
def fetch_range(s, e, w, attempt=1):
    global total
    try:
        cur.execute("""
        SELECT DeviceTime, Vendor, JsonPayload
        FROM dbo.Lotus_loco_process_signals_RDSOJson WITH (NOLOCK)
        WHERE LocoId=? AND DeviceTime >= ? AND DeviceTime < ?
        ORDER BY DeviceTime
        """, "42728", s, e)
        cnt = 0
        while True:
            batch = cur.fetchmany(5000)
            if not batch:
                break
            for (dt, vendor, payload) in batch:
                try:
                    obj = json.loads(payload) if payload else {}
                except Exception:
                    obj = {}
                w.writerow([obj.get(k, "") for k in keeps])
                cnt += 1
                total += 1
        return cnt
    except pyodbc.OperationalError as ex:
        if 'HYT00' in str(ex) and attempt <= 3:
            logmsg(f"  timeout {s}..{e} attempt {attempt}, retrying in 5s...")
            time.sleep(5)
            return fetch_range(s, e, w, attempt+1)
        raise
for d in days:
    s = d + " 00:00:00"
    e = d + " 23:59:59"
    with open(OUT, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        try:
            n = fetch_range(s, e, w)
            logmsg(f"{d}: day rows {n}, cumulative {total}")
        except Exception as ex:
            logmsg(f"{d}: FAILED {type(ex).__name__} {str(ex)[:300]} - trying 2 half-day splits")
            # split day into 00-12 and 12-24
            for hs, he, tag in [(d+" 00:00:00", d+" 12:00:00", "AM"), (d+" 12:00:00", d+" 23:59:59", "PM")]:
                n2 = fetch_range(hs, he, w)
                logmsg(f"{d} {tag}: day rows {n2}, cumulative {total}")
conn.close()
logmsg("RESUME DONE cumulative: %d" % total)
log.close()
