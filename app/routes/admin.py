"""Admin routes — Administrator module page and CRUD APIs."""
import logging
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from datetime import datetime
from functools import wraps
from flask_login import login_required, current_user, logout_user
from sqlalchemy import func
from app.models import db
from app.models.worksched import WorkSched
from app.models.modelref import ModelRef
from app.models.partref import PartRef
from app.models.crs import CRS
from app.models.gms import GMS
from app.models.att import ATT
from app.models.spams import SPAMS
from app.models.cb_pcb import CBPCB
from app.models.insp2 import INSP2
from app.models.insp3_run import INSP3Run
from app.models.insp3_vib import INSP3Vib
from app.models.insp4 import INSP4
from app.models.repair import Repair
from app.models.audit import AuditLog, log_audit
from app.models.line import Line
from app.models.module import Module
from app.models.tag import Tag
from app.models.user import User

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator: allow only admin and super_admin roles."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            logger.warning(
                'Unauthorized admin API access attempt by user "%s" (role: %s) on %s',
                getattr(current_user, 'username', 'anonymous'),
                getattr(current_user, 'role', 'none'),
                request.path,
            )
            return jsonify({'error': 'Forbidden — admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/admin')
@login_required
def admin_page():
    if current_user.role != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin.html')

@admin_bp.route('/admin/api/lines', methods=['GET'])
@login_required
def get_lines():
    lines = db.session.query(WorkSched.lineno).distinct().all()
    result = []
    for i, (lineno,) in enumerate(lines, start=1):
        result.append({'id': i, 'line_code': lineno, 'name': f'Line {lineno}'})
    return jsonify(result)

@admin_bp.route('/admin/api/schedules', methods=['GET'])
@login_required
def get_schedules():
    date_str = request.args.get('date')
    line_id = request.args.get('line_id', 'all')

    query = WorkSched.query
    if date_str:
        try:
            parsed_date = datetime.strptime(date_str, '%m/%d/%Y').date()
            query = query.filter_by(date=parsed_date)
        except ValueError:
            pass

    if line_id != 'all':
        lineno = line_id if line_id.startswith('L') else f"L{line_id}"
        query = query.filter_by(lineno=lineno)

    schedules = query.order_by(WorkSched.lineno, WorkSched.seq).all()

    # Build set of valid modelcodes for has_bom flag
    valid_models = set(
        mc for (mc,) in db.session.query(PartRef.modelcode).distinct().all()
    )

    schedules_data = []
    total_qty = 0
    for s in schedules:
        total_qty += s.plan
        schedules_data.append({
            'id': s.id,
            'line_code': s.lineno,
            'line_id': int(s.lineno.replace('L', '')) if 'L' in s.lineno else 1,
            'sort_order': s.seq,
            'model_number': s.modelcode,
            'model_id': s.id,
            'planned_qty': s.plan,
            'actual_qty': s.act,
            'takt_time': s.takttime,
            'shift': 'DAY',
            'status': 'ON_GOING' if s.act < s.plan else 'DONE',
            'variance': s.act - s.plan,
            'has_discrepancy': (s.act - s.plan > 0),
            'total_work_time_seconds': s.plan * s.takttime,
            'has_bom': s.modelcode in valid_models,
        })

    return jsonify({
        'date': date_str,
        'total_qty': total_qty,
        'schedules': schedules_data,
    })

@admin_bp.route('/admin/api/next-sequence', methods=['GET'])
@login_required
@admin_required
def get_next_sequence():
    line_id = request.args.get('line_id', '1')
    date_str = request.args.get('date')
    lineno = line_id if line_id.startswith('L') else f"L{line_id}"

    query = WorkSched.query.filter_by(lineno=lineno)
    if date_str:
        try:
            parsed_date = datetime.strptime(date_str, '%m/%d/%Y').date()
            query = query.filter_by(date=parsed_date)
        except ValueError:
            pass

    last_sched = query.order_by(WorkSched.seq.desc()).first()
    next_seq = 0 if not last_sched else last_sched.seq + 1
    return jsonify({'next_sequence': next_seq})

@admin_bp.route('/admin/api/schedule', methods=['POST'])
@login_required
@admin_required
def add_schedule():
    data = request.get_json()
    raw_line = data.get('line_id', 1)
    lineno = str(raw_line) if str(raw_line).startswith('L') else f"L{raw_line}"
    date_str = data.get('date')
    modelcode = data.get('model_number', '')

    parsed_date = datetime.now().date()
    if date_str:
        try:
            parsed_date = datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            pass

    # Guard: duplicate model on same line + date
    duplicate = WorkSched.query.filter_by(
        lineno=lineno,
        date=parsed_date,
        modelcode=modelcode
    ).first()
    if duplicate:
        return jsonify({
            'success': False,
            'error': 'duplicate',
            'message': f'Model "{modelcode}" already exists in this line/date schedule. Please select the existing entry and click Edit.'
        }), 409

    last_sched = WorkSched.query.filter_by(lineno=lineno, date=parsed_date).order_by(WorkSched.seq.desc()).first()
    next_seq = 0 if not last_sched else last_sched.seq + 1

    new_sched = WorkSched(
        lineno=lineno,
        seq=next_seq,
        modelcode=modelcode,
        plan=data.get('planned_qty', 0),
        act=0,
        takttime=data.get('takt_time', 0),
        date=parsed_date
    )
    db.session.add(new_sched)
    db.session.commit()
    log_audit(getattr(current_user, 'username', 'system'), 'CREATE', 'worksched', new_sched.id, {'modelcode': modelcode, 'plan': new_sched.plan})
    return jsonify({'success': True, 'id': new_sched.id})

@admin_bp.route('/admin/api/schedule/<int:sid>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_schedule(sid):
    sched = db.get_or_404(WorkSched, sid)
    if request.method == 'DELETE':
        lineno = sched.lineno
        date_val = sched.date
        db.session.delete(sched)
        db.session.commit()

        # Re-sequence remaining entries for this line+date, 0-based
        remaining = WorkSched.query.filter_by(lineno=lineno, date=date_val).order_by(WorkSched.seq).all()
        for idx, s in enumerate(remaining):
            s.seq = idx
        db.session.commit()
        log_audit(getattr(current_user, 'username', 'system'), 'DELETE', 'worksched', sid)
        return jsonify({'success': True})

    data = request.get_json()
    if 'model_number' in data:
        sched.modelcode = data['model_number']
    if 'planned_qty' in data:
        sched.plan = data['planned_qty']
    if 'takt_time' in data:
        sched.takttime = data['takt_time']
    db.session.commit()
    log_audit(getattr(current_user, 'username', 'system'), 'UPDATE', 'worksched', sid, data)
    return jsonify({'success': True})

@admin_bp.route('/admin/api/module-schedules', methods=['GET', 'PUT', 'DELETE'])
@login_required
@admin_required
def module_schedules():
    if request.method == 'GET':
        return jsonify({'module_schedules': []})
    return jsonify({'success': True})

@admin_bp.route('/admin/api/models', methods=['GET'])
@login_required
def get_models():
    models = db.session.query(ModelRef.modelcode).order_by(ModelRef.modelcode).all()
    return jsonify([{
        'id': mcode,
        'model_number': mcode,
    } for (mcode,) in models])

@admin_bp.route('/admin/api/model', methods=['POST'])
@login_required
@admin_required
def add_model():
    return jsonify({
        'success': False,
        'error': 'Manual model creation is not supported. Import models via the BOM Excel import feature.'
    }), 501

@admin_bp.route('/admin/api/model/<modelcode>', methods=['DELETE'])
@login_required
@admin_required
def delete_model(modelcode):
    """Delete all BOM rows for the given model code."""
    deleted = PartRef.query.filter_by(modelcode=modelcode).delete()
    db.session.commit()
    if deleted == 0:
        return jsonify({'success': False, 'error': 'Model not found.'}), 404
    log_audit(getattr(current_user, 'username', 'system'), 'DELETE', 'partref', modelcode, {'deleted_parts': deleted})
    return jsonify({'success': True, 'deleted_parts': deleted})

@admin_bp.route('/admin/api/bom', methods=['GET'])
@login_required
def get_bom():
    modelcode = request.args.get('modelcode')
    if not modelcode:
        return jsonify({'parts': []})

    # Order by ID ascending first to ensure new entries go to the bottom of their group
    entries = PartRef.query.filter_by(modelcode=modelcode).order_by(PartRef.id).all()
    
    # Sort modules in the order: CRS, GMS, SPAMS, CB
    module_order = {'crs': 1, 'gms': 2, 'spams': 3, 'cb': 4}
    entries.sort(key=lambda e: module_order.get((e.module or '').lower(), 99))

    return jsonify({
        'parts': [{
            'id': e.id,
            'module_code': e.module,
            'part_number': e.partno,
            'description': e.partdesc,
            'usage_qty': float(e.usage),
            'tag': e.tag,
        } for e in entries],
    })

@admin_bp.route('/admin/api/is-production-running', methods=['GET'])
@login_required
def is_production_running():
    return jsonify({'is_running': False})

@admin_bp.route('/admin/api/bom', methods=['POST'])
@login_required
@admin_required
def add_bom():
    data = request.get_json()
    modelcode = data.get('modelcode', '')
    
    current_count = PartRef.query.filter_by(modelcode=modelcode).count()
    if current_count >= 20:
        return jsonify({'success': False, 'message': 'Maximum limit of 20 parts per model reached.'})
        
    new_part = PartRef(
        modelcode=modelcode,
        module=data.get('module', ''),
        partno=data.get('partno', ''),
        partdesc=data.get('partdesc', ''),
        usage=float(data.get('usage', 0)),
        tag=data.get('tag', '')
    )
    db.session.add(new_part)
    db.session.commit()
    log_audit(getattr(current_user, 'username', 'system'), 'CREATE', 'partref', new_part.id, {'modelcode': modelcode, 'partno': new_part.partno})
    return jsonify({'success': True, 'id': new_part.id})

@admin_bp.route('/admin/api/bom/<int:bid>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_bom(bid):
    part = db.get_or_404(PartRef, bid)
    if request.method == 'DELETE':
        db.session.delete(part)
        db.session.commit()
        log_audit(getattr(current_user, 'username', 'system'), 'DELETE', 'partref', bid)
        return jsonify({'success': True})

    data = request.get_json()
    if 'modelcode' in data:
        part.modelcode = data['modelcode']
    if 'module' in data:
        part.module = data['module']
    if 'partno' in data:
        part.partno = data['partno']
    if 'partdesc' in data:
        part.partdesc = data['partdesc']
    if 'usage' in data:
        part.usage = float(data['usage'])
    if 'tag' in data:
        part.tag = data['tag']

    db.session.commit()
    log_audit(getattr(current_user, 'username', 'system'), 'UPDATE', 'partref', bid, data)
    return jsonify({'success': True})

# ── Model Reference (Serial Start) CRUD ─────────────────────────────────────

VALID_AREAS = ('Domestic', 'HongKong', 'Export', 'Taiwan')

@admin_bp.route('/admin/api/modelref', methods=['GET'])
@login_required
def get_modelref():
    """List all serial-start reference entries, optionally filtered by area."""
    area = request.args.get('area')
    query = ModelRef.query
    if area:
        query = query.filter_by(area=area)
    entries = query.order_by(ModelRef.modelcode, ModelRef.area).all()
    return jsonify({
        'entries': [{
            'id':          e.id,
            'modelcode':   e.modelcode,
            'area':        e.area,
            'serialstart': e.serialstart,
        } for e in entries]
    })

@admin_bp.route('/admin/api/modelref', methods=['POST'])
@login_required
@admin_required
def add_modelref():
    """Add a new serial-start reference entry."""
    data = request.get_json()
    modelcode   = (data.get('modelcode') or '').strip()
    area        = (data.get('area') or '').strip()
    serialstart = (data.get('serialstart') or '').strip()

    if not modelcode or not area or not serialstart:
        return jsonify({'success': False, 'error': 'modelcode, area, and serialstart are required.'}), 400
    if area not in VALID_AREAS:
        return jsonify({'success': False, 'error': f'area must be one of: {", ".join(VALID_AREAS)}'}), 400

    entry = ModelRef(modelcode=modelcode, area=area, serialstart=serialstart)
    db.session.add(entry)
    db.session.commit()
    log_audit(getattr(current_user, 'username', 'system'), 'CREATE', 'modelref', entry.id,
              {'modelcode': modelcode, 'area': area, 'serialstart': serialstart})
    return jsonify({'success': True, 'id': entry.id})

@admin_bp.route('/admin/api/modelref/<int:rid>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_modelref(rid):
    """Edit or delete a serial-start reference entry."""
    entry = db.get_or_404(ModelRef, rid)
    if request.method == 'DELETE':
        db.session.delete(entry)
        db.session.commit()
        log_audit(getattr(current_user, 'username', 'system'), 'DELETE', 'modelref', rid)
        return jsonify({'success': True})

    data = request.get_json()
    if 'modelcode' in data:
        entry.modelcode = (data['modelcode'] or '').strip()
    if 'area' in data:
        area = (data['area'] or '').strip()
        if area not in VALID_AREAS:
            return jsonify({'success': False, 'error': f'area must be one of: {", ".join(VALID_AREAS)}'}), 400
        entry.area = area
    if 'serialstart' in data:
        entry.serialstart = (data['serialstart'] or '').strip()
    db.session.commit()
    log_audit(getattr(current_user, 'username', 'system'), 'UPDATE', 'modelref', rid, data)
    return jsonify({'success': True})

@admin_bp.route('/admin/api/settings', methods=['GET'])
@login_required
def get_settings():
    return jsonify({
        'crs_active': True,
        'gms_active': True,
        'spams_active': False,
        'fpcp_active': False,
        'cb_active': False,
        'carry_over_unfinished': False,
        'validate_serial': False,
        'allow_all_chars_serial': True,
        'no_item_qty_deduction': False,
        'validate_domestic_serial_date': False,
    })

@admin_bp.route('/admin/api/settings', methods=['PUT'])
@login_required
@admin_required
def save_settings():
    return jsonify({
        'success': False,
        'error': 'Settings are managed via the server .env file and cannot be changed from the UI.'
    }), 501

@admin_bp.route('/admin/api/scoreboard-data', methods=['GET'])
@login_required
def get_scoreboard_data():
    date_str = request.args.get('date')
    line_id = request.args.get('line_id', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)

    query = WorkSched.query

    if date_str:
        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter_by(date=parsed_date)
        except ValueError:
            pass

    if line_id and line_id != 'all':
        lineno = line_id if line_id.startswith('L') else f"L{line_id}"
        query = query.filter_by(lineno=lineno)

    pagination = query.order_by(WorkSched.date.desc(), WorkSched.lineno, WorkSched.seq).paginate(page=page, per_page=per_page, error_out=False)
    schedules = pagination.items

    result = []
    for s in schedules:
        result.append({
            'id': s.id,
            'date': s.date.strftime('%Y-%m-%d'),
            'line_code': s.lineno,
            'seq': s.seq,
            'model_number': s.modelcode,
            'takt_time': s.takttime,
            'total_sec': s.plan * s.takttime,
            'plan': s.plan,
            'act': s.act,
        })

    return jsonify({
        'scoreboards': result,
        'total_pages': pagination.pages,
        'current_page': pagination.page,
        'total_items': pagination.total
    })


# ── Reopen Day ────────────────────────────────────────────────────────────────

@admin_bp.route('/admin/api/reopen-day', methods=['POST'])
@login_required
@admin_required
def reopen_day():
    """Reset finalized=0 for all worksched rows on a given date/line."""
    data = request.get_json() or {}
    line_id  = data.get('line_id')
    date_str = data.get('date')

    if not line_id or not date_str:
        return jsonify({'success': False, 'error': 'line_id and date are required.'}), 400

    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    lineno = f"L{line_id}"
    rows = WorkSched.query.filter_by(lineno=lineno, date=parsed_date).all()

    if not rows:
        return jsonify({'success': False, 'error': 'No records found for that date/line.'}), 404

    for row in rows:
        row.finalized    = False
        row.finalized_at = None
        row.finalized_by = None

    db.session.commit()
    return jsonify({'success': True, 'reopened': len(rows)})


# ── CRS Data Viewer ───────────────────────────────────────────────────────────

@admin_bp.route('/admin/api/crs-data', methods=['GET'])
@login_required
def get_crs_data():
    page     = max(1, int(request.args.get('page', 1)))
    per_page = 50
    date_str = request.args.get('date', '').strip()
    serial   = request.args.get('serial', '').strip()
    sort_by  = request.args.get('sort_by', 'time').strip()
    sort_dir = request.args.get('sort_dir', 'desc').strip()

    query = CRS.query
    if date_str:
        try:
            parsed = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(func.date(CRS.time) == parsed)
        except ValueError:
            pass
    if serial:
        query = query.filter(CRS.serial.ilike(f'%{serial}%'))

    total   = query.count()
    
    # Apply dynamic sorting
    if hasattr(CRS, sort_by):
        column = getattr(CRS, sort_by)
        if sort_dir == 'asc':
            query = query.order_by(column.asc())
        else:
            query = query.order_by(column.desc())
    else:
        query = query.order_by(CRS.time.desc())
        
    records = query.offset((page - 1) * per_page).limit(per_page).all()
    ng = _check_ng_history(records)

    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'records': [{
            'id':         r.id,
            'time':       r.time.strftime('%Y-%m-%d %H:%M:%S'),
            'modelcode':  r.modelcode,
            'serial':     r.serial,
            'compmod':    r.compmod,
            'compserial': r.compserial,
            'fan1mod':    r.fan1mod,
            'fan1serial': r.fan1serial,
            'fan2mod':    r.fan2mod or '—',
            'fan2serial': r.fan2serial or '—',
            'part1mod':   r.part1mod or '—',
            'part1desc':  r.part1desc or '—',
            'part1serial': r.part1serial or '—',
            'part2mod':   r.part2mod or '—',
            'part2desc':  r.part2desc or '—',
            'part2serial': r.part2serial or '—',
            'part3mod':   r.part3mod or '—',
            'part3desc':  r.part3desc or '—',
            'part3serial': r.part3serial or '—',
            'inspector':  r.inspector or '—',
        } for r in records],
    })

@admin_bp.route('/admin/api/crs-data/<int:id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def update_crs_data(id):
    record = db.get_or_404(CRS, id)
    if request.method == 'DELETE':
        db.session.delete(record)
        db.session.commit()
        log_audit(getattr(current_user, 'username', 'system'), 'DELETE', 'crs', id)
        return jsonify({'success': True})
    
    data = request.get_json()
    fields = ['modelcode', 'serial', 'compmod', 'compserial', 'fan1mod', 'fan1serial', 'fan2mod', 'fan2serial']
    for f in fields:
        if f in data:
            setattr(record, f, data[f])
    db.session.commit()
    log_audit(getattr(current_user, 'username', 'system'), 'UPDATE', 'crs', id, data)
    return jsonify({'success': True})


# ── GMS Data Viewer ───────────────────────────────────────────────────────────

@admin_bp.route('/admin/api/gms-data', methods=['GET'])
@login_required
def get_gms_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total, records = _get_paginated_data(
        GMS, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)

    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'records': [{
            'id':        r.id,
            'time':      r.time.strftime('%Y-%m-%d %H:%M:%S'),
            'modelcode': r.modelcode,
            'serial':    r.serial,
            'gascharge': float(r.gascharge),
            'status':    r.status,
            'inspector': r.inspector or '—',
            'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')
        } for r in records],
    })

