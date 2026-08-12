/* =========================================================================
   AUDIT 03 - Global telemetry outage calendar (daily row counts).
   Reproduces the two platform-wide outages:
     - 2024-07-05 .. 2024-07-27   (~0-132k/day; 0 on 17 & 21 Jul)
     - 2024-10-10 .. 2024-10-17   (862k -> 0,0,0 -> 44)
   and the June-2024 ramp-up, plus per-day healthy baseline (~3.5-4.5M/day).

   IMPORTANT (performance): Lotus_loco_process_signals is ~5.3B rows and has
   NO usable index on devicetime alone. Running this over the full table will
   time out. The date-bounded version below scanned 2024-06-01..2025-02-01 in
   ~245s and is the version used for the report. Run at an off-peak time.
   ------------------------------------------------------------------------- */
DECLARE @lo datetime = '2024-06-01 00:00:00';
DECLARE @hi datetime = '2025-02-01 00:00:00';

SELECT CONVERT(date, devicetime) AS day, COUNT_BIG(*) AS global_rows
FROM dbo.Lotus_loco_process_signals WITH (NOLOCK)
WHERE devicetime >= @lo AND devicetime < @hi
GROUP BY CONVERT(date, devicetime)
ORDER BY day;

/* Zero-row days in the same window (outages / ingest stops). */
;WITH days AS (
    SELECT TOP (DATEDIFF(day, @lo, @hi)) CONVERT(date, DATEADD(day, ROW_NUMBER() OVER (ORDER BY (SELECT 0)) - 1, @lo)) AS day
    FROM sys.all_objects a CROSS JOIN sys.all_objects b
)
SELECT d.day
FROM days d
LEFT JOIN (
    SELECT CONVERT(date, devicetime) AS day, COUNT_BIG(*) AS n
    FROM dbo.Lotus_loco_process_signals WITH (NOLOCK)
    WHERE devicetime >= @lo AND devicetime < @hi
    GROUP BY CONVERT(date, devicetime)
) g ON g.day = d.day
WHERE g.n IS NULL
ORDER BY d.day;

/* Expected zero-row days (verified 31-Jul-2026): 2024-07-17, 2024-07-21,
   2024-10-11, 2024-10-12, 2024-10-13. (NOT 2025-01-16 — that day has ~3.9M
   rows; an earlier draft of the report wrongly listed it.) */
