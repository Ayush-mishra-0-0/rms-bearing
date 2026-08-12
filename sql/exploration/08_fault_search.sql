/* Phase 1 / Step 3. One keyword family and one calendar month per execution. No telemetry access. */
DECLARE @month_start datetime='2025-01-01', @month_end datetime='2025-02-01';
DECLARE @keyword nvarchar(100)=N'axle';
SELECT LFDId,locoid,faulttime,errorinfo2 AS fault_code,processorid,Vendor,FaultText,
 CASE WHEN FaultText LIKE N'%seiz%' OR FaultText LIKE N'%locked axle%' OR FaultText LIKE N'%bearing lock%' OR FaultText LIKE N'%pinion cut%' THEN 'PROBABLE'
      WHEN FaultText LIKE N'%axle%' OR FaultText LIKE N'%bearing%' OR FaultText LIKE N'%traction motor%' OR FaultText LIKE N'%gear%' OR FaultText LIKE N'%pinion%' THEN 'POSSIBLE'
      WHEN FaultText LIKE N'%wheel heating%' OR FaultText LIKE N'%hot axle%' OR FaultText LIKE N'%smoke%' OR FaultText LIKE N'%oil leak%' OR FaultText LIKE N'%labyrinth%' THEN 'POSSIBLE' END AS evidence
FROM dbo.Lotus_LocoFaultData
WHERE faulttime>=@month_start AND faulttime<@month_end AND FaultText LIKE N'%'+@keyword+N'%'
ORDER BY faulttime,LFDId;
/* Execute separately for: axle, lock, bearing, seize, traction motor, TM, motor, gear, gearcase, pinion, wheel, hot axle, smoke, oil leak, labyrinth. */
