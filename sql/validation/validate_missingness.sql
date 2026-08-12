/* Null percentages for core channels. */
SELECT COUNT_BIG(*) rows,100.0*SUM(CASE WHEN xtempmotor1_1 IS NULL THEN 1 ELSE 0 END)/NULLIF(COUNT_BIG(*),0) tm1_null_pct,100.0*SUM(CASE WHEN xspeedloco IS NULL THEN 1 ELSE 0 END)/NULLIF(COUNT_BIG(*),0) speed_null_pct,100.0*SUM(CASE WHEN xvist_a1_1 IS NULL THEN 1 ELSE 0 END)/NULLIF(COUNT_BIG(*),0) tm_speed_null_pct FROM dbo.Locoprocessdata;
