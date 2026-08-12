/* =========================================================================
   AUDIT 08 - Healthy-control telemetry gaps (is "silent week" normal?).
   Reproduces the finding that a HEALTHY loco (39085) had the same 23-day
   gap as 30751 during the July-2024 platform outage:
     39085: 2024-07-05 .. 2024-07-27 (zero rows, 23 days)
   => the July gap is platform-wide, not loco-specific or failure-linked.
   ------------------------------------------------------------------------- */
DECLARE @loco varchar(10) = '39085';
DECLARE @lo datetime = '2024-06-01 00:00:00';
DECLARE @hi datetime = '2024-09-01 00:00:00';

SELECT CONVERT(date, devicetime) AS day, COUNT_BIG(*) AS rows
FROM dbo.Lotus_loco_process_signals WITH (NOLOCK)
WHERE locoid = @loco AND devicetime >= @lo AND devicetime < @hi
GROUP BY CONVERT(date, devicetime)
ORDER BY day;

/* Expected: rows 2024-06-04..07-04, ZERO 2024-07-05..07-27, resumes 07-28.
   Set @loco to any other RMS loco to replicate the control comparison. */
