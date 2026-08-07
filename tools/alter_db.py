import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get('DB_HOST', '127.0.0.1')
port = int(os.environ.get('DB_PORT', 3306))
user = os.environ.get('DB_USER', 'root')
password = os.environ.get('DB_PASSWORD', '')
db_name = os.environ.get('DB_NAME', 'plcdata')

def main():
    print(f"Connecting to DB {db_name} at {host}:{port} with user {user}")
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db_name)
    cursor = conn.cursor()

    try:
        # Check and add inspector column to CRS
        try:
            cursor.execute("ALTER TABLE crs ADD COLUMN inspector VARCHAR(20) NULL;")
            print("Added 'inspector' to 'crs'.")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("'inspector' already exists in 'crs'.")
            else:
                raise e
                
        # Check and add inspector column to GMS
        try:
            cursor.execute("ALTER TABLE gms ADD COLUMN inspector VARCHAR(20) NULL;")
            print("Added 'inspector' to 'gms'.")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("'inspector' already exists in 'gms'.")
            else:
                raise e

        # Check and add inspector column to ATT
        try:
            cursor.execute("ALTER TABLE att ADD COLUMN inspector VARCHAR(20) NULL;")
            print("Added 'inspector' to 'att'.")
        except pymysql.err.OperationalError as e:
            if "Duplicate column name" in str(e):
                print("'inspector' already exists in 'att'.")
            else:
                raise e

        # Now, update the previously inserted test data to have an inspector
        cursor.execute("UPDATE crs SET inspector = 'Admin' WHERE serial LIKE 'TEST-FG%'")
        cursor.execute("UPDATE gms SET inspector = 'Admin' WHERE serial LIKE 'TEST-FG%'")
        cursor.execute("UPDATE att SET inspector = 'Admin' WHERE serial LIKE 'TEST-FG%'")

        conn.commit()
        print("Database schema updated successfully.")

    except Exception as e:
        conn.rollback()
        print("Error: ", e)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
