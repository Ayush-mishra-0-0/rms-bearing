/* Step 0. 4L deliberately excluded: it has no devicetime column. */
SELECT 'Locoprocessdata' table_name,MIN(devicetime) first_ts,MAX(devicetime) last_ts,COUNT_BIG(*) rows,COUNT(DISTINCT CONVERT(date,devicetime)) recording_days,COUNT(DISTINCT locoid) locos FROM dbo.Locoprocessdata
UNION ALL SELECT 'Lotus_loco_process_signals_5',MIN(devicetime),MAX(devicetime),COUNT_BIG(*),COUNT(DISTINCT CONVERT(date,devicetime)),COUNT(DISTINCT locoid) FROM dbo.Lotus_loco_process_signals_5
UNION ALL SELECT 'Lotus_loco_process_signals_sma',MIN(devicetime),MAX(devicetime),COUNT_BIG(*),COUNT(DISTINCT CONVERT(date,devicetime)),COUNT(DISTINCT locoid) FROM dbo.Lotus_loco_process_signals_sma;
/* Run this per table to expose daily coverage and gaps. */
SELECT CONVERT(date,devicetime) recording_day,COUNT_BIG(*) rows,COUNT(DISTINCT locoid) locos FROM dbo.Locoprocessdata GROUP BY CONVERT(date,devicetime) ORDER BY recording_day;
