import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USERNAME')};"
        f"PWD={os.getenv('DB_PASSWORD')};"
        f"TrustServerCertificate=yes;"
    )

def explore_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("Connected successfully!")
        
        # 1. Get Top 20 tables by row count
        print("\n--- Top 20 Tables by Row Count ---")
        cursor.execute("""
            SELECT t.name AS TableName, p.rows AS RowCounts
            FROM sys.tables t
            INNER JOIN sys.indexes i ON t.object_id = i.object_id
            INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
            WHERE t.is_ms_shipped = 0 AND i.type IN (0, 1)
            GROUP BY t.name, p.rows
            ORDER BY p.rows DESC
        """)
        rows = cursor.fetchmany(20)
        top_tables = []
        for r in rows:
            print(f"{r.TableName}: {r.RowCounts} rows")
            top_tables.append(r.TableName)
            
        # 2. Find tables with 'loco', 'fault', 'bearing', 'report', 'slam' in name
        print("\n--- Tables of Interest (Names matching keywords) ---")
        cursor.execute("""
            SELECT name 
            FROM sys.tables 
            WHERE is_ms_shipped = 0 
            AND (LOWER(name) LIKE '%loco%' OR LOWER(name) LIKE '%fault%' OR LOWER(name) LIKE '%bearing%' OR LOWER(name) LIKE '%report%' OR LOWER(name) LIKE '%slam%')
        """)
        interest_tables = [r[0] for r in cursor.fetchall()]
        for t in interest_tables:
            print(t)
            
        # 3. For a few top/interesting tables, let's see their columns
        # Prioritize tables that look like they have fault or loco logs
        tables_to_inspect = list(set(top_tables[:10] + interest_tables[:10]))
        print("\n--- Columns in Selected Tables ---")
        for t in tables_to_inspect:
            print(f"\nTable: {t}")
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{t}'
            """)
            cols = cursor.fetchall()
            date_cols = []
            for c in cols:
                print(f"  {c.COLUMN_NAME} ({c.DATA_TYPE})")
                if 'date' in c.COLUMN_NAME.lower() or 'time' in c.COLUMN_NAME.lower():
                    date_cols.append(c.COLUMN_NAME)
                
            # Try to get top 1 row
            try:
                cursor.execute(f"SELECT TOP 1 * FROM [{t}]")
                top1 = cursor.fetchone()
                print(f"  Sample Row: {top1}")
            except Exception as e:
                print(f"  Could not fetch sample row: {e}")
                
            # Check most recent data if there is a date column
            if date_cols:
                try:
                    date_col = date_cols[0]
                    cursor.execute(f"SELECT MAX([{date_col}]) FROM [{t}]")
                    max_date = cursor.fetchone()[0]
                    print(f"  Max [{date_col}]: {max_date}")
                except Exception as e:
                    print(f"  Could not fetch max date: {e}")

        conn.close()
    except Exception as e:
        print(f"Error connecting or executing: {e}")

if __name__ == '__main__':
    explore_db()
