import os
import csv
import io
import json
from datetime import datetime
from flask import current_app

def get_plant_code_for_line(line_str, app=None):
    """
    Dynamically resolve the default Plant code based on Line No. / Slip Line.
    Resolution priority:
    1. Check `lines` SQL table for a configured plant_code for this line.
    2. Check Flask config / .env `LINE_PLANT_MAPPING`.
    3. Factory default: if line normalizes to 'L1' or 'LINE 1', default to '34P3'.
    4. Fallback: global PLANT_CODE config (default '34P3').
    """
    if not line_str:
        fallback = '34P3'
        if app:
            return app.config.get('PLANT_CODE', fallback)
        try:
            return current_app.config.get('PLANT_CODE', fallback)
        except Exception:
            return fallback

    norm = str(line_str).strip().upper()
    if norm.startswith('LINE'):
        num_part = norm.replace('LINE', '').strip()
        if num_part.isdigit():
            norm = f"L{num_part}"

    # 1. Query database lines table
    try:
        from app.models.line import Line
        line_rec = Line.query.filter(
            (Line.lineno == norm) | (Line.name == str(line_str).strip())
        ).first()
        if line_rec and line_rec.plant_code and line_rec.plant_code.strip():
            return line_rec.plant_code.strip().upper()
    except Exception:
        pass

    # 2. Check config LINE_PLANT_MAPPING
    cfg = app.config if app else (current_app.config if current_app else {})
    mapping = cfg.get('LINE_PLANT_MAPPING', {})
    if norm in mapping and mapping[norm]:
        return str(mapping[norm]).strip().upper()

    # 3. Built-in Factory Default
    if norm == 'L1':
        return '34P3'

    # 4. Fallback to global PLANT_CODE
    return cfg.get('PLANT_CODE', '34P3')


def generate_transfer_slip_csv(slip_id, overwrite_existing=True):
    """
    Generates or updates the 10-column SAP-formatted Transfer Slip CSV file
    for a given TransferSlip and saves it to the dynamically routed path
    configured in TRANSFER_SLIP_CSV_PATH. Supports multi-model batches
    combined under the same daily transfer slip.
    If overwrite_existing=False and the file already exists on disk, the existing
    historical CSV file is preserved untouched.
    """
    from app.models import db
    from app.models.transfer_slip import TransferSlip
    from app.models.pit import PIT
    
    slip = TransferSlip.query.get(slip_id)
    if not slip:
        current_app.logger.error(f"[CSV Generator] Slip ID {slip_id} not found.")
        return False
        
    try:
        serials = json.loads(slip.serials_json) if slip.serials_json else []
    except Exception:
        serials = []
        
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

    # If overwrite_existing is False and the historical CSV already exists on disk, preserve it
    if not overwrite_existing and os.path.exists(filepath):
        current_app.logger.info(f"[CSV Generator] Historical CSV file already exists for slip {slip.ref_number}. Preserving: {filepath}")
        return True
    
    headers = [
        "Plant", "Serial Number", "Material Number", "Actual Quantity",
        "Update Date", "Update Time", "Slip No.", "Slip Line",
        "Production Order", "Operation No."
    ]
    
    # Use the slip's stored plant_code if available, otherwise resolve default based on Slip Line
    plant_code = getattr(slip, 'plant_code', None)
    if not plant_code or not str(plant_code).strip():
        plant_code = get_plant_code_for_line(slip.line)
    slip_finished_date = slip.time.strftime('%d.%m.%Y') if slip.time else (prod_date.strftime('%d.%m.%Y') if prod_date else '--')

    # Query PIT records scoped to this slip's production date and line to avoid cross-day serial collisions
    from sqlalchemy import func
    pit_records = []
    if serials:
        pit_query = PIT.query.filter(PIT.serial.in_(serials))
        if prod_date:
            pit_query = pit_query.filter(func.date(PIT.time) == prod_date)
        if slip.line:
            pit_query = pit_query.filter(PIT.lineno == slip.line)
        pit_records = pit_query.all()

        found_serials = {p.serial for p in pit_records}
        missing_serials = [s for s in serials if s not in found_serials]
        if missing_serials:
            fallback = PIT.query.filter(PIT.serial.in_(missing_serials)).order_by(PIT.time.desc()).all()
            fallback_map = {p.serial: p for p in fallback}
            for ms in missing_serials:
                if ms in fallback_map:
                    pit_records.append(fallback_map[ms])

    pit_map = {p.serial: p for p in pit_records}
    
    models_order = []
    model_serials = {}
    for s in serials:
        pit_rec = pit_map.get(s)
        m_code = (pit_rec.modelcode if pit_rec and pit_rec.modelcode else slip.modelcode) or 'UNKNOWN'
        if m_code not in model_serials:
            model_serials[m_code] = []
            models_order.append(m_code)
        model_serials[m_code].append(s)
        
    if not models_order:
        models_order = [slip.modelcode or 'UNKNOWN']
        model_serials = {slip.modelcode or 'UNKNOWN': []}
        
    rows = []
    for m_code in models_order:
        s_list = model_serials[m_code]
        model_qty = len(s_list) if s_list else slip.total_qty
        
        # Calculate "TO" time for this specific model (last PIT inspection time)
        model_pit_times = [pit_map[s].time for s in s_list if s in pit_map and pit_map[s].time]
        if model_pit_times:
            model_update_time = max(model_pit_times).strftime('%H:%M:%S')
            model_update_date = max(model_pit_times).strftime('%d.%m.%Y')
        else:
            model_update_time = slip.time.strftime('%H:%M:%S') if slip.time else '--:--:--'
            model_update_date = slip_finished_date
            
        if s_list:
            for serial in s_list:
                rows.append([
                    plant_code,
                    serial,
                    m_code,
                    model_qty,
                    model_update_date,
                    model_update_time,
                    slip.ref_number,
                    slip.line,
                    "",
                    ""
                ])
        else:
            rows.append([
                plant_code,
                "",
                m_code,
                model_qty,
                model_update_date,
                model_update_time,
                slip.ref_number,
                slip.line,
                "",
                ""
            ])
            
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(rows)
        current_app.logger.info(f"[CSV Generator] Generated Transfer Slip CSV at: {filepath}")
        
        # Keep the continuous middleware master CSV synchronized
        try:
            generate_middleware_continuous_csv()
        except Exception as e_mw:
            current_app.logger.warning(f"[CSV Generator] Warning syncing middleware continuous CSV: {e_mw}")
            
        return True
    except Exception as e:
        current_app.logger.error(f"[CSV Generator] Failed to write CSV file for slip {slip.ref_number}: {e}")
        return False


