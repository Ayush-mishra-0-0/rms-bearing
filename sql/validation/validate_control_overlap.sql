/* Find locos with sufficient observations in a nominated comparison window. */
DECLARE @from datetime='2025-01-01',@to datetime='2025-01-31'; SELECT locoid,COUNT_BIG(*) rows,MIN(devicetime) first_ts,MAX(devicetime) last_ts FROM dbo.Locoprocessdata WHERE devicetime>=@from AND devicetime<@to GROUP BY locoid HAVING COUNT_BIG(*)>=1000 ORDER BY rows DESC;
