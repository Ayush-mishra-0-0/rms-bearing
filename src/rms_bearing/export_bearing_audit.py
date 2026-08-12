import pyodbc, os, csv
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

rows = []
with open(r'C:\Users\CRIS\AppData\Local\Temp\opencode\owner_rows.txt', encoding='utf-8-sig') as f:
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) < 8: continue
        fid, loco, date, c, s, e, m, d = p[:8]
        dl = d.lower()
        if 'bear' in dl or 'seize' in dl or 'labyrinth' in dl:
            rows.append({'fid': fid.strip(), 'loco': loco.strip(), 'date': date.strip(), 'defect': d.strip()})

reg = {}
with open(r'data\processed\ground_truth_failure_registry.csv', newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        reg[str(row['FailureID']).strip()] = row

cls = {}
with open(r'data\processed\owner_failure_classification.csv', newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        cls[str(row['FailureID']).strip()] = row

c = pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={os.getenv('DB_SERVER')};DATABASE={os.getenv('DB_NAME')};UID={os.getenv('DB_USERNAME')};PWD={os.getenv('DB_PASSWORD')};TrustServerCertificate=yes", timeout=120)
r = c.cursor()

out = []
for row in sorted(rows, key=lambda x: x['date']):
    fid, loco, date, defect = row['fid'], row['loco'], row['date'], row['defect']
    d = datetime.strptime(date, '%d/%m/%Y')
    lo5 = (d - timedelta(days=5)).strftime('%Y-%m-%d')
    hi5 = (d + timedelta(days=5)).strftime('%Y-%m-%d')
    lo1 = (d - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    hi1 = (d + timedelta(days=1)).strftime('%Y-%m-%d 23:59:59')
    try:
        t5 = r.execute(f"SELECT COUNT(*) FROM dbo.Lotus_loco_process_signals WHERE locoid='{loco}' AND devicetime BETWEEN '{lo5}' AND '{hi5}'").fetchval()
        t1 = r.execute(f"SELECT COUNT(*) FROM dbo.Lotus_loco_process_signals WHERE locoid='{loco}' AND devicetime BETWEEN '{lo1}' AND '{hi1}'").fetchval()
    except Exception:
        t5 = t1 = -1
    r_ = reg.get(fid, {})
    c_ = cls.get(fid, {})
    out.append({
        'FailureID': fid,
        'Loco': loco,
        'FailureDate': date,
        'Defect': defect,
        'RegistryLabel': r_.get('Label', ''),
        'Classification': c_.get('AssignedLabel', ''),
        'InRegistry': 'Y' if fid in reg else 'N',
        'TelemetryRows_plus_minus5d': t5,
        'TelemetryRows_plus_minus1d': t1,
        'TelemetryNearFailure': 'Y' if t5 > 0 else 'N',
    })

with open(r'data\manifests\bearing_failure_events_audit.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

print(f'wrote {len(out)} bearing events to data/manifests/bearing_failure_events_audit.csv')
n_tel = sum(1 for o in out if o['TelemetryNearFailure'] == 'Y')
print(f'with telemetry near failure: {n_tel}')
c.close()