@admin_bp.route('/admin/api/gms-data/<int:id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def update_gms_data(id):
    record = db.get_or_404(GMS, id)
    if request.method == 'DELETE':
        db.session.delete(record)
        db.session.commit()
        log_audit(getattr(current_user, 'username', 'system'), 'DELETE', 'gms', id)
        return jsonify({'success': True})
    
    data = request.get_json()
    if 'modelcode' in data: record.modelcode = data['modelcode']
    if 'serial' in data: record.serial = data['serial']
    if 'gascharge' in data: record.gascharge = data['gascharge']
    if 'status' in data: record.status = data['status']
    db.session.commit()
    log_audit(getattr(current_user, 'username', 'system'), 'UPDATE', 'gms', id, data)
    return jsonify({'success': True})


# ── ATT / Safety Parts Data Viewer ───────────────────────────────────────────

@admin_bp.route('/admin/api/att-data', methods=['GET'])
@login_required
def get_att_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total, records = _get_paginated_data(
        ATT, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)

    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'records': [{
            'id':        r.id,
            'time':      r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '',
            'modelcode': r.modelcode or '',
            'serial':    r.serial or '',
            'status':    r.status,
            'status1':   r.status1 or '',
            'status2':   r.status2 or '',
            'status3':   r.status3 or '',
            'inspector': r.inspector or '—',
            'brazzer1':  r.brazzer1 or '',
            'brazzer2':  r.brazzer2 or '',
            'brazzer3':  r.brazzer3 or '',
            'brazzer4':  r.brazzer4 or '',
            'brazzer5':  r.brazzer5 or '',
            'brazzer6':  r.brazzer6 or '',
            'brazzer7':  r.brazzer7 or '',
            'ng_history': True if ng.get(r.serial) else False,
        } for r in records],
    })

