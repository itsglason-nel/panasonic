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
        from app.services.csv_generator import generate_transfer_slip_csv, generate_middleware_continuous_csv
        from datetime import date, timedelta
        
        # Startup sync: Ensure all existing Transfer Slips have up-to-date CSVs in current format
        try:
            all_existing_slips = TransferSlip.query.all()
            for slip in all_existing_slips:
                generate_transfer_slip_csv(slip.id, overwrite_existing=False)
            generate_middleware_continuous_csv()
            app.logger.info(f"[TS Observer] Synced CSVs for {len(all_existing_slips)} existing transfer slip(s) and continuous middleware master CSV on startup.")
        except Exception as e:
            app.logger.warning(f"[TS Observer] Startup CSV sync warning: {e}")

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
                    
                    # Gather all assigned serials for this line and date to prevent duplicate assignment
                    all_slips_today = TransferSlip.query.filter(
                        func.date(TransferSlip.production_date) == sched.date,
                        TransferSlip.line == sched.lineno
                    ).all()
                    assigned_serials = set()
                    for s in all_slips_today:
                        if s.serials_json:
                            try:
                                assigned_serials.update(json.loads(s.serials_json))
                            except Exception:
                                pass

                    # Fetch serials from PIT that passed for this model
                    pit_records = PIT.query.filter(
                        func.date(PIT.time) == sched.date,
                        PIT.lineno == sched.lineno,
                        PIT.modelcode == sched.modelcode
                    ).all()
                    
                    new_serials = [p.serial for p in pit_records if p.overallstatus == 'GOOD' and p.serial not in assigned_serials]
                    
                    if not existing_slip:
                        if new_serials:
                            app.logger.info(f"[TS Observer] Found completed schedule (ID: {sched.id}, Line: {sched.lineno}, Date: {sched.date}, Model: {sched.modelcode}). Creating Transfer Slip...")
                            
                            # Generate Ref Number (Line No. | 2-digit Year | 2-digit Month | 4-digit Series)
                            year2 = str(sched.date.year)[-2:]
                            month2 = f"{sched.date.month:02d}"
                            prefix = f"{sched.lineno}{year2}{month2}"
                            
                            month_slips_count = TransferSlip.query.filter(
                                TransferSlip.ref_number.startswith(prefix)
                            ).count()
                            
                            series4 = f"{month_slips_count + 1:04d}"
                            ref_number = f"{prefix}{series4}"
                            
                            from app.services.csv_generator import get_plant_code_for_line
                            current_plant = get_plant_code_for_line(sched.lineno, app)
                            # Create Slip per model
                            new_slip = TransferSlip(
                                ref_number=ref_number,
                                plant_code=current_plant,
                                production_date=sched.date,
                                line=sched.lineno,
                                shift="Shift 1",
                                modelcode=sched.modelcode,
                                total_qty=len(new_serials),
                                created_by='System (Auto)',
                                serials_json=json.dumps(new_serials)
                            )
                            
                            db.session.add(new_slip)
                            db.session.commit()
                            app.logger.info(f"[TS Observer] Successfully created Transfer Slip {ref_number} for {sched.modelcode}.")
                            
                            csv_success = generate_transfer_slip_csv(new_slip.id)
                            if csv_success:
                                app.logger.info(f"[TS Observer] Automatically generated CSV for {ref_number}.")
                            else:
                                app.logger.error(f"[TS Observer] Failed to automatically generate CSV for {ref_number}.")
                    else:
                        # Slip already exists for this model; if additional passed units arrived, update it
                        if new_serials:
                            app.logger.info(f"[TS Observer] Updating Transfer Slip {existing_slip.ref_number} with {len(new_serials)} additional units for {sched.modelcode}...")
                            current_serials = json.loads(existing_slip.serials_json) if existing_slip.serials_json else []
                            combined_serials = current_serials + new_serials
                            existing_slip.serials_json = json.dumps(combined_serials)
                            existing_slip.total_qty = len(combined_serials)
                            existing_slip.time = datetime.now()
                            db.session.commit()
                            app.logger.info(f"[TS Observer] Updated Transfer Slip {existing_slip.ref_number}.")
                            
                            generate_transfer_slip_csv(existing_slip.id)
                            
            except Exception as e:
                app.logger.error(f"[TS Observer] Error in observer loop: {e}")
                db.session.rollback()
                
            # Sleep for 10 seconds before polling again
            db.session.remove()
            time.sleep(10)

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
