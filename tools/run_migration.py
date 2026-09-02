import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get('DB_HOST', '127.0.0.1')
port = int(os.environ.get('DB_PORT', 3306))
user = os.environ.get('DB_USER', 'root')
password = os.environ.get('DB_PASSWORD', '')
db_name = os.environ.get('DB_NAME', 'plcdata')

print(f"Connecting to database '{db_name}' at {host}:{port} as '{user}'...")

try:
    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db_name)
    cursor = conn.cursor()
    
    # 1. Update users
    print("Updating user roles...")
    cursor.execute("UPDATE `users` SET `role` = 'admin' WHERE `role` = 'super_admin';")
    
    # 2. Drop remarks from gms (ignore error if it doesn't exist)
    print("Dropping remarks column from gms...")
    try:
        cursor.execute("ALTER TABLE `gms` DROP COLUMN `remarks`;")
    except Exception as e:
        print(f" (Note: {e})")
        
    # 3. Rename modelref to serialref (ignore if already renamed)
    print("Renaming modelref to serialref...")
    try:
        cursor.execute("RENAME TABLE `modelref` TO `serialref`;")
    except Exception as e:
        print(f" (Note: {e})")
        
    # 4. Create att table
    print("Creating att table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS `att` (
        `id`        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        `modelcode` VARCHAR(14) NULL,
        `serial`    VARCHAR(14) NULL,
        `status1`    VARCHAR(12) NULL,
        `status2`    VARCHAR(12) NULL,
        `status3`    VARCHAR(12) NULL,
        `time`      TIMESTAMP NULL,
        `inspector`   VARCHAR(20) NULL,
        `lineno`	  VARCHAR(4) NOT NULL,
        `brazzer1`    VARCHAR(20) NULL,
        `brazzer2`    VARCHAR(20) NULL,
        `brazzer3`    VARCHAR(20) NULL,
        `brazzer4`    VARCHAR(20) NULL,
        `brazzer5`    VARCHAR(20) NULL,
        `brazzer6`    VARCHAR(20) NULL,
        `brazzer7`    VARCHAR(20) NULL,
        INDEX idx_att_serial (serial)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    conn.commit()
    print("\nDatabase migration completed successfully!")
    conn.close()
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