@admin_bp.route('/admin/api/att-data/<int:id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def update_att_data(id):
    record = db.get_or_404(ATT, id)
    if request.method == 'DELETE':
        db.session.delete(record)
        db.session.commit()
        log_audit(getattr(current_user, 'username', 'system'), 'DELETE', 'att', id)
        return jsonify({'success': True})
    
    data = request.get_json()
    if 'modelcode' in data: record.modelcode = data['modelcode']
    if 'serial' in data: record.serial = data['serial']
    if 'status1' in data: record.status1 = data['status1']
    if 'status2' in data: record.status2 = data['status2']
    if 'status3' in data: record.status3 = data['status3']
    if 'brazzer1' in data: record.brazzer1 = data['brazzer1']
    if 'brazzer2' in data: record.brazzer2 = data['brazzer2']
    if 'brazzer3' in data: record.brazzer3 = data['brazzer3']
    if 'brazzer4' in data: record.brazzer4 = data['brazzer4']
    if 'brazzer5' in data: record.brazzer5 = data['brazzer5']
    if 'brazzer6' in data: record.brazzer6 = data['brazzer6']
    if 'brazzer7' in data: record.brazzer7 = data['brazzer7']
    db.session.commit()
    log_audit(getattr(current_user, 'username', 'system'), 'UPDATE', 'att', id, data)
    return jsonify({'success': True})

# ── Audit Log Viewer ──────────────────────────────────────────────────────────

@admin_bp.route('/admin/api/audit-logs', methods=['GET'])
@login_required
@admin_required
def get_audit_logs():
    page     = max(1, int(request.args.get('page', 1)))
    per_page = 50
    query = AuditLog.query.order_by(AuditLog.timestamp.desc())
    total = query.count()
    records = query.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'records': [{
            'id': r.id,
            'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'username': r.username,
            'action': r.action,
            'table_name': r.table_name,
            'record_id': r.record_id,
            'details': r.details
        } for r in records]
    })

