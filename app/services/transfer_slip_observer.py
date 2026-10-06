import os
import time
import json
import threading
from datetime import datetime
from flask import current_app

def _transfer_slip_observer_loop(app):
    """Background loop that polls for completed WorkSchedules and automatically generates Transfer Slips and CSVs."""
    with app.app_context():
        from app.models import db
        from app.models.worksched import WorkSched
        from app.models.transfer_slip import TransferSlip
        from app.models.pit import PIT
        from sqlalchemy import func
        from app.services.csv_generator import generate_transfer_slip_csv
        from datetime import date, timedelta
        
        while True:
            try:
                # OPTIMIZATION: Only look at schedules from the last 7 days to prevent full-table scans in production.
                recent_cutoff = date.today() - timedelta(days=7)
                
                # Find all completed schedules in the recent window
                completed_schedules = WorkSched.query.filter(
                    WorkSched.act >= WorkSched.plan, 
                    WorkSched.plan > 0,
                    WorkSched.date >= recent_cutoff
                ).all()
                
                for sched in completed_schedules:
                    # Check if a transfer slip already exists for this date, line, and model
                    existing_slip = TransferSlip.query.filter(
                        func.date(TransferSlip.production_date) == sched.date,
                        TransferSlip.line == sched.lineno,
                        TransferSlip.modelcode == sched.modelcode
                    ).first()
                    
                    if not existing_slip:
                        
                        # Gather all assigned serials for this date to avoid duplicates
                        all_slips_today = TransferSlip.query.filter(
                            func.date(TransferSlip.production_date) == sched.date
                        ).all()
                        
                        assigned_serials = set()
                        for s in all_slips_today:
                            if s.serials_json:
                                try:
                                    assigned_serials.update(json.loads(s.serials_json))
                                except:
                                    pass

                        # Fetch serials from PIT that passed
                        pit_records = PIT.query.filter(
                            func.date(PIT.time) == sched.date,
                            PIT.lineno == sched.lineno,
                            PIT.modelcode == sched.modelcode
                        ).all()
                        
                        serials = [p.serial for p in pit_records if p.overallstatus == 'GOOD' and p.serial not in assigned_serials]
                        total_qty = len(serials)
                        
                        if total_qty > 0:
                            app.logger.info(f"[TS Observer] Found completed schedule (ID: {sched.id}, Line: {sched.lineno}, Date: {sched.date}, Model: {sched.modelcode}). Generating Transfer Slip...")
                            
                            # Generate Ref Number
                            year2 = str(sched.date.year)[-2:]
                            month2 = f"{sched.date.month:02d}"
                            prefix = f"{sched.lineno}{year2}{month2}"
                            
                            month_slips_count = TransferSlip.query.filter(
                                TransferSlip.ref_number.startswith(prefix)
                            ).count()
                            
                            series4 = f"{month_slips_count + 1:04d}"
                            ref_number = f"{prefix}{series4}"
                            
                            # Create Slip
                            new_slip = TransferSlip(
                                ref_number=ref_number,
                                production_date=sched.date,
                                line=sched.lineno,
                                shift="Shift 1", # Assuming Shift 1 for automated creation, or look up shift
                                modelcode=sched.modelcode,
                                total_qty=total_qty,
                                created_by='System (Auto)',
                                serials_json=json.dumps(serials)
                            )
                            
                            db.session.add(new_slip)
                            db.session.commit()
                            
                            app.logger.info(f"[TS Observer] Successfully created Transfer Slip {ref_number}.")
                            
                            # Trigger CSV Generation
                            csv_success = generate_transfer_slip_csv(new_slip.id)
                            if csv_success:
                                app.logger.info(f"[TS Observer] Automatically generated CSV for {ref_number}.")
                            else:
                                app.logger.error(f"[TS Observer] Failed to automatically generate CSV for {ref_number}.")
                        else:
                            # Might be that all PIT records are not GOOD yet or already assigned. We'll check again next loop.
                            pass
                            
            except Exception as e:
                app.logger.error(f"[TS Observer] Error in observer loop: {e}")
                db.session.rollback()
                
            # Sleep for 30 seconds before polling again
            time.sleep(30)

def start_transfer_slip_observer(app):
    """Start the background Transfer Slip observer thread."""
    observer_thread = threading.Thread(
        target=_transfer_slip_observer_loop, 
        args=(app,), 
        daemon=True,
        name="TransferSlipObserverThread"
    )
    observer_thread.start()
    app.logger.info("[TS Observer] Background thread started.")
