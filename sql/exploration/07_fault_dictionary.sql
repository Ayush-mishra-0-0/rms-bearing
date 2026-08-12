/* Phase 1 / Step 2. Run one month at a time. Distinct text values reveal the alarm vocabulary. */
DECLARE @month_start datetime='2025-01-01', @month_end datetime='2025-02-01';
SELECT TOP (5000) FaultText,COUNT_BIG(*) AS occurrences,MIN(faulttime) first_seen,MAX(faulttime) last_seen
FROM dbo.Lotus_LocoFaultData
WHERE faulttime>=@month_start AND faulttime<@month_end AND FaultText IS NOT NULL
GROUP BY FaultText ORDER BY occurrences DESC;
/* Date distribution: run only after choosing a bounded period. */
SELECT CONVERT(char(7),faulttime,120) fault_month,COUNT_BIG(*) record_count
FROM dbo.Lotus_LocoFaultData WHERE faulttime>=@month_start AND faulttime<@month_end
GROUP BY CONVERT(char(7),faulttime,120) ORDER BY fault_month;
