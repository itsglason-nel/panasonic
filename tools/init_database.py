import pymysql  # type: ignore[import-untyped]
import os
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get('DB_HOST', '127.0.0.1')
port = int(os.environ.get('DB_PORT', 3306))
user = os.environ.get('DB_USER', 'root')
password = os.environ.get('DB_PASSWORD', '')
db_name = os.environ.get('DB_NAME', 'plcdata')

try:
    # Connect WITHOUT specifying a database, so we can create it if it doesn't exist
    conn = pymysql.connect(host=host, port=port, user=user, password=password)
    cursor = conn.cursor()
    
    # Ensure MySQL read-only mode is disabled to prevent Error 1290
    try:
        cursor.execute("SET GLOBAL super_read_only = 0;")
        cursor.execute("SET GLOBAL read_only = 0;")
    except Exception as e:
        print(f"Warning: Could not disable read_only (requires privileges): {e}")
        
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    print(f"Verified database '{db_name}' exists.")
    conn.close()
except Exception as e:
    print(f"Error creating database: {e}")