# ── Print Production Tag ──────────────────────────────────────────────────────

@admin_bp.route('/admin/print-tag/<serial>', methods=['GET'])
@login_required
def print_tag(serial):
    """Render the Production Information Tag for a specific serial number."""
    # Gather data from CRS, GMS, ATT, INSP2
    crs_record = CRS.query.filter_by(serial=serial).order_by(CRS.id.desc()).first()
    gms_record = GMS.query.filter_by(serial=serial).order_by(GMS.id.desc()).first()
    att_record = ATT.query.filter_by(serial=serial).order_by(ATT.id.desc()).first()
    
    from app.models.insp2 import INSP2
    from app.models.insp3_run import INSP3Run
    from app.models.insp3_vib import INSP3Vib
    from app.models.insp4 import INSP4
    
    insp2_record = INSP2.query.filter_by(serial=serial).order_by(INSP2.id.desc()).first()
    insp3_run_record = INSP3Run.query.filter_by(serial=serial).order_by(INSP3Run.id.desc()).first()
    insp3_vib_record = INSP3Vib.query.filter_by(serial=serial).order_by(INSP3Vib.id.desc()).first()
    insp4_record = INSP4.query.filter_by(serial=serial).order_by(INSP4.id.desc()).first()
    
    # Determine the time to calculate shift (Day/Night) and Date
    production_time = crs_record.time if crs_record else datetime.now()
    
    shift = 'DAY'
    if production_time.hour >= 18 or production_time.hour < 6:
        shift = 'NIGHT'
        
    lineno = crs_record.lineno if crs_record and crs_record.lineno else (
        gms_record.lineno if gms_record and gms_record.lineno else (
            att_record.lineno if att_record and att_record.lineno else ''
        )
    )
    
    unit_data = {
        'serial': serial,
        'modelcode': crs_record.modelcode if crs_record else (gms_record.modelcode if gms_record else (att_record.modelcode if att_record else '')),
        'production_date': production_time.strftime('%Y-%m-%d'),
        'shift': shift,
        'lineno': lineno,
        
        'crs_inspector': crs_record.inspector if crs_record else '',
        
        'att_status': att_record.status if att_record else '',
        'att_inspector': att_record.inspector if att_record else '',
        'att_status1': att_record.status1 if att_record else '',
        'att_status2': att_record.status2 if att_record else '',
        'att_status3': att_record.status3 if att_record else '',
        'att_brazzer1': att_record.brazzer1 if att_record else '',
        'att_brazzer2': att_record.brazzer2 if att_record else '',
        'att_brazzer3': att_record.brazzer3 if att_record else '',
        'att_brazzer4': att_record.brazzer4 if att_record else '',
        'att_brazzer5': att_record.brazzer5 if att_record else '',
        'att_brazzer6': att_record.brazzer6 if att_record else '',
        'att_brazzer7': att_record.brazzer7 if att_record else '',
        
        'gms_gascharge': float(gms_record.gascharge) if gms_record else '',
        'gms_status': gms_record.status if gms_record else '',
        'gms_inspector': gms_record.inspector if gms_record else '',
        
        'insp2_status': insp2_record.status if insp2_record else '',
        'insp2_inspector': insp2_record.inspector if insp2_record else '',
        'insp2_wiring_seq': insp2_record.test_wiring_seq if insp2_record else '',
        'insp2_no_touching': insp2_record.test_no_touching if insp2_record else '',
        'insp2_no_misaligned': insp2_record.test_no_misaligned if insp2_record else '',
        'insp2_no_lacking': insp2_record.test_no_lacking if insp2_record else '',
        
        'insp3_run_status': insp3_run_record.status if insp3_run_record else '',
        'insp3_run_inspector': insp3_run_record.inspector if insp3_run_record else '',
        'insp3_run_leak_status': insp3_run_record.leak_status if insp3_run_record else '',
        'insp3_run_insulation': insp3_run_record.insulation_resistance if insp3_run_record else '',
        'insp3_run_withstand': insp3_run_record.withstand_voltage if insp3_run_record else '',
        'insp3_run_airswing': insp3_run_record.airswing if insp3_run_record else '',
        'insp3_run_comp_operation': insp3_run_record.comp_operation if insp3_run_record else '',
        'insp3_run_fan_operation': insp3_run_record.fan_operation if insp3_run_record else '',
        'insp3_run_temp_diff': insp3_run_record.temp_diff if insp3_run_record else '',
        'insp3_run_leak_location': insp3_run_record.leak_location if insp3_run_record else '',
        'insp3_run_prog_check_h': insp3_run_record.prog_check_h if insp3_run_record else '',
        'insp3_run_prog_check_f': insp3_run_record.prog_check_f if insp3_run_record else '',
        'insp3_run_operating_current': insp3_run_record.operating_current if insp3_run_record else '',
        'insp3_run_input_power': insp3_run_record.input_power if insp3_run_record else '',
        'insp3_run_evap_cool': insp3_run_record.evap_tubes_cool if insp3_run_record else '',
        'insp3_run_evap_heat': insp3_run_record.evap_tubes_heat if insp3_run_record else '',
        'insp3_run_cond_cool': insp3_run_record.cond_tubes_cool if insp3_run_record else '',
        'insp3_run_cond_heat': insp3_run_record.cond_tubes_heat if insp3_run_record else '',
        'insp3_run_op_cool': insp3_run_record.op_current_cool if insp3_run_record else '',
        'insp3_run_op_heat': insp3_run_record.op_current_heat if insp3_run_record else '',
        'insp3_run_in_cool': insp3_run_record.in_power_cool if insp3_run_record else '',
        'insp3_run_in_heat': insp3_run_record.in_power_heat if insp3_run_record else '',
        
        'insp3_vib_status': insp3_vib_record.status if insp3_vib_record else '',
        'insp3_vib_inspector': insp3_vib_record.inspector if insp3_vib_record else '',
        
        'insp4_status': insp4_record.status if insp4_record else '',
        'insp4_inspector': insp4_record.inspector if insp4_record else '',
        'insp4_insulation': insp4_record.insulation_resistance if insp4_record else '',
        'insp4_operating_current': insp4_record.operating_current if insp4_record else '',
        'insp4_nameplate': insp4_record.nameplate_match if insp4_record else '',
        'insp4_label': insp4_record.model_label if insp4_record else '',
        'insp4_manual_remote': insp4_record.manual_remote if insp4_record else '',
        'insp4_manual_warranty': insp4_record.manual_warranty if insp4_record else '',
        'insp4_manual_screws': insp4_record.manual_screws if insp4_record else '',
        'insp4_grille_eel': insp4_record.grille_eel if insp4_record else '',
        'insp4_grille_model': insp4_record.grille_model if insp4_record else '',
        'insp4_grille_logo': insp4_record.grille_logo if insp4_record else '',
    }
    return render_template('admin/print_tag.html', unit=unit_data)

