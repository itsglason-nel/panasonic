"""
Migration: modelref -> partref + new modelref (serial start)
Run this ONCE to fix the database schema.
Usage: py migrate_partref.py
"""
import os
import sys
import pymysql
from dotenv import load_dotenv

load_dotenv()

HOST     = os.environ.get('DB_HOST', '127.0.0.1')
PORT     = int(os.environ.get('DB_PORT', 3306))
USER     = os.environ.get('DB_USER', 'root')
PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME  = os.environ.get('DB_NAME', 'plcdata')

print(f"Connecting to MySQL at {HOST}:{PORT}, database '{DB_NAME}' ...")

try:
    conn = pymysql.connect(
        host=HOST, port=PORT, user=USER, password=PASSWORD,
        database=DB_NAME, charset='utf8mb4'
    )
except Exception as e:
    print(f"[ERROR] Could not connect: {e}")
    sys.exit(1)

cur = conn.cursor()

def table_exists(name):
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = %s AND table_name = %s",
        (DB_NAME, name)
    )
    row = cur.fetchone()
    return bool(row and row[0] > 0)

def column_exists(table, col):
    cur.execute(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = %s AND column_name = %s",
        (DB_NAME, table, col)
    )
    row = cur.fetchone()
    return bool(row and row[0] > 0)

print()
print("=" * 60)
print("Step 1: Rename old BOM table  modelref -> partref")
print("=" * 60)

if table_exists('modelref') and not table_exists('partref'):
    # Check if old modelref has BOM columns (module, partno) — not the new schema
    if column_exists('modelref', 'module'):
        print("  Found old modelref (BOM table). Renaming to partref ...")
        cur.execute("RENAME TABLE `modelref` TO `partref`")
        conn.commit()
        print("  [OK] Renamed modelref -> partref")
    else:
        print("  modelref exists but looks like the new schema already. Skipping rename.")
elif table_exists('partref'):
    print("  [OK] partref already exists. Skipping rename.")
else:
    print("  modelref does not exist — nothing to rename.")

print()
print("=" * 60)
print("Step 2: Create new modelref (serial start reference)")
print("=" * 60)

if not table_exists('modelref'):
    print("  Creating new modelref table ...")
    cur.execute("""
        CREATE TABLE `modelref` (
            `id`          INT AUTO_INCREMENT PRIMARY KEY,
            `modelcode`   VARCHAR(14) NULL,
            `area`        VARCHAR(14) NULL,
            `serialstart` VARCHAR(6)  NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    conn.commit()
    print("  [OK] Created new modelref table (modelcode, area, serialstart)")
else:
    # Table exists — make sure it has the new columns
    print("  modelref table already exists. Checking columns ...")
    if not column_exists('modelref', 'area'):
        print("  Adding 'area' column ...")
        cur.execute("ALTER TABLE `modelref` ADD COLUMN `area` VARCHAR(14) NULL")
        conn.commit()
        print("  [OK] Added 'area' column")
    else:
        print("  [OK] 'area' column already present")

    if not column_exists('modelref', 'serialstart'):
        print("  Adding 'serialstart' column ...")
        cur.execute("ALTER TABLE `modelref` ADD COLUMN `serialstart` VARCHAR(6) NULL")
        conn.commit()
        print("  [OK] Added 'serialstart' column")
    else:
        print("  [OK] 'serialstart' column already present")

    # Remove old BOM columns if they still exist on this table
    for old_col in ('module', 'partno', 'partdesc', 'usage', 'tag'):
        if column_exists('modelref', old_col):
            print(f"  Dropping old column '{old_col}' from modelref ...")
            cur.execute(f"ALTER TABLE `modelref` DROP COLUMN `{old_col}`")
            conn.commit()
            print(f"  [OK] Dropped '{old_col}'")

print()
print("=" * 60)
print("Step 3: Recreate sort view for partref")
print("=" * 60)

cur.execute("DROP VIEW IF EXISTS `modelref_sort`")
if table_exists('partref'):
    cur.execute("""
        CREATE VIEW `partref_sort` AS
        SELECT `id`, `modelcode`, `module`, `partno`, `partdesc`, `usage`, `tag`
        FROM `partref`
        ORDER BY
            CASE
                WHEN `module` = 'CRS'   THEN 1
                WHEN `module` = 'gms'   THEN 2
                WHEN `module` = 'spams' THEN 3
                WHEN `module` = 'cb'    THEN 4
                ELSE 5
            END ASC, `id` ASC
    """)
    conn.commit()
    print("  [OK] Recreated view: partref_sort (pointing to partref)")
else:
    print("  [WARN] partref table not found — skipping view creation")

cur.close()
conn.close()

print()
print("=" * 60)
print("Migration complete! Restart the web server.")
print("=" * 60)
