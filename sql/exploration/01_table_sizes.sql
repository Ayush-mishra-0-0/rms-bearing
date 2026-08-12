/* Approximate row counts from metadata; read-only. */
SELECT t.name, SUM(p.rows) AS approximate_rows FROM sys.tables t JOIN sys.partitions p ON p.object_id=t.object_id AND p.index_id IN(0,1)
WHERE t.name IN ('Lotus_loco_process_signals_4L','Locoprocessdata','Lotus_loco_process_signals_5','Lotus_loco_process_signals_sma','Lotus_LocoFaultData') GROUP BY t.name ORDER BY approximate_rows DESC;