# ── New Quality Inspection Station APIs ───────────────────────────────────────


def _check_ng_history(records):
    if not records:
        return {}
    serials = list(set([r.serial for r in records if getattr(r, 'serial', None)]))
    if not serials:
        return {}
    repaired = db.session.query(Repair.serial).filter(Repair.serial.in_(serials)).all()
    ng_serials = {r[0] for r in repaired}
    return {s: (s in ng_serials) for s in serials}

def _get_paginated_data(model_class, page, per_page, date_str, serial, sort_by='time', sort_dir='desc'):
    query = model_class.query
    if date_str:
        try:
            parsed = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(func.date(model_class.time) == parsed)
        except ValueError:
            pass
    if serial:
        query = query.filter(model_class.serial.ilike(f'%{serial}%'))

    total = query.count()
    
    if hasattr(model_class, sort_by):
        column = getattr(model_class, sort_by)
        if sort_dir == 'asc':
            query = query.order_by(column.asc())
        else:
            query = query.order_by(column.desc())
    else:
        query = query.order_by(model_class.time.desc())
        
    records = query.offset((page - 1) * per_page).limit(per_page).all()
    return total, records

@admin_bp.route('/admin/api/spams-data', methods=['GET'])
@login_required
def get_spams_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total, records = _get_paginated_data(
        SPAMS, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S'), 'modelcode': r.modelcode, 'serial': r.serial, 'status': r.status, 'inspector': r.inspector or '—', 'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')} for r in records]
    })

