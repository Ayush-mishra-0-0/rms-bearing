/* Explicit event/telemetry overlap count. */
DECLARE @loco varchar(30)='31637',@failure datetime='2026-06-08'; SELECT MIN(devicetime) first_ts,MAX(devicetime) last_ts,COUNT_BIG(*) rows_30d FROM dbo.Locoprocessdata WHERE CAST(locoid AS varchar(30))=@loco AND devicetime>=DATEADD(day,-30,@failure) AND devicetime<@failure;
