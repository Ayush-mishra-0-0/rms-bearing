/* =========================================================================
   AUDIT 05 - RMSLocoMap fitment dates (RMS vs failure timeline).
   Reproduces: RMSLocoMap entry dates confirm RMS fitment timing, not a date
   mismatch (data_audit_report.md 7.4 / comprehensive 7.4).

   Verified entries for the 5 bearing-event locos fitted per RMSLocoMap:
     30532: make=ARC        entry=2024-04-01
     30514: make=Medha      entry=2026-03-13   (AFTER its 04/07/2024 failure)
     30751: make=LotusWireless entry=2024-04-30
     37282: make=LotusWireless entry=2024-04-30
     37361: make=ARC        entry=2024-04-15
   ------------------------------------------------------------------------- */
SELECT LomNumber, RMSFlag, RMSMake, EntryDate
FROM dbo.RMSLocoMap
WHERE LomNumber IN ('30514','30532','30751','37282','37361','32134','37044')
ORDER BY LomNumber;

/* Total RMSLocoMap row count and fitted (RMSFlag=Y) count. */
SELECT COUNT(*) AS total_rows,
       SUM(CASE WHEN RMSFlag='Y' THEN 1 ELSE 0 END) AS fitted
FROM dbo.RMSLocoMap;