@admin_bp.route('/admin/api/cbpcb-data', methods=['GET'])
@login_required
def get_cbpcb_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total, records = _get_paginated_data(
        CBPCB, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S'), 'modelcode': r.modelcode, 'serial': r.serial, 'status': r.status, 'inspector': r.inspector or '—', 'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')} for r in records]
    })

@admin_bp.route('/admin/api/insp2-data', methods=['GET'])
@login_required
def get_insp2_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total, records = _get_paginated_data(
        INSP2, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S'), 'modelcode': r.modelcode, 'serial': r.serial, 'status': r.status, 'inspector': r.inspector or '—', 'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else ''), 'test_wiring_seq': r.test_wiring_seq or '', 'test_no_touching': r.test_no_touching or '', 'test_no_misaligned': r.test_no_misaligned or '', 'test_no_lacking': r.test_no_lacking or ''} for r in records]
    })

@admin_bp.route('/admin/api/insp3run-data', methods=['GET'])
@login_required
def get_insp3run_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total, records = _get_paginated_data(
        INSP3Run, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S'), 'modelcode': r.modelcode, 'serial': r.serial, 'status': r.status, 'inspector': r.inspector or '—', 'insulation_resistance': r.insulation_resistance or '', 'withstand_voltage': r.withstand_voltage or '', 'leak_status': r.leak_status or '', 'leak_location': r.leak_location or '', 'prog_check_h': r.prog_check_h or '', 'prog_check_f': r.prog_check_f or '', 'airswing': r.airswing or '', 'comp_operation': r.comp_operation or '', 'fan_operation': r.fan_operation or '', 'evap_tubes': r.evap_tubes or '', 'cond_tubes': r.cond_tubes or '', 'operating_current': r.operating_current or '', 'input_power': r.input_power or '', 'temp_diff': r.temp_diff or '', 'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')} for r in records]
    })

@admin_bp.route('/admin/api/insp3vib-data', methods=['GET'])
@login_required
def get_insp3vib_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total, records = _get_paginated_data(
        INSP3Vib, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S'), 'modelcode': r.modelcode, 'serial': r.serial, 'status': r.status, 'inspector': r.inspector or '—', 'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')} for r in records]
    })

@admin_bp.route('/admin/api/insp4-data', methods=['GET'])
@login_required
def get_insp4_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total, records = _get_paginated_data(
        INSP4, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S'), 'modelcode': r.modelcode, 'serial': r.serial, 'status': r.status, 'inspector': r.inspector or '—', 'insulation_resistance': r.insulation_resistance or '', 'operating_current': r.operating_current or '', 'nameplate_match': r.nameplate_match or '', 'model_label': r.model_label or '', 'manual_remote': r.manual_remote or '', 'manual_warranty': r.manual_warranty or '', 'manual_screws': r.manual_screws or '', 'grille_eel': r.grille_eel or '', 'grille_model': r.grille_model or '', 'grille_logo': r.grille_logo or '', 'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')} for r in records]
    })

@admin_bp.route('/admin/api/repair-data', methods=['GET'])
@login_required
def get_repair_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    total, records = _get_paginated_data(
        Repair, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S'), 'modelcode': r.modelcode, 'serial': r.serial, 'status': r.status, 'inspector': r.inspector or '—', 'station_origin': r.station_origin or '', 'defect_type': r.defect_type or '', 'action_taken': r.action_taken or '', 'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')} for r in records]
    })

