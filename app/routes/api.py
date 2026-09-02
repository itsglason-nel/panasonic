"""API routes — real JSON endpoints for all station data."""
import os
import redis as _redis_lib
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, date as date_type
from decimal import Decimal
from app.models import db
from app.models.crs import CRS
from app.models.att import ATT
from app.models.gms import GMS

from app.models.spamsi import SPAMSI
from app.models.packaging import Packaging
from app.models.spamso import SPAMSO
from app.models.partref import PartRef
from app.models.worksched import WorkSched
from app.services.barcode_parser import decode_safety_part_qr
from app.services.pit_generator import generate_and_save_pit

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ── Redis singleton ────────────────────────────────────────────────────────────────────
_redis_client = None

def _get_redis():
    """Return a module-level Redis client, creating it on first call."""
    global _redis_client
    if _redis_client is None:
        _redis_client = _redis_lib.Redis(
            host=os.environ.get('REDIS_HOST', '127.0.0.1'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            decode_responses=True,
            socket_timeout=0.5,
        )
    return _redis_client


# ── Unit lookup ───────────────────────────────────────────────────────────────
@api_bp.route('/unit/<serial>', methods=['GET'])
@login_required
def get_unit(serial):
    """Look up a unit by serial — searches CRS table as primary source."""
    unit = CRS.query.filter_by(serial=serial).order_by(CRS.time.desc()).first()
    if not unit:
        return jsonify({'found': False, 'serial': serial})

    # Check downstream statuses
    att_record = ATT.query.filter_by(serial=serial).order_by(ATT.time.desc()).first()
    gms_record = GMS.query.filter_by(serial=serial).order_by(GMS.time.desc()).first()
    spamsi_record = SPAMSI.query.filter_by(serial=serial).order_by(SPAMSI.time.desc()).first()
    spamso_record = SPAMSO.query.filter_by(serial=serial).order_by(SPAMSO.time.desc()).first()

    return jsonify({
        'found': True,
        'serial': serial,
        'model_number': unit.modelcode,
        'compressor_model': unit.compmod,
        'compressor_serial': unit.compserial,
        'fan1_model': unit.fan1mod,
        'fan1_serial': unit.fan1serial,
        'fan2_model': unit.fan2mod,
        'fan2_serial': unit.fan2serial,
        'scanned_at': str(unit.time),
        'att_status': att_record.status if att_record else None,
        'gms_status': gms_record.status if gms_record else None,
        'gms_charge_kg': float(gms_record.gascharge) if gms_record else None,
        'spamsi_status': 'GOOD' if spamsi_record else None,
        'spamso_status': 'GOOD' if spamso_record else None,
    })


# ── BOM lookup ────────────────────────────────────────────────────────────────
@api_bp.route('/bom/<model_number>/<module_code>', methods=['GET'])
@login_required
def get_bom(model_number, module_code):
    entries = PartRef.query.filter_by(modelcode=model_number, module=module_code).order_by(PartRef.id).all()
    return jsonify({
        'model_number': model_number,
        'module_code': module_code,
        'parts': [{
            'bom_id': e.id,
            'part_number': e.partno,
            'description': e.partdesc,
            'usage_qty': float(e.usage),
            'tag': e.tag,
        } for e in entries],
    })


# ── Serial Reference (Serial Start) lookup ─────────────────────────────────────
@api_bp.route('/serialref/<modelcode>', methods=['GET'])
@login_required
def get_serialref(modelcode):
    """Return all serial-start entries for a given model code."""
    from app.models.modelref import ModelRef
    entries = ModelRef.query.filter_by(modelcode=modelcode).order_by(ModelRef.area).all()
    if not entries:
        return jsonify({'found': False, 'modelcode': modelcode})
    return jsonify({
        'found': True,
        'modelcode': modelcode,
        'entries': [{
            'id':          e.id,
            'area':        e.area,
            'serialstart': e.serialstart,
        } for e in entries],
    })


# ── Schedule lookup ────────────────────────────────────────────────────────────
@api_bp.route('/schedule/<int:lid>/<date_str>', methods=['GET'])
@login_required
def get_schedule(lid, date_str):
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    schedules = WorkSched.query.filter_by(
        lineno=f"L{lid}", date=query_date
    ).order_by(WorkSched.seq).all()

    return jsonify({
        'line_id': lid,
        'date': str(query_date),
        'schedules': [{
            'id': s.id,
            'seq': s.seq,
            'model_number': s.modelcode,
            'planned_qty': s.plan,
            'actual_qty': s.act,
            'variance': s.act - s.plan,
            'takt_time': s.takttime,
        } for s in schedules],
    })


# ── Scoreboard summary ────────────────────────────────────────────────────────
@api_bp.route('/scoreboard/<int:line_id>', methods=['GET'])
@login_required
def get_scoreboard(line_id):
    """Return today's plan/actual totals for a given line."""
    today = date_type.today()
    lineno = f"L{line_id}"
    schedules = WorkSched.query.filter_by(lineno=lineno, date=today).all()

    total_plan = sum(s.plan for s in schedules)
    total_act  = sum(s.act  for s in schedules)

    return jsonify({
        'success': True,
        'line_id': line_id,
        'lineno': lineno,
        'date': str(today),
        'planned_qty': total_plan,
        'actual_qty': total_act,
        'variance': total_act - total_plan,
        'schedules': [{
            'seq': s.seq,
            'model': s.modelcode,
            'plan': s.plan,
            'act': s.act,
            'variance': s.act - s.plan,
        } for s in schedules],
    })


# ── Station submit ────────────────────────────────────────────────────────────
@api_bp.route('/station/<station_code>/submit', methods=['POST'])
@login_required
def submit_station(station_code):
    """Write station scan data to the appropriate DB table."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No JSON payload received.'}), 400

    now = datetime.now()
    station_lower = station_code.lower()

    # ── SFIS1 / CRS ────────────────────────────────────────────────────────
    if station_lower in ('sfis1', 'crs'):
        required = ['modelcode', 'serial', 'compmod', 'compserial']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing)}'}), 400

        record = CRS(
            modelcode   = data.get('modelcode', ''),
            serial      = data.get('serial', ''),
            compmod     = data.get('compmod', ''),
            compserial  = data.get('compserial', ''),
            fan1mod     = data.get('fan1mod') or None,
            fan1serial  = data.get('fan1serial') or None,
            fan2mod     = data.get('fan2mod') or None,
            fan2serial  = data.get('fan2serial') or None,
            part1mod    = data.get('part1mod') or None,
            part1desc   = data.get('part1desc') or None,
            part1serial = data.get('part1serial') or None,
            part2mod    = data.get('part2mod') or None,
            part2desc   = data.get('part2desc') or None,
            part2serial = data.get('part2serial') or None,
            part3mod    = data.get('part3mod') or None,
            part3desc   = data.get('part3desc') or None,
            part3serial = data.get('part3serial') or None,
            part4mod    = data.get('part4mod') or None,
            part4desc   = data.get('part4desc') or None,
            part4serial = data.get('part4serial') or None,
            time        = now,
            inspector   = getattr(current_user, 'username', 'system'),
            lineno      = data.get('lineno', 'L1')
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'success': True, 'scan_id': record.id, 'station': 'CRS'})

    # ── INSP1 / ATT ────────────────────────────────────────────────────────
    elif station_lower in ('insp1', 'att'):
        required = ['modelcode', 'serial', 'status1']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing)}'}), 400

        record = ATT(
            modelcode = data.get('modelcode', ''),
            serial    = data.get('serial', ''),
            status1   = (data.get('status1') or '').upper(),
            status2   = (data.get('status2') or '').upper(),
            status3   = (data.get('status3') or '').upper(),
            time      = now,
            inspector = getattr(current_user, 'username', 'system'),
            lineno    = data.get('lineno', 'L1'),
            brazzer1  = data.get('brazzer1'),
            brazzer2  = data.get('brazzer2'),
            brazzer3  = data.get('brazzer3'),
            brazzer4  = data.get('brazzer4'),
            brazzer5  = data.get('brazzer5'),
            brazzer6  = data.get('brazzer6'),
            brazzer7  = data.get('brazzer7'),
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'success': True, 'scan_id': record.id, 'station': 'ATT'})

    # ── SFIS2 / GMS ────────────────────────────────────────────────────────
    elif station_lower in ('sfis2', 'gms'):
        required = ['modelcode', 'serial', 'gascharge', 'status']
        missing = [f for f in required if f not in data or data[f] is None]
        if missing:
            return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing)}'}), 400

        try:
            gascharge = Decimal(str(data['gascharge']))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'gascharge must be a number.'}), 400

        status = data.get('status', '').upper()
        if status not in ('GOOD', 'NO GOOD'):
            return jsonify({'success': False, 'error': 'Status must be "GOOD" or "NO GOOD".'}), 400

        record = GMS(
            modelcode = data.get('modelcode', ''),
            serial    = data.get('serial', ''),
            gascharge = gascharge,
            status    = status,
            time      = now,
            inspector = getattr(current_user, 'username', 'system'),
            lineno    = data.get('lineno', 'L1')
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'success': True, 'scan_id': record.id, 'station': 'GMS'})

    # ── SPAMSI (Indoor Safety Parts) ────────────────────────────────────────
    elif station_lower in ('spamsi',):
        required = ['modelcode', 'serial']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing)}'}), 400
            
        record = SPAMSI(
            modelcode = data.get('modelcode', ''),
            serial    = data.get('serial', ''),
            inserial  = data.get('inserial', ''),
            part1mod  = data.get('part1mod'), part1desc = data.get('part1desc'), part1serial = data.get('part1serial'),
            part2mod  = data.get('part2mod'), part2desc = data.get('part2desc'), part2serial = data.get('part2serial'),
            part3mod  = data.get('part3mod'), part3desc = data.get('part3desc'), part3serial = data.get('part3serial'),
            part4mod  = data.get('part4mod'), part4desc = data.get('part4desc'), part4serial = data.get('part4serial'),
            part5mod  = data.get('part5mod'), part5desc = data.get('part5desc'), part5serial = data.get('part5serial'),
            part6mod  = data.get('part6mod'), part6desc = data.get('part6desc'), part6serial = data.get('part6serial'),
            time      = now,
            inspector = getattr(current_user, 'username', 'system'),
            lineno    = data.get('lineno', 'L1')
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'success': True, 'scan_id': record.id, 'station': 'SPAMSI'})

    # ── SPAMSO (Outdoor Safety Parts) ───────────────────────────────────────
    elif station_lower in ('spamso',):
        required = ['modelcode', 'serial']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'success': False, 'error': f'Missing fields: {", ".join(missing)}'}), 400
            
        record = SPAMSO(
            modelcode = data.get('modelcode', ''),
            serial    = data.get('serial', ''),
            outmodel  = data.get('outmodel', ''),
            outserial = data.get('outserial', ''),
            part1mod  = data.get('part1mod'), part1desc = data.get('part1desc'), part1serial = data.get('part1serial'),
            part2mod  = data.get('part2mod'), part2desc = data.get('part2desc'), part2serial = data.get('part2serial'),
            part3mod  = data.get('part3mod'), part3desc = data.get('part3desc'), part3serial = data.get('part3serial'),
            time      = now,
            inspector = getattr(current_user, 'username', 'system'),
            lineno    = data.get('lineno', 'L1')
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'success': True, 'scan_id': record.id, 'station': 'SPAMSO'})

    # ── SPAMS (Legacy / Safety Parts QR Parser) ─────────────────────────────
    elif station_lower in ('spams', 'safety'):
        raw_qr = data.get('raw_qr', '')
        if not raw_qr:
            return jsonify({'success': False, 'error': 'Missing raw_qr.'}), 400
            
        parsed_data = decode_safety_part_qr(raw_qr)
        if not parsed_data:
            return jsonify({'success': False, 'error': 'Failed to parse QR code.'}), 400
            
        return jsonify({
            'success': True,
            'station': 'SPAMS',
            'parsed_part_number': parsed_data.get('part_number'),
            'parsed_lot': parsed_data.get('lot_barcode'),
            'message': 'Parsed successfully. Database save logic not yet implemented.'
        })

    # ── Other stations — not yet implemented ───────────────────────────────
    else:
        return jsonify({
            'success': False,
            'error': f'Station "{station_code}" submission is not yet implemented.',
            'station': station_code,
        }), 501



# ── PIT record ────────────────────────────────────────────────────────────────
@api_bp.route('/pit/<int:unit_id>', methods=['GET'])
@login_required
def get_pit(unit_id):
    # Retrieve the unit (Requires the new schema to be fully implemented)
    try:
        from app.models.unit import Unit # type: ignore[import-untyped]
        unit = Unit.query.get(unit_id)
        if not unit:
            return jsonify({'success': False, 'error': 'Unit not found.'}), 404
            
        # Utilize the orphaned pit_generator
        pit = generate_and_save_pit(unit)
        if not pit:
            return jsonify({'success': False, 'error': 'Could not generate PIT. Unit may not be complete.'}), 400
            
        return jsonify({'success': True, 'pit_data': pit.pit_json})
    except ImportError:
        return jsonify({'error': 'PIT record system requires the new Unit model which is not yet implemented.'}), 501


# ── Weight reader ────────────────────────────────────────────────────────────────────
@api_bp.route('/weight/current', methods=['GET'])
@login_required
def get_current_weight():
    """Read current weight from Redis (singleton), then file fallback."""
    # Try Redis singleton
    try:
        r = _get_redis()
        val = r.get('current_weight_kg')
        if val is not None and val != 'error':
            return jsonify({'success': True, 'weight_kg': float(str(val)), 'source': 'redis'})
    except Exception:
        pass

    # Try file fallback with retry for Windows file locking
    import time
    for _ in range(3):
        try:
            fpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 '..', 'current_weight.txt')
            with open(fpath, 'r') as f:
                val = f.read().strip()
                return jsonify({'success': True, 'weight_kg': float(val), 'source': 'file'})
        except PermissionError:
            time.sleep(0.05) # Wait briefly if file is locked by the writer
        except Exception:
            break # Break on other errors (like FileNotFoundError)

    return jsonify({'success': False, 'error': 'Scale disconnected or weight reader not running.'})