def generate_middleware_continuous_csv():
    """
    Generates or updates the single continuous 10-column SAP-formatted Transfer Slip CSV
    containing ALL historical records ordered chronologically from past to latest.
    Saves to the middleware directory configured in TRANSFER_SLIP_MIDDLEWARE_DIR.
    Uses atomic file replacement to ensure zero downtime or locked reads for external consumers.
    """
    from app.models.transfer_slip import TransferSlip
    from app.models.pit import PIT

    default_base_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'tools', 'transfer_slip_data'))
    base_dir = current_app.config.get('TRANSFER_SLIP_DIR', default_base_dir)
    middleware_dir = current_app.config.get('TRANSFER_SLIP_MIDDLEWARE_DIR', os.path.join(base_dir, 'middleware'))
    filename = current_app.config.get('TRANSFER_SLIP_MIDDLEWARE_FILENAME', 'transfer_slip_continuous.csv')
    preview_filename = current_app.config.get('TRANSFER_SLIP_MIDDLEWARE_PREVIEW_FILENAME', 'transfer_slip_continuous_preview.csv')

    os.makedirs(middleware_dir, exist_ok=True)
    filepath = os.path.join(middleware_dir, filename)
    tmp_filepath = os.path.join(middleware_dir, f".{filename}.tmp")
    preview_filepath = os.path.join(middleware_dir, preview_filename)
    preview_tmp_filepath = os.path.join(middleware_dir, f".{preview_filename}.tmp")

    headers = [
        "Plant", "Serial Number", "Material Number", "Actual Quantity",
        "Update Date", "Update Time", "Slip No.", "Slip Line",
        "Production Order", "Operation No."
    ]

    plant_code = current_app.config.get('PLANT_CODE', '34P3')

    # Query all historical transfer slips ordered from past (oldest) to latest
    slips = TransferSlip.query.order_by(
        TransferSlip.production_date.asc(),
        TransferSlip.id.asc()
    ).all()

    if not slips:
        current_app.logger.info("[CSV Generator] No transfer slips found for continuous middleware CSV.")
        for p_tmp, p_dest in [(tmp_filepath, filepath), (preview_tmp_filepath, preview_filepath)]:
            try:
                with open(p_tmp, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(headers)
                os.replace(p_tmp, p_dest)
            except Exception:
                pass
        return True

    # Gather all serials across all slips for batch PIT query
    all_serials = []
    slip_serials_map = {}
    for slip in slips:
        try:
            s_list = json.loads(slip.serials_json) if slip.serials_json else []
        except Exception:
            s_list = []
        slip_serials_map[slip.id] = s_list
        all_serials.extend(s_list)

    # Load all PIT records for these serials ordered by inspection time
    pit_records = PIT.query.filter(PIT.serial.in_(all_serials)).order_by(PIT.time.asc()).all() if all_serials else []

    # Map composite-wise by (serial, line, date) for exact production run matching, with line/serial fallbacks
    pit_composite_map = {}
    pit_fallback_map = {}
    for p in pit_records:
        if p.time:
            pit_composite_map[(p.serial, p.lineno, p.time.date())] = p
        pit_fallback_map[(p.serial, p.lineno)] = p
        pit_fallback_map[p.serial] = p

    continuous_rows = []

    # Iterate over each slip in chronological order (past to latest)
    for slip in slips:
        serials = slip_serials_map.get(slip.id, [])
        prod_date = slip.production_date
        slip_finished_date = slip.time.strftime('%d.%m.%Y') if slip.time else (prod_date.strftime('%d.%m.%Y') if prod_date else '--')
        # Use each slip's stored plant_code so historical records never change if .env PLANT_CODE updates
        slip_plant = getattr(slip, 'plant_code', None)
        if not slip_plant or not str(slip_plant).strip():
            slip_plant = get_plant_code_for_line(slip.line)

        # Resolve PIT records specifically for this slip's line and date
        slip_pit_map = {}
        for s in serials:
            rec = None
            if prod_date:
                rec = pit_composite_map.get((s, slip.line, prod_date))
            if not rec:
                rec = pit_fallback_map.get((s, slip.line))
            if not rec:
                rec = pit_fallback_map.get(s)
            if rec:
                slip_pit_map[s] = rec

        models_order = []
        model_serials = {}
        for s in serials:
            pit_rec = slip_pit_map.get(s)
            m_code = (pit_rec.modelcode if pit_rec and pit_rec.modelcode else slip.modelcode) or 'UNKNOWN'
            if m_code not in model_serials:
                model_serials[m_code] = []
                models_order.append(m_code)
            model_serials[m_code].append(s)

        if not models_order:
            models_order = [slip.modelcode or 'UNKNOWN']
            model_serials = {slip.modelcode or 'UNKNOWN': []}

        for m_code in models_order:
            s_list = model_serials[m_code]
            model_qty = len(s_list) if s_list else slip.total_qty

            model_pit_times = [slip_pit_map[s].time for s in s_list if s in slip_pit_map and slip_pit_map[s].time]
            if model_pit_times:
                model_update_time = max(model_pit_times).strftime('%H:%M:%S')
                model_update_date = max(model_pit_times).strftime('%d.%m.%Y')
            else:
                model_update_time = slip.time.strftime('%H:%M:%S') if slip.time else '--:--:--'
                model_update_date = slip_finished_date

            if s_list:
                for serial in s_list:
                    continuous_rows.append([
                        slip_plant,
                        serial,
                        m_code,
                        model_qty,
                        model_update_date,
                        model_update_time,
                        slip.ref_number,
                        slip.line,
                        "",
                        ""
                    ])
            else:
                continuous_rows.append([
                    slip_plant,
                    "",
                    m_code,
                    model_qty,
                    model_update_date,
                    model_update_time,
                    slip.ref_number,
                    slip.line,
                    "",
                    ""
                ])

    # 1. Write the master continuous CSV (used by SAP / middleware)
    master_success = False
    try:
        with open(tmp_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(continuous_rows)
        os.replace(tmp_filepath, filepath)
        current_app.logger.info(f"[CSV Generator] Updated Continuous Middleware CSV ({len(continuous_rows)} rows) at: {filepath}")
        master_success = True
    except PermissionError:
        current_app.logger.warning(f"[CSV Generator] Continuous middleware master file locked by another process: {filepath}")
    except Exception as e:
        current_app.logger.error(f"[CSV Generator] Failed to write continuous middleware master CSV: {e}")
        if os.path.exists(tmp_filepath):
            try:
                os.remove(tmp_filepath)
            except Exception:
                pass

    # 2. Synchronize the client preview CSV (used for client/human raw inspection without locking master)
    preview_success = False
    try:
        with open(preview_tmp_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(continuous_rows)
        os.replace(preview_tmp_filepath, preview_filepath)
        current_app.logger.info(f"[CSV Generator] Updated Client Preview CSV ({len(continuous_rows)} rows) at: {preview_filepath}")
        preview_success = True
    except PermissionError:
        current_app.logger.warning(f"[CSV Generator] Client preview file locked by viewer (e.g. Excel): {preview_filepath}")
    except Exception as e:
        current_app.logger.error(f"[CSV Generator] Failed to write client preview CSV: {e}")
        if os.path.exists(preview_tmp_filepath):
            try:
                os.remove(preview_tmp_filepath)
            except Exception:
                pass

    return master_success or preview_success
