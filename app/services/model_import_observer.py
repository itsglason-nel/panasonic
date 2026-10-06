import os
import time
import shutil
import threading
from datetime import datetime
from flask import current_app

def _is_file_ready(filepath):
    """Check if file can be opened (not locked by another process)."""
    try:
        with open(filepath, 'a'):
            pass
        return True
    except IOError:
        return False

def _model_import_observer_loop(app):
    """Background loop that polls the input directory for model import CSV files."""
    with app.app_context():
        from app.models import db

        
        try:
            from tools.bulk_model_import.csv_to_sql import convert_csv_to_sql
        except ImportError as e:
            app.logger.error(f"[Model Import Observer] Failed to import csv_to_sql: {e}")
            return

        input_dir = app.config.get('BULK_MODEL_IMPORT_INPUT_DIR')
        archive_dir = app.config.get('BULK_MODEL_IMPORT_ARCHIVE_DIR')

        if not input_dir or not archive_dir:
            app.logger.error("[Model Import Observer] Input or Archive directory not configured.")
            return

        # Ensure directories exist
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(archive_dir, exist_ok=True)

        app.logger.info(f"[Model Import Observer] Started observing {input_dir}")

        while True:
            try:
                config_path = os.path.join(input_dir, 'model_import_config.csv')
                parts_path = os.path.join(input_dir, 'model_import_parts.csv')

                if os.path.exists(config_path) and os.path.exists(parts_path):
                    if _is_file_ready(config_path) and _is_file_ready(parts_path):
                        app.logger.info("[Model Import Observer] Found complete bulk model import files. Processing...")
                        
                        # Generate SQL statements (config is parsed BEFORE parts implicitly by convert_csv_to_sql)
                        sql_lines = convert_csv_to_sql(config_path, parts_path)
                        
                        # Execute SQL statements safely
                        success = True
                        try:
                            for stmt in sql_lines:
                                stmt = stmt.strip()
                                if stmt and not stmt.startswith('--'):
                                    db.session.execute(db.text(stmt))
                            db.session.commit()
                            app.logger.info("[Model Import Observer] Successfully imported model configuration and parts.")
                        except Exception as e:
                            db.session.rollback()
                            app.logger.error(f"[Model Import Observer] SQL Execution failed: {e}")
                            success = False
                            
                        # Archive files with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                        if success:
                            new_config_name = f"model_import_config_{timestamp}.csv"
                            new_parts_name = f"model_import_parts_{timestamp}.csv"
                        else:
                            new_config_name = f"model_import_config_{timestamp}_FAILED.csv"
                            new_parts_name = f"model_import_parts_{timestamp}_FAILED.csv"
                            
                        try:
                            shutil.move(config_path, os.path.join(archive_dir, new_config_name))
                            shutil.move(parts_path, os.path.join(archive_dir, new_parts_name))
                            app.logger.info(f"[Model Import Observer] Archived files to {archive_dir}")
                        except Exception as e:
                            app.logger.error(f"[Model Import Observer] Failed to archive files: {e}")

            except Exception as e:
                app.logger.error(f"[Model Import Observer] Unexpected error in observer loop: {e}")
                
            time.sleep(10)


def start_model_import_observer(app):
    """Start the model import observer in a background daemon thread."""
    thread = threading.Thread(target=_model_import_observer_loop, args=(app,), daemon=True)
    thread.start()
    return thread