@admin_bp.route('/admin/api/prod-tag-tracker', methods=['GET'])
@login_required
def get_prod_tag_tracker():
    page = max(1, int(request.args.get('page', 1)))
    per_page = 50
    date_str = request.args.get('date', '').strip()
    serial = request.args.get('serial', '').strip()

    # The tracker aggregates data based on serials present in CRS.
    query = CRS.query
    if date_str:
        try:
            parsed = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(func.date(CRS.time) == parsed)
        except ValueError:
            pass
    if serial:
        query = query.filter(CRS.serial.ilike(f'%{serial}%'))

    total = query.count()
    crs_records = query.order_by(CRS.time.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # Pre-fetch statuses for these serials from all stations
    serials = [r.serial for r in crs_records]
    if not serials:
        return jsonify({'total': 0, 'page': page, 'per_page': per_page, 'records': []})

    def get_latest_statuses(model):
        subquery = db.session.query(model.serial, func.max(model.time).label('maxtime')).filter(model.serial.in_(serials)).group_by(model.serial).subquery()
        records = db.session.query(model).join(subquery, db.and_(model.serial == subquery.c.serial, model.time == subquery.c.maxtime)).all()
        return {r.serial: r.status for r in records}

    att_status = get_latest_statuses(ATT)
    gms_status = get_latest_statuses(GMS)
    spams_status = get_latest_statuses(SPAMS)
    cb_status = get_latest_statuses(CBPCB)
    insp2_status = get_latest_statuses(INSP2)
    insp3run_status = get_latest_statuses(INSP3Run)
    insp3vib_status = get_latest_statuses(INSP3Vib)
    insp4_status = get_latest_statuses(INSP4)
    repair_status = get_latest_statuses(Repair)

    results = []
    for r in crs_records:
        s = r.serial
        # A serial is considered Ready to Print if ALL inspection stations are OK.
        stations = {
            'CRS': 'GOOD',
            'ATT': att_status.get(s, 'PENDING'),
            'GMS': gms_status.get(s, 'PENDING'),
            'SPAMS': spams_status.get(s, 'PENDING'),
            'CB': cb_status.get(s, 'PENDING'),
            'INSP2': insp2_status.get(s, 'PENDING'),
            'INSP3Run': insp3run_status.get(s, 'PENDING'),
            'INSP3Vib': insp3vib_status.get(s, 'PENDING'),
            'INSP4': insp4_status.get(s, 'PENDING'),
            'Repair': repair_status.get(s, 'N/A')
        }
        
        # Check if all required stations are GOOD
        required_stations = ['CRS', 'ATT', 'GMS', 'SPAMS', 'CB', 'INSP2', 'INSP3Run', 'INSP3Vib', 'INSP4']
        all_good = True
        for st in required_stations:
            if stations[st].upper() not in ('OK', 'GOOD', 'PASS'):
                all_good = False
                break
                
        tag_status = 'READY' if all_good else 'NOT READY'
        
        results.append({
            'modelcode': r.modelcode,
            'serial': s,
            'crs': stations['CRS'],
            'att': stations['ATT'],
            'gms': stations['GMS'],
            'spams': stations['SPAMS'],
            'cb': stations['CB'],
            'insp2': stations['INSP2'],
            'insp3': stations['INSP3Run'],
            'vib': stations['INSP3Vib'],
            'insp4': stations['INSP4'],
            'repair': stations['Repair'],
            'tag_status': tag_status
        })

    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'records': results
    })

# ==========================================
# SYSTEM CONTROL APIs (Migrated from Superadmin)
# ==========================================

# ── Lines API ──────────────────────────────────────────────────────────────────

@admin_bp.route('/sys/api/lines', methods=['GET'])
@login_required
@admin_required
def sys_get_lines():
    lines = Line.query.order_by(Line.lineno).all()
    return jsonify([{
        'id': l.id,
        'lineno': l.lineno,
        'name': l.name,
        'is_active': l.is_active,
        'created_at': str(l.created_at)
    } for l in lines])


@admin_bp.route('/sys/api/line', methods=['POST'])
@login_required
@admin_required
def create_line():
    data = request.get_json()
    lineno = data.get('lineno', '').strip().upper()
    name = data.get('name', '').strip()

    if not lineno or not name:
        return jsonify({'success': False, 'error': 'Line number and name are required.'}), 400

    if Line.query.filter_by(lineno=lineno).first():
        return jsonify({'success': False, 'error': f'Line "{lineno}" already exists.'}), 409

    new_line = Line(lineno=lineno, name=name, is_active=True)
    db.session.add(new_line)
    db.session.commit()
    return jsonify({'success': True, 'id': new_line.id})


@admin_bp.route('/sys/api/line/<int:lid>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_line(lid):
    line = db.get_or_404(Line, lid)

    if request.method == 'DELETE':
        db.session.delete(line)
        db.session.commit()
        return jsonify({'success': True})

    data = request.get_json()
    if 'name' in data:
        line.name = data['name'].strip()
    if 'is_active' in data:
        line.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({'success': True})


# ── Public line list (used by scoreboard and admin dropdowns) ──────────────────
@admin_bp.route('/api/lines/active', methods=['GET'])
@login_required
def get_active_lines():
    """Public endpoint — returns active lines for scoreboard and admin dropdowns."""
    lines = Line.query.filter_by(is_active=True).order_by(Line.lineno).all()
    return jsonify([{
        'id': l.id,
        'lineno': l.lineno,
        'name': l.name,
    } for l in lines])


# ── Modules API ────────────────────────────────────────────────────────────────

@admin_bp.route('/sys/api/modules', methods=['GET'])
@login_required
@admin_required
def get_modules():
    modules = Module.query.order_by(Module.id).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'description': m.description,
        'is_active': m.is_active,
        'created_at': str(m.created_at)
    } for m in modules])

@admin_bp.route('/sys/api/module', methods=['POST'])
@login_required
@admin_required
def create_module():
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not name:
        return jsonify({'success': False, 'error': 'Module name is required.'}), 400

    if Module.query.filter_by(name=name).first():
        return jsonify({'success': False, 'error': f'Module "{name}" already exists.'}), 409

    new_module = Module(name=name, description=description, is_active=True)
    db.session.add(new_module)
    db.session.commit()
    return jsonify({'success': True, 'id': new_module.id})

@admin_bp.route('/sys/api/module/<int:mid>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_module(mid):
    module = db.get_or_404(Module, mid)

    if request.method == 'DELETE':
        db.session.delete(module)
        db.session.commit()
        return jsonify({'success': True})

    data = request.get_json()
    if 'name' in data:
        module.name = data['name'].strip()
    if 'description' in data:
        module.description = data['description'].strip()
    if 'is_active' in data:
        module.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/api/modules/active', methods=['GET'])
@login_required
def get_active_modules():
    modules = Module.query.filter_by(is_active=True).order_by(Module.id).all()
    return jsonify([{'id': m.id, 'name': m.name} for m in modules])


# ── Tags API ───────────────────────────────────────────────────────────────────

@admin_bp.route('/sys/api/tags', methods=['GET'])
@login_required
@admin_required
def get_tags():
    tags = Tag.query.order_by(Tag.id).all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'description': t.description,
        'is_active': t.is_active,
        'created_at': str(t.created_at)
    } for t in tags])

