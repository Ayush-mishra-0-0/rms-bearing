from scratch_db_explore import get_connection


def main():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT fi.is_enabled,fi.change_tracking_state_desc,fc.column_id,c.name AS fulltext_column FROM sys.fulltext_indexes fi JOIN sys.fulltext_index_columns fc ON fc.object_id=fi.object_id JOIN sys.columns c ON c.object_id=fc.object_id AND c.column_id=fc.column_id WHERE fi.object_id=OBJECT_ID('dbo.Lotus_LocoFaultData');
        SELECT s.name AS statistic_name,COL_NAME(sc.object_id,sc.column_id) AS first_column FROM sys.stats s JOIN sys.stats_columns sc ON sc.object_id=s.object_id AND sc.stats_id=s.stats_id AND sc.stats_column_id=1 WHERE s.object_id=OBJECT_ID('dbo.Lotus_LocoFaultData');
    """)
    for row in cursor:
        print("|".join("" if value is None else str(value) for value in row))
    connection.close()


if __name__ == "__main__":
    main()
