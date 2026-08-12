/* Daily locomotive availability for matching controls. */
SELECT CONVERT(date,devicetime) recording_day,locoid,COUNT_BIG(*) rows FROM dbo.Locoprocessdata GROUP BY CONVERT(date,devicetime),locoid ORDER BY recording_day,locoid;
