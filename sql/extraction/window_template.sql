-- Read-only window template. Indexed on (locoid, devicetime). Always use WITH (NOLOCK) + OPTION (RECOMPILE).
SELECT locoid, devicetime, Vendor,
  xspeedloco, gpsspeed, xiprim_1, xuprim_1, ltedemand, lbedemand, mtrcctract1,
  xtempmotor1_1, xtempmotor2_1, xtempmotor3_1, xtempmotor1_2, xtempmotor2_2, xtempmotor3_2
FROM dbo.Lotus_loco_process_signals WITH (NOLOCK)
WHERE locoid = '37282' AND devicetime >= '2024-12-03' AND devicetime < '2024-12-10'
ORDER BY devicetime OPTION (RECOMPILE);
