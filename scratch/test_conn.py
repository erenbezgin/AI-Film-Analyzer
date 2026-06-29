import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def test_conn():
    print("Listing tables...")
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="film_arsivi_db"
        )
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} rows")
        cursor.close()
        connection.close()
    except Exception as e:
        print("Error:", str(e))

test_conn()
