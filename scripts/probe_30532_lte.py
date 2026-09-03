"""Probe 30532 ltedemand/speed coverage to pick a valid baseline."""
import csv
from datetime import datetime

P = 'C:/Users/CRIS/Desktop/ayush/rms-bearing/data/interim/30532_11d.csv'


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


with open(P, newline='', encoding='utf-8') as fh:
    rows = list(csv.DictReader(fh))
print('rows:', len(rows))
days = {}
for r in rows:
    try:
        t = datetime.strptime(str(r.get('devicetime'))[:19], '%Y-%m-%d %H:%M:%S')
    except Exception:
        continue
    lte = f(r.get('ltedemand'))
    v = f(r.get('xspeedloco'))
    ip = f(r.get('xiprim_1'))
    key = t.strftime('%m-%d')
    d = days.setdefault(key, {'n': 0, 'lte1': 0, 'full': 0})
    d['n'] += 1
    if lte == 1:
        d['lte1'] += 1
    if lte == 1 and v is not None and ip is not None:
        d['full'] += 1
for k in sorted(days):
    print(k, days[k])
