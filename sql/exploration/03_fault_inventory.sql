/* Step 1. Only documented columns exist: LFDId, locoid, faulttime, FaultText, errorinfo2, processorid. */
DECLARE @from datetime='2024-01-01',@to datetime='2027-01-01';
SELECT locoid,faulttime,errorinfo2 AS FaultCode,processorid,FaultText FROM dbo.Lotus_LocoFaultData
WHERE faulttime>=@from AND faulttime<@to AND (FaultText LIKE '%axle%' OR FaultText LIKE '%lock%' OR FaultText LIKE '%bear%' OR FaultText LIKE '%seiz%' OR FaultText LIKE '%traction motor%' OR FaultText LIKE '%pinion%' OR FaultText LIKE '%gear%' OR FaultText LIKE '%wheel%' OR FaultText LIKE '%smoke%' OR FaultText LIKE '%labyrinth%' OR FaultText LIKE '%oil leak%') ORDER BY faulttime;
