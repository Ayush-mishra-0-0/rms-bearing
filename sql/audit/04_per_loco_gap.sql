/* =========================================================================
   AUDIT 04 - Per-loco telemetry gap analysis around incidents.
   Reproduces the per-loco outage facts:

     30751: 0 rows 11-17 Dec 2024  (platform healthy -> per-loco gap)
     37282: continuous dense telemetry through 10/12/2024 failure
     30532: sparse telemetry 01-07 Apr 2024 (failure 04/04)
     37361: only 1 telemetry day (23-Jul-2024) in 15-Jul..20-Aug window
     30514: telemetry begins 2026-03-13 (fitted later; none at 04/07/2024)
     32134: single telemetry row on 2022-01-15 (none at 25/05/2024)

   Uses the (locoid, devicetime) index -> fast per-loco aggregates.
   Change @loco and the date range to re-check any loco.
   ------------------------------------------------------------------------- */
DECLARE @loco varchar(10) = '30751';
DECLARE @lo datetime = '2024-11-01 00:00:00';
DECLARE @hi datetime = '2025-01-01 00:00:00';

SELECT CONVERT(date, devicetime) AS day, COUNT_BIG(*) AS rows
FROM dbo.Lotus_loco_process_signals WITH (NOLOCK)
WHERE locoid = @loco AND devicetime >= @lo AND devicetime < @hi
GROUP BY CONVERT(date, devicetime)
ORDER BY day;

/* Expected for 30751 Nov-2024..Jan-2025:
   ... 09-Dec 21,326 | 10-Dec 10,609 | (11-17 Dec ZERO) | 18-Dec 4,395 | 19-Dec 25,032 ... */

/* --- 37361 window around its 03-Aug-2024 failure --- */
-- SET @loco='37361'; SET @lo='2024-07-15'; SET @hi='2024-08-21'; re-run.

/* --- 30532 around its 04-Apr-2024 failure --- */
-- SET @loco='30532'; SET @lo='2024-03-29'; SET @hi='2024-04-09'; re-run.

/* --- 37282 around its 10-Dec-2024 failure --- */
-- SET @loco='37282'; SET @lo='2024-12-01'; SET @hi='2024-12-15'; re-run.

/* --- 30514 (should be empty before 2026-03-13) --- */
-- SET @loco='30514'; SET @lo='2024-06-01'; SET @hi='2024-08-15'; re-run.

/* --- 32134 (single row 2022-01-15) --- */
-- SET @loco='32134'; SET @lo='2022-01-01'; SET @hi='2024-12-31'; re-run.
