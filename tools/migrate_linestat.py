import os
import sys
from sqlalchemy import text

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db

def run_migration():
    app = create_app()
    with app.app_context():
        print("Running migration for LineStat...")
        migration_file = os.path.join(os.path.dirname(__file__), '..', 'migrations', '003_linestat.sql')
        
        with open(migration_file, 'r') as f:
            sql_statements = f.read().split(';')
            
        for statement in sql_statements:
            if statement.strip():
                try:
                    db.session.execute(text(statement))
                    db.session.commit()
                except Exception as e:
                    print(f"Error executing statement: {e}")
                    db.session.rollback()
        print("Migration complete.")

if __name__ == '__main__':
    run_migration()
