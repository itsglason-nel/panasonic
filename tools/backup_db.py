"""
PMPC Data Logger — Daily Database Backup Script
Can be scheduled via Windows Task Scheduler or Linux Cron.
Creates a timestamped mysqldump and retains only the last 30 days.
"""
import os
import subprocess
import time
from datetime import datetime, timedelta

# Configuration
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '')
DB_NAME = os.environ.get('DB_NAME', 'plcdata')

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
RETENTION_DAYS = 30

def backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{DB_NAME}_backup_{timestamp}.sql"
    filepath = os.path.join(BACKUP_DIR, filename)

    print(f"Starting backup for {DB_NAME} to {filepath}...")

    # Build mysqldump command
    cmd = [
        'mysqldump',
        f'-h{DB_HOST}',
        f'-u{DB_USER}'
    ]
    if DB_PASS:
        cmd.append(f'-p{DB_PASS}')
    cmd.append(DB_NAME)

    try:
        with open(filepath, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True)
        print("Backup completed successfully.")
    except Exception as e:
        print(f"Error during backup: {e}")
        return

    # Clean up old backups
    print(f"Cleaning up backups older than {RETENTION_DAYS} days...")
    now = time.time()
    for f in os.listdir(BACKUP_DIR):
        f_path = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(f_path) and f.endswith('.sql'):
            file_mtime = os.stat(f_path).st_mtime
            if file_mtime < now - (RETENTION_DAYS * 86400):
                os.remove(f_path)
                print(f"Deleted old backup: {f}")

if __name__ == '__main__':
    backup()
