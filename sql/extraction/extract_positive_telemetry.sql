/* Replace values only after an event is confirmed. */
DECLARE @loco varchar(30)='31637',@failure datetime='2026-06-08';
SELECT * FROM dbo.Locoprocessdata WHERE CAST(locoid AS varchar(30))=@loco AND devicetime>=DATEADD(day,-30,@failure) AND devicetime<@failure ORDER BY devicetime;
