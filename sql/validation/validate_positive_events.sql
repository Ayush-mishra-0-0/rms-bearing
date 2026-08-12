/* Phase 1 validation. Review candidates; this does not access telemetry. */
DECLARE @from datetime='2024-01-01',@to datetime='2027-01-01';
SELECT locoid,CONVERT(date,faulttime) event_date,FaultText,errorinfo2 AS fault_code,processorid,Vendor,COUNT_BIG(*) repeated_records,MIN(faulttime) first_record,MAX(faulttime) last_record,
 CASE WHEN FaultText LIKE '%seiz%' OR FaultText LIKE '%locked axle%' OR FaultText LIKE '%bearing lock%' THEN 'PROBABLE' WHEN FaultText LIKE '%axle%' OR FaultText LIKE '%bearing%' OR FaultText LIKE '%traction motor%' OR FaultText LIKE '%pinion%' OR FaultText LIKE '%gear%' THEN 'POSSIBLE' ELSE 'POSSIBLE' END AS evidence
FROM dbo.Lotus_LocoFaultData WHERE faulttime>=@from AND faulttime<@to AND (FaultText LIKE '%axle%' OR FaultText LIKE '%lock%' OR FaultText LIKE '%bearing%' OR FaultText LIKE '%seiz%' OR FaultText LIKE '%traction motor%' OR FaultText LIKE '%pinion%' OR FaultText LIKE '%gear%' OR FaultText LIKE '%wheel%' OR FaultText LIKE '%smoke%' OR FaultText LIKE '%oil leak%' OR FaultText LIKE '%labyrinth%')
GROUP BY locoid,CONVERT(date,faulttime),FaultText,errorinfo2,processorid,Vendor ORDER BY event_date,locoid;
