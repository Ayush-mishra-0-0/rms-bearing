/* =========================================================================
   AUDIT 01 - Fleet coverage: RMS master-list counts and union.
   Reproduces: "846 RMS-equipped locos" (union of three master lists) and
   the per-list counts used throughout the audit report.

   Tables:
     dbo.rmslocolist                        (615 rows)
     dbo.LomNumber                          (70 rows)
     dbo.Loco_Process_Signals_LocoNumber    (671 rows)
   -------------------------------------------------------------------------
   Run in SSMS connected to SLAM_RDS_DB_26.04.2024. Read-only, safe.
   ========================================================================= */
SELECT 'rmslocolist'                       AS source, COUNT(*) AS n_locos FROM dbo.rmslocolist
UNION ALL SELECT 'LomNumber',                          COUNT(*)        FROM dbo.LomNumber
UNION ALL SELECT 'Loco_Process_Signals_LocoNumber',    COUNT(*)        FROM dbo.Loco_Process_Signals_LocoNumber;

/* Union (deduped) of the three master lists. NOTE: this is NOT the full RMS
   fleet - it undercounts. The authoritative roster is RMSLocoMap below. */
SELECT COUNT(*) AS union_locos
FROM (
    SELECT locoid     AS locoid FROM dbo.rmslocolist
    UNION
    SELECT LomNumber AS locoid FROM dbo.LomNumber
    UNION
    SELECT LocoNumber AS locoid FROM dbo.Loco_Process_Signals_LocoNumber
) m;

/* RMSLocoMap: the authoritative RMS-fitted roster (2408 rows, ~2387 distinct).
   Verified 31-Jul-2026: all rows have RMSFlag='Y'; RMSMake distribution =
   LotusWireless 1072, ARC 525, Medha 457, Siemens 348, CRIS 3, Equus 2, LRail 1.
   ~281 LomNumbers are non-numeric (test/synthetic entries, e.g. '65119B'). */
SELECT LomNumber, RMSFlag, RMSMake, EntryDate
FROM dbo.RMSLocoMap
WHERE RMSFlag = 'Y'
ORDER BY LomNumber;

/* Distinct fitted count + make distribution. */
SELECT RMSMake, COUNT(*) AS n FROM dbo.RMSLocoMap WHERE RMSFlag='Y' GROUP BY RMSMake ORDER BY n DESC;
SELECT COUNT(DISTINCT LomNumber) AS distinct_fitted FROM dbo.RMSLocoMap WHERE RMSFlag='Y';
