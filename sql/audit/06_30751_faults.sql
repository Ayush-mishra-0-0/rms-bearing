/* =========================================================================
   AUDIT 06 - Fault events around a loco's incident (30751 precursor sequence).
   Reproduces the 30751 evidence used for validation / precursor mining:
     - Fault channel KEPT FLOWING through the telemetry gap (11-17 Dec 2024),
       proving telemetry and fault events are separate channels.
     - 16-Dec 17:29/17:30 "STB1:0009 Rotary switch bogie 1 cut out" +
       "FLG1:0094 SS02 traction bogie1 off", repeated 20:38/20:39.
   ------------------------------------------------------------------------- */
SELECT locoid, faulttime, FaultText, errorinfo2, processorid, Vendor
FROM dbo.Lotus_LocoFaultData WITH (NOLOCK)
WHERE locoid = '30751'
  AND faulttime >= '2024-12-10 00:00:00'
  AND faulttime <  '2024-12-20 00:00:00'
ORDER BY faulttime;
