/* Schema inventory; read-only and independently executable. */
SELECT s.name AS schema_name,t.name AS table_name,c.name AS column_name,ty.name AS data_type,c.max_length,c.is_nullable
FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id JOIN sys.columns c ON c.object_id=t.object_id JOIN sys.types ty ON ty.user_type_id=c.user_type_id
WHERE t.name IN ('Lotus_loco_process_signals_4L','Locoprocessdata','Lotus_loco_process_signals_5','Lotus_loco_process_signals_sma','Lotus_LocoFaultData') ORDER BY t.name,c.column_id;
