import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get('DB_HOST', '127.0.0.1')
port = int(os.environ.get('DB_PORT', 3306))
user = os.environ.get('DB_USER', 'root')
password = os.environ.get('DB_PASSWORD', '')
db_name = os.environ.get('DB_NAME', 'plcdata')

def table_exists(cursor, table_name):
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
    """, (db_name, table_name))
    return cursor.fetchone()[0] == 1

def main():
    print(f"Connecting to DB {db_name} at {host}:{port} with user {user}")
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db_name)
    cursor = conn.cursor()

    try:
        has_modelref = table_exists(cursor, 'modelref')
        has_serialref = table_exists(cursor, 'serialref')

        if has_serialref:
            print("Table 'serialref' already exists. No rename needed or it has already been done.")
        elif has_modelref:
            print("Renaming table 'modelref' to 'serialref'...")
            cursor.execute("RENAME TABLE `modelref` TO `serialref`;")
            print("Successfully renamed 'modelref' to 'serialref'.")
        else:
            print("Neither 'modelref' nor 'serialref' table found.")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Error: ", e)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
