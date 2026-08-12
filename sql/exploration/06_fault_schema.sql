/* Phase 1 / Step 1. Read-only, independently executable schema check. */
SELECT c.column_id,c.name AS column_name,t.name AS data_type,c.max_length,c.precision,c.scale,c.is_nullable
FROM sys.columns c JOIN sys.types t ON t.user_type_id=c.user_type_id
WHERE c.object_id=OBJECT_ID('dbo.Lotus_LocoFaultData') ORDER BY c.column_id;
/* The following reports searchable text fields without assuming their names. */
SELECT c.name AS text_column,t.name AS data_type,c.max_length
FROM sys.columns c JOIN sys.types t ON t.user_type_id=c.user_type_id
WHERE c.object_id=OBJECT_ID('dbo.Lotus_LocoFaultData') AND t.name IN ('char','varchar','nchar','nvarchar','text','ntext') ORDER BY c.column_id;
