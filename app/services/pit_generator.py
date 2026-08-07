"""
PMPC Data Logger — PIT Generator Service
Generates structured JSON data for the Production Information Tag (PIT).
An external service reads the `pit_records` table to print physical tags.

NOTE: This service depends on operator-station models (PITRecord, UnitPart,
InspectionRecord, GasChargeRecord) that are not yet implemented. The imports
are lazy-loaded so this file can be safely imported without crashing the app.
"""
import json
from app.models import db

def generate_and_save_pit(unit):
    """
    Generate PIT data for a completed unit and save it to the pit_records table.
    Should be called when a unit reaches COMPLETE status (e.g. after SFIS5).
    Returns None if operator-station models are not yet implemented.
    """
    # Lazy imports — these models are not yet created; guard so startup never fails.
    # type: ignore comments suppress Pyright static-analysis errors; the try/except
    # handles the runtime ImportError when the modules don't exist yet.
    try:
        from app.models.pit import PITRecord          # type: ignore[import-untyped]
        from app.models.unit_part import UnitPart     # type: ignore[import-untyped]
        from app.models.inspection import InspectionRecord  # type: ignore[import-untyped]
        from app.models.gas_charge import GasChargeRecord   # type: ignore[import-untyped]
    except ImportError:
        return None  # Operator station models not yet implemented

    if unit.overall_status != 'COMPLETE':
        return None

    # Gather Parts
    parts_data = []
    unit_parts = UnitPart.query.filter_by(unit_id=unit.id).all()
    for up in unit_parts:
        parts_data.append({
            'module': up.station_scan.station.module_code if up.station_scan else 'UNKNOWN',
            'part_type': up.part.part_type,
            'part_number': up.part.part_number,
            'description': up.part.description,
            'serial_or_lot': up.part_serial_number or (up.lot.lot_barcode if up.lot else None) or up.part_qr_raw
        })
        
    # Gather Gas Charge
    gas_charge = GasChargeRecord.query.filter_by(unit_id=unit.id).first()
    gas_data = None
    if gas_charge:
        gas_data = {
            'target_kg': float(gas_charge.target_weight_kg),
            'actual_kg': float(gas_charge.actual_weight_kg),
            'result': gas_charge.result
        }
        
    # Gather Inspections
    inspections = InspectionRecord.query.filter_by(unit_id=unit.id).all()
    insp_data = {}
    for insp in inspections:
        insp_data[insp.test_type] = {
            'result': insp.result,
            'recorded_at': str(insp.recorded_at)
        }
        if insp.test_type == 'RUNNING':
            insp_data['RUNNING'].update({
                'cooling_current_a': float(insp.current_cooling_a) if insp.current_cooling_a else None,
                'cooling_power_w': float(insp.power_cooling_w) if insp.power_cooling_w else None,
            })
            
    # Build PIT JSON
    pit_json = json.dumps({
        'serial_number': unit.serial_number,
        'model_number': unit.model.model_number,
        'production_date': str(unit.production_date),
        'shift': unit.shift,
        'line': unit.line.name if unit.line else str(unit.line_id),
        'parts': parts_data,
        'gas_charge': gas_data,
        'inspections': insp_data,
        'generated_at': str(db.func.current_timestamp())
    })
    
    # Save to database
    pit = PITRecord.query.filter_by(unit_id=unit.id).first()
    if pit:
        pit.pit_json = pit_json
    else:
        pit = PITRecord(
            unit_id=unit.id,
            serial_number=unit.serial_number,
            model_id=unit.model_id,
            production_date=unit.production_date,
            shift=unit.shift,
            line_id=unit.line_id,
            pit_json=pit_json
        )
        db.session.add(pit)
        
    db.session.commit()
    return pit
