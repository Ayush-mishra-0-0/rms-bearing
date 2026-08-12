/* Phase 1 / Steps 5–6. Replace dates with the actual bounds returned by discovery. */
DECLARE @from datetime='2024-01-01',@to datetime='2027-01-01';
WITH candidate AS (
 SELECT LFDId,locoid,faulttime,errorinfo2,processorid,Vendor,FaultText,
 CONVERT(date,faulttime) event_date,
 LAG(faulttime) OVER(PARTITION BY locoid,CONVERT(date,faulttime),FaultText ORDER BY faulttime) prior_same_text
 FROM dbo.Lotus_LocoFaultData WHERE faulttime>=@from AND faulttime<@to AND (FaultText LIKE '%axle%' OR FaultText LIKE '%lock%' OR FaultText LIKE '%bearing%' OR FaultText LIKE '%seiz%' OR FaultText LIKE '%traction motor%' OR FaultText LIKE '%pinion%' OR FaultText LIKE '%gear%' OR FaultText LIKE '%wheel%' OR FaultText LIKE '%smoke%' OR FaultText LIKE '%oil leak%' OR FaultText LIKE '%labyrinth%')
), incident AS (SELECT *,CASE WHEN prior_same_text IS NULL OR DATEDIFF(minute,prior_same_text,faulttime)>60 THEN 1 ELSE 0 END AS new_incident FROM candidate)
SELECT locoid,event_date,MIN(faulttime) incident_start,MAX(faulttime) incident_end,COUNT_BIG(*) source_records,MAX(FaultText) representative_fault_text,MAX(errorinfo2) fault_code,MAX(processorid) processorid,MAX(Vendor) vendor FROM incident GROUP BY locoid,event_date,FaultText,CASE WHEN new_incident=1 THEN faulttime ELSE event_date END ORDER BY incident_start;
