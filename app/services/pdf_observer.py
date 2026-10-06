import os
import time
import threading
from flask import current_app

def _pdf_observer_loop(app):
    """Background loop that polls for new PIT records and generates missing or outdated PDFs."""
    with app.app_context():
        from app.models import db
        from sqlalchemy import text
        from app.services.pdf_generator import generate_tag_pdf, get_pdf_filepath
        
        while True:
            try:
                query = text("""
                    SELECT a.serial, a.last_update 
                    FROM (
                        SELECT serial, MAX(max_time) as last_update FROM (
                            SELECT serial, MAX(time) as max_time FROM crs WHERE serial IS NOT NULL GROUP BY serial
                            UNION ALL SELECT serial, MAX(time) FROM att WHERE serial IS NOT NULL GROUP BY serial
                            UNION ALL SELECT serial, MAX(time) FROM gms WHERE serial IS NOT NULL GROUP BY serial
                            UNION ALL SELECT serial, MAX(time) FROM spamsi WHERE serial IS NOT NULL GROUP BY serial
                            UNION ALL SELECT serial, MAX(time) FROM spamso WHERE serial IS NOT NULL GROUP BY serial
                            UNION ALL SELECT serial, MAX(time) FROM wci WHERE serial IS NOT NULL GROUP BY serial
                            UNION ALL SELECT serial, MAX(time) FROM rit WHERE serial IS NOT NULL GROUP BY serial
                            UNION ALL SELECT serial, MAX(time) FROM fit WHERE serial IS NOT NULL GROUP BY serial
                            UNION ALL SELECT serial, MAX(time) FROM pit WHERE serial IS NOT NULL GROUP BY serial
                        ) as all_times
                        GROUP BY serial
                    ) a
                    JOIN (SELECT DISTINCT serial FROM pit WHERE serial IS NOT NULL) p ON a.serial = p.serial
                """)
                
                result = db.session.execute(query).fetchall()
                
                for row in result:
                    serial = row[0]
                    last_update_dt = row[1]
                    
                    pdf_filepath = get_pdf_filepath(serial)
                    file_exists = os.path.exists(pdf_filepath)
                    needs_generation = False
                    
                    if not file_exists:
                        needs_generation = True
                        app.logger.info(f"[PDF Observer] PDF missing for PIT serial {serial}. Generating...")
                    else:
                        file_mtime = os.path.getmtime(pdf_filepath)
                        if last_update_dt and last_update_dt.timestamp() > file_mtime:
                            needs_generation = True
                            app.logger.info(f"[PDF Observer] Data updated for serial {serial}. Regenerating PDF...")
                    
                    if needs_generation:
                        success = generate_tag_pdf(serial, port=8080)
                        if success:
                            app.logger.info(f"[PDF Observer] Successfully generated PDF for {serial}")
                        else:
                            app.logger.error(f"[PDF Observer] Failed to generate PDF for {serial}")
                            
            except Exception as e:
                app.logger.error(f"[PDF Observer] Error in observer loop: {e}")
                db.session.rollback()
                
            # Sleep for 30 seconds before polling again
            time.sleep(30)

def start_pdf_observer(app):
    """Start the background PDF generator thread."""
    observer_thread = threading.Thread(
        target=_pdf_observer_loop, 
        args=(app,), 
        daemon=True,
        name="PDFObserverThread"
    )
    observer_thread.start()
    app.logger.info("[PDF Observer] Background thread started.")
