-- 37282 7d MLSTM-iForest extraction (read-only, indexed).
-- FailureID 4635100, TM bearing seized, anchor 2024-12-10 05:00:00 EXACT
-- (override: axle-6 locked 04:42-04:46, EP withdrawal 05:00 per registry summary).
-- Window: 2024-12-03 05:00:00 → 2024-12-10 05:00:00 (168h, Long-term degradation).
-- Audit: 359,439 rows ±5d, dense 21k–72k/day. Use Dec 03–07 healthy-train, Dec 08–10 05:00 validate.
-- Run in SSMS or via pipelines/01_extract_windows.py (same predicate).
SELECT locoid, devicetime, Vendor,
  latitude, longitude, gpsspeed, xspeedloco,
  xiprim_1, xuprim_1, ltedemand, lbedemand, mtrcctract1,
  xtempmotor1_1, xtempmotor2_1, xtempmotor3_1,
  xtempmotor1_2, xtempmotor2_2, xtempmotor3_2
FROM dbo.Lotus_loco_process_signals WITH (NOLOCK)
WHERE locoid = '37282'
  AND devicetime >= '2024-12-03 05:00:00'
  AND devicetime < '2024-12-10 05:00:00'
ORDER BY devicetime OPTION (RECOMPILE);
