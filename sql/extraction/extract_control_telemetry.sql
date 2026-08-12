/* Replace control loco/time with a verified matched control from 05_loco_inventory.sql. */
DECLARE @loco varchar(30)='00000',@from datetime='2025-01-01',@to datetime='2025-01-02'; SELECT * FROM dbo.Locoprocessdata WHERE CAST(locoid AS varchar(30))=@loco AND devicetime>=@from AND devicetime<@to ORDER BY devicetime;