@admin_bp.route('/sys/api/tag', methods=['POST'])
@login_required
@admin_required
def create_tag():
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not name:
        return jsonify({'success': False, 'error': 'Tag name is required.'}), 400

    if Tag.query.filter_by(name=name).first():
        return jsonify({'success': False, 'error': f'Tag "{name}" already exists.'}), 409

    new_tag = Tag(name=name, description=description, is_active=True)
    db.session.add(new_tag)
    db.session.commit()
    return jsonify({'success': True, 'id': new_tag.id})

@admin_bp.route('/sys/api/tag/<int:tid>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_tag(tid):
    tag = db.get_or_404(Tag, tid)

    if request.method == 'DELETE':
        db.session.delete(tag)
        db.session.commit()
        return jsonify({'success': True})

    data = request.get_json()
    if 'name' in data:
        tag.name = data['name'].strip()
    if 'description' in data:
        tag.description = data['description'].strip()
    if 'is_active' in data:
        tag.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/api/tags/active', methods=['GET'])
@login_required
def get_active_tags():
    tags = Tag.query.filter_by(is_active=True).order_by(Tag.id).all()
    return jsonify([{'id': t.id, 'name': t.name} for t in tags])


# ── Users API ─────────────────────────────────────────────────────────────────

@admin_bp.route('/sys/api/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    users = User.query.order_by(User.role, User.username).all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'full_name': u.full_name or '',
        'role': u.role,
        'is_active': u.is_active,
        'created_at': str(u.created_at)
    } for u in users])


@admin_bp.route('/sys/api/user', methods=['POST'])
@login_required
@admin_required
def create_user():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    role = data.get('role', 'operator')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password are required.'}), 400

    valid_roles = ('admin', 'supervisor', 'operator', 'inspector')
    if role not in valid_roles:
        return jsonify({'success': False, 'error': 'Invalid role.'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': f'Username "{username}" already exists.'}), 409

    new_user = User(username=username, full_name=full_name or None, role=role, is_active=True)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'success': True, 'id': new_user.id})


@admin_bp.route('/sys/api/user/<int:uid>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_user(uid):
    user = db.get_or_404(User, uid)

    if request.method == 'DELETE':
        if user.role == 'admin':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count <= 1:
                return jsonify({'success': False, 'error': 'Cannot delete the only Admin account in the system.'}), 400
        
        is_self = (user.id == current_user.id)
        
        db.session.delete(user)
        db.session.commit()
        
        if is_self:
            logout_user()
            return jsonify({
                'success': True, 
                'redirect': url_for('auth.login'), 
                'message': 'You have deleted your own account and been logged out.'
            })
            
        return jsonify({'success': True})

    data = request.get_json()
    if 'full_name' in data:
        user.full_name = data['full_name'].strip() or None
    if 'role' in data:
        valid_roles = ('admin', 'supervisor', 'operator', 'inspector')
        if data['role'] in valid_roles:
            user.role = data['role']
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    if 'password' in data and data['password'].strip():
        user.set_password(data['password'].strip())
    db.session.commit()
    return jsonify({'success': True})

# ═══════════════════════════════════════════════════════════════════════════
#  PRINT SPECIFIC QC REPORT
# ═══════════════════════════════════════════════════════════════════════════
@admin_bp.route('/admin/print-specific-qc', methods=['GET'])
@login_required
def print_specific_qc():
    model = request.args.get('model', '').strip()
    serial = request.args.get('serial', '').strip()
    
    if not model or not serial:
        return "Model and Serial are required.", 400
        
    # Get base CRS record
    crs_record = CRS.query.filter_by(modelcode=model, serial=serial).first()
    if not crs_record:
        return f"No records found for Model {model} and Serial {serial}.", 404
        
    # Get Gas Charge
    gms_record = GMS.query.filter_by(modelcode=model, serial=serial).first()
    gas_charge = gms_record.gascharge if gms_record else None
    
    # Get PartRef BOM
    bom = PartRef.query.filter_by(modelcode=model).all()
    
    parts_list = []
    
    # Helper to parse 8-digit date
    def parse_mfg_date(serial_str):
        if not serial_str:
            return ""
        # The first 8 chars might be YYYYMMDD
        potential_date = serial_str.split('|')[0].strip()
        if len(potential_date) >= 8 and potential_date[:8].isdigit():
            dt_str = potential_date[:8]
            try:
                # format to MM/DD/YYYY
                dt = datetime.strptime(dt_str, "%Y%m%d")
                return dt.strftime("%m/%d/%Y")
            except:
                pass
        return ""
        
    # We map CRS parts for easy matching
    crs_parts_map = {
        crs_record.compmod: crs_record.compserial,
        crs_record.fan1mod: crs_record.fan1serial,
        crs_record.fan2mod: crs_record.fan2serial,
        crs_record.part1mod: crs_record.part1serial,
        crs_record.part2mod: crs_record.part2serial,
        crs_record.part3mod: crs_record.part3serial,
        crs_record.part4mod: crs_record.part4serial
    }
    
    # For Arrival date from other modules
    spams_record = SPAMS.query.filter_by(modelcode=model, serial=serial).first()
    cb_record = CBPCB.query.filter_by(modelcode=model, serial=serial).first()
    
    for part in bom:
        p_serial = crs_parts_map.get(part.partno)
        mfg_date = parse_mfg_date(p_serial)
        
        arv_date = ""
        if part.module.upper() == 'CRS':
            arv_date = crs_record.time.strftime("%m/%d/%Y") if crs_record.time else ""
        elif part.module.upper() == 'SPAMS':
            arv_date = spams_record.time.strftime("%m/%d/%Y") if spams_record and spams_record.time else ""
        elif part.module.upper() == 'CB':
            arv_date = cb_record.time.strftime("%m/%d/%Y") if cb_record and cb_record.time else ""
            
        parts_list.append({
            'partno': part.partno,
            'partdesc': part.partdesc,
            'module': part.module,
            'mfg_date': mfg_date,
            'arv_date': arv_date
        })
        
    return render_template(
        'admin/qc_report_print.html',
        model=model,
        serial=serial,
        crs_record=crs_record,
        gas_charge=gas_charge,
        parts_list=parts_list,
        current_time=datetime.now()
    )