/* Timestamp bounds and duplicate timestamps. */
SELECT MIN(devicetime) min_ts,MAX(devicetime) max_ts,SUM(CASE WHEN devicetime>'2026-12-31' OR devicetime<'2000-01-01' THEN 1 ELSE 0 END) implausible_rows FROM dbo.Locoprocessdata; SELECT locoid,devicetime,COUNT_BIG(*) duplicates FROM dbo.Locoprocessdata GROUP BY locoid,devicetime HAVING COUNT_BIG(*)>1;
