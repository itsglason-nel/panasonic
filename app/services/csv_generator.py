import os
import csv
import io
import json
from datetime import datetime
from flask import current_app

def generate_transfer_slip_csv(slip_id):
    """
    Generates a 2-row CSV file for a given TransferSlip and saves it to the
    dynamically routed path configured in TRANSFER_SLIP_CSV_PATH.
    """
    from app.models import db
    from app.models.transfer_slip import TransferSlip
    from app.models.pit import PIT
    from app.models.crs import CRS
    
    slip = TransferSlip.query.get(slip_id)
    if not slip:
        current_app.logger.error(f"[CSV Generator] Slip ID {slip_id} not found.")
        return False
        
    try:
        serials = json.loads(slip.serials_json) if slip.serials_json else []
    except Exception:
        serials = []
        
    start_time = '--:--:--'
    end_time = '--:--:--'
    
    if serials:
        pit_records = PIT.query.filter(PIT.serial.in_(serials)).all()
        pit_times = [p.time for p in pit_records if p.time]
        if pit_times:
            end_time = max(pit_times).strftime('%H:%M:%S')
            
        crs_records = CRS.query.filter(CRS.serial.in_(serials)).all()
        crs_times = [c.time for c in crs_records if c.time]
        if crs_times:
            start_time = min(crs_times).strftime('%H:%M:%S')
            
    finished_date = slip.time.strftime('%Y-%m-%d') if slip.time else '--'
    
    default_base_path = os.path.abspath(os.path.join(current_app.root_path, '..', 'tools', 'transfer_slip_data', 'actual'))
    base_path = current_app.config.get('TRANSFER_SLIP_CSV_PATH', default_base_path)
    
    line_str = str(slip.line).strip().upper()
    if line_str.startswith('L') and len(line_str) > 1 and line_str[1:].isdigit():
        folder_line = line_str.replace('L', 'Line ')
    else:
        folder_line = line_str
        
    prod_date = slip.production_date
    if prod_date:
        year = str(prod_date.year)
        month = prod_date.strftime('%B')
        day = prod_date.strftime('%d')
    else:
        year, month, day = 'YYYY', 'MM', 'DD'
        
    hierarchy_path = os.path.join(base_path, folder_line, year, month, day)
    os.makedirs(hierarchy_path, exist_ok=True)
    
    filepath = os.path.join(hierarchy_path, f"{slip.ref_number}.csv")
    
    headers = [
        "Reference Number", "Production Date", "Line", "Shift", 
        "Model", "Total Qty", "Created By", "Start Time", 
        "End Time", "Finished Date", "Serials"
    ]
    
    serials_str = ", ".join(serials)
    
    row_values = [
        slip.ref_number,
        prod_date.strftime('%Y-%m-%d') if prod_date else '--',
        slip.line,
        slip.shift,
        slip.modelcode,
        slip.total_qty,
        slip.created_by or 'System',
        start_time,
        end_time,
        finished_date,
        serials_str
    ]
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerow(row_values)
        current_app.logger.info(f"[CSV Generator] Generated Transfer Slip CSV at: {filepath}")
        return True
    except Exception as e:
        current_app.logger.error(f"[CSV Generator] Failed to write CSV file for slip {slip.ref_number}: {e}")
        return False
