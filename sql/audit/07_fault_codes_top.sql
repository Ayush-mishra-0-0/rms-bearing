/* =========================================================================
   AUDIT 07 - Top fault codes across the RMS-bearing locos (fleet-level view).
   Reproduces the "no bearing-specific fault code in the top ranks" finding.

   NOTE: Lotus_LocoFaultData is ~405M rows; a join against the full 2,387-loco
   RMSLocoMap roster times out. This bounded version (the way the report number
   was originally computed) filters to the 6 RMS-fitted locos found in the
   fleet-coverage cross-check, using the (locoid) index per loco.
   ------------------------------------------------------------------------- */
SELECT TOP 25 f.FaultText, COUNT_BIG(*) AS occurrences
FROM dbo.Lotus_LocoFaultData f WITH (NOLOCK)
WHERE f.locoid IN ('30346','30751','37282','37361','39117','44092')
GROUP BY f.FaultText
ORDER BY occurrences DESC;

/* Expected (verified): top-25 contains no bearing-specific text.
   Top ranks: ACP/Train Part (124k), Earth fault control circuit (43k),
   Power on MCE (23k), Lifesign from ACI1 missing (14.5k), ...  */
