"""Admin routes — Administrator module page and CRUD APIs."""
import logging
from flask import Blueprint, session, render_template, jsonify, request, redirect, url_for
from datetime import datetime
from functools import wraps
from flask_login import login_required, current_user, logout_user
from sqlalchemy import func
from app.models import db
from app.models.worksched import WorkSched
from app.models.linestat import LineStat

from app.models.partref import PartRef
from app.models.crs import CRS
from app.models.gms import GMS
from app.models.att import ATT
from app.models.spamsi import SPAMSI
from app.models.packaging import Packaging
from app.models.spamso import SPAMSO
from app.models.insp2 import INSP2
from app.models.insp3_run import INSP3Run
from app.models.insp4 import INSP4

from app.models.line import Line
from app.models.module import Module
from app.models.shift import Shift
from app.models.tag import Tag
from app.models.area import Area
from app.models.spamsi_unique_ref import SPAMSIUniqueRef
from app.models.spamso_outmodel_ref import SpamsoOutmodelRef
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
    from app.models.line import Line
    lines = Line.query.filter_by(is_active=True).all()
    result = []
    for l in lines:
        result.append({'id': l.id, 'line_code': l.lineno, 'name': l.name})
    return jsonify(result)

@admin_bp.route('/admin/api/schedules', methods=['GET'])
@login_required
def get_schedules():
    date_str = request.args.get('date')
    line_id = request.args.get('line_id', 'all')

    query = WorkSched.query
    parsed_date = None
    if date_str:
        try:
            parsed_date = datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            pass

    lineno_str = None
    if line_id != 'all':
        lineno_str = line_id if line_id.startswith('L') else f"L{line_id}"
        query = query.filter_by(lineno=lineno_str)

    wip_status = None
    ghost_date = None
    if parsed_date:
        if lineno_str:
            # Single Line View: Find the most recent date that HAS unfinished work
            ghost_date_query = db.session.query(db.func.max(WorkSched.date)).filter(
                WorkSched.date < parsed_date,
                WorkSched.lineno == lineno_str,
                WorkSched.act < WorkSched.plan
            )
            ghost_date = ghost_date_query.scalar()
            
            if ghost_date:
                active_models = []
                from app.models.linestat import LineStat
                linestat = LineStat.query.filter_by(lineno=lineno_str).first()
                
                def get_sched_stats(modelcode):
                    s = WorkSched.query.filter_by(date=ghost_date, lineno=lineno_str, modelcode=modelcode).first()
                    if s: return s.plan, s.act
                    return 0, 0
                
                # Only map to physical line if the physical line is actively stuck on this exact ghost_date
                if linestat and linestat.active_date == ghost_date:
                    if linestat.crsvar and linestat.crsvar > 0:
                        p, a = get_sched_stats(linestat.crsmodelcode)
                        active_models.append({'station': 'CRS', 'model': linestat.crsmodelcode, 'var': linestat.crsvar, 'plan': p, 'act': a})
                    if linestat.attvar and linestat.attvar > 0:
                        p, a = get_sched_stats(linestat.attmodelcode)
                        active_models.append({'station': 'ATT', 'model': linestat.attmodelcode, 'var': linestat.attvar, 'plan': p, 'act': a})
                    if linestat.gmsvar and linestat.gmsvar > 0:
                        p, a = get_sched_stats(linestat.gmsmodelcode)
                        active_models.append({'station': 'GMS', 'model': linestat.gmsmodelcode, 'var': linestat.gmsvar, 'plan': p, 'act': a})
                    if linestat.invar and linestat.invar > 0:
                        p, a = get_sched_stats(linestat.inmodelcode)
                        active_models.append({'station': 'SPAMSI', 'model': linestat.inmodelcode, 'var': linestat.invar, 'plan': p, 'act': a})
                    if linestat.outvar and linestat.outvar > 0:
                        p, a = get_sched_stats(linestat.outmodelcode)
                        active_models.append({'station': 'SPAMSO', 'model': linestat.outmodelcode, 'var': linestat.outvar, 'plan': p, 'act': a})

                active_model_codes = [m['model'] for m in active_models]
                unstarted = []
                past_scheds = WorkSched.query.filter_by(date=ghost_date, lineno=lineno_str).all()
                for ps in past_scheds:
                    if ps.act < ps.plan and ps.modelcode not in active_model_codes:
                        unstarted.append({'id': ps.id, 'model': ps.modelcode, 'plan': ps.plan})

                wip_status = {
                    'active_date': ghost_date.strftime('%m/%d/%Y'),
                    'active_models': active_models,
                    'unstarted': unstarted
                }
        else:
            # All Lines View: Find max(date) with unfinished work per line
            subq = db.session.query(
                WorkSched.lineno, 
                db.func.max(WorkSched.date).label('max_date')
            ).filter(
                WorkSched.date < parsed_date,
                WorkSched.act < WorkSched.plan
            ).group_by(WorkSched.lineno).all()
            
            lines_list = [{'line': r[0], 'date': r[1].strftime('%m/%d/%Y')} for r in subq if r[0]]
            if lines_list:
                wip_status = {
                    'active_date': 'multiple',
                    'lines_with_wip': lines_list
                }

    from sqlalchemy import or_
    if ghost_date and lineno_str:
        query = query.filter(
            or_(
                WorkSched.date == parsed_date,
                (WorkSched.date == ghost_date) & (WorkSched.act < WorkSched.plan)
            )
        )
    elif parsed_date and not lineno_str and wip_status and 'lines_with_wip' in wip_status:
        # In all view, pull today's schedules PLUS any unfinished schedules from each line's max_date
        subq = db.session.query(
            WorkSched.lineno, 
            db.func.max(WorkSched.date).label('max_date')
        ).filter(
            WorkSched.date < parsed_date,
            WorkSched.act < WorkSched.plan
        ).group_by(WorkSched.lineno).subquery()
        
        query = query.outerjoin(
            subq,
            WorkSched.lineno == subq.c.lineno
        ).filter(
            or_(
                WorkSched.date == parsed_date,
                (WorkSched.date == subq.c.max_date) & (WorkSched.act < WorkSched.plan)
            )
        )
    else:
        query = query.filter(WorkSched.date == parsed_date)

    schedules = query.order_by(WorkSched.date.asc(), WorkSched.lineno, WorkSched.seq).all()

    # Build set of valid modelcodes for has_bom flag
    valid_models = set(
        mc for (mc,) in db.session.query(PartRef.modelcode).distinct().all()
    )

    from app.models.linestat import LineStat
    linestat_dict = {ls.lineno: ls for ls in LineStat.query.all()}

    schedules_data = []
    total_qty = 0
    for s in schedules:
        is_ghost = False
        if parsed_date and s.date < parsed_date and s.act < s.plan:
            is_ghost = True
            
        if not is_ghost:
            total_qty += s.plan
            
        is_locked = False
        is_queued_at_crs = False
        ls = linestat_dict.get(s.lineno)
        if ls:
            is_on_belt = (ls.crsmodelcode == s.modelcode or ls.attmodelcode == s.modelcode or ls.gmsmodelcode == s.modelcode or ls.inmodelcode == s.modelcode or ls.outmodelcode == s.modelcode)
            if s.act > 0:
                is_locked = True
            elif is_on_belt:
                if ls.attmodelcode == s.modelcode or ls.gmsmodelcode == s.modelcode or ls.inmodelcode == s.modelcode or ls.outmodelcode == s.modelcode:
                    is_locked = True
                elif ls.crsmodelcode == s.modelcode and ls.crsvar < s.plan:
                    is_locked = True
            
            is_queued_at_crs = is_on_belt and not is_locked

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
            'is_ghost': is_ghost,
            'is_locked': is_locked,
            'is_queued_at_crs': is_queued_at_crs,
        })

    return jsonify({
        'date': date_str,
        'total_qty': total_qty,
        'schedules': schedules_data,
        'wip_status': wip_status,
    })

@admin_bp.route('/admin/api/wip-resolve', methods=['POST'])
@login_required
@admin_required
def wip_resolve():
    from app.models.worksched import WorkSched
    from app.models.linestat import LineStat
    
    data = request.get_json()
    line_code = data.get('line_id')
    action = data.get('action') # 'clear' or 'continue'
    crs_new_plan = data.get('crs_new_plan')
    unstarted_plans = data.get('unstarted_plans', {})
    
    if not line_code:
        return jsonify({'success': False, 'error': 'Missing line code'})
        
    lineno = line_code if str(line_code).startswith('L') else f"L{line_code}"
    from datetime import datetime
    today_date = datetime.now().date()
    
    # Find the most recent date before today that has schedules
    ghost_date = db.session.query(db.func.max(WorkSched.date)).filter(
        WorkSched.date < today_date,
        WorkSched.lineno == lineno
    ).scalar()
    
    if not ghost_date:
        return jsonify({'success': False, 'error': 'No past schedules found to resolve.'})
        
    unfinished_scheds = WorkSched.query.filter(
        WorkSched.lineno == lineno,
        WorkSched.date == ghost_date,
        WorkSched.act < WorkSched.plan
    ).all()
    
    if not unfinished_scheds:
        return jsonify({'success': False, 'error': 'No unfinished schedules found on the most recent date.'})
        
    if action == 'clear':
        # Discard & Clear all
        for sched in unfinished_scheds:
            sched.plan = sched.act
            
        linestat = LineStat.query.filter_by(lineno=lineno).first()
        if linestat:
            from datetime import datetime
            linestat.status = 'No Work'
            linestat.active_date = None
            linestat.crsmodelcode = None
            linestat.crsvar = 0
            linestat.attmodelcode = None
            linestat.attvar = 0
            linestat.gmsmodelcode = None
            linestat.gmsvar = 0
            linestat.inmodelcode = None
            linestat.invar = 0
            linestat.inuniqe = None
            linestat.inpart1mod = None
            linestat.inpart1desc = None
            linestat.inpart2mod = None
            linestat.inpart2desc = None
            linestat.inpart3mod = None
            linestat.inpart3desc = None
            linestat.inpart4mod = None
            linestat.inpart4desc = None
            linestat.inpart5mod = None
            linestat.inpart5desc = None
            linestat.inpart6mod = None
            linestat.inpart6desc = None
            linestat.outmodelcode = None
            linestat.outvar = 0
            linestat.outpart1mod = None
            linestat.outpart1desc = None
            linestat.outpart2mod = None
            linestat.outpart2desc = None
            linestat.outpart3mod = None
            linestat.outpart3desc = None
            linestat.compmod = None
            linestat.fan1mod = None
            linestat.fan2mod = None
            linestat.crspart1mod = None
            linestat.crspart1desc = None
            linestat.crspart2mod = None
            linestat.crspart2desc = None
            linestat.crspart3mod = None
            linestat.crspart3desc = None
            linestat.crspart4mod = None
            linestat.crspart4desc = None
            linestat.area = None
            linestat.serialstart = None
            linestat.gascharge = 0
            linestat.updtime = datetime.now()
            
        db.session.commit()
        return jsonify({'success': True})
        
    elif action == 'continue':
        linestat = LineStat.query.filter_by(lineno=lineno).first()
        active_model_codes = set()
        
        if linestat and linestat.active_date == ghost_date:
            if linestat.crsvar and linestat.crsvar > 0:
                active_model_codes.add(linestat.crsmodelcode)
            if linestat.attvar and linestat.attvar > 0:
                active_model_codes.add(linestat.attmodelcode)
            if linestat.gmsvar and linestat.gmsvar > 0:
                active_model_codes.add(linestat.gmsmodelcode)
            if linestat.invar and linestat.invar > 0:
                active_model_codes.add(linestat.inmodelcode)
            if linestat.outvar and linestat.outvar > 0:
                active_model_codes.add(linestat.outmodelcode)
                
        # Get next sequence number for today
        last_sched = WorkSched.query.filter_by(lineno=lineno, date=today_date).order_by(WorkSched.seq.desc()).first()
        next_seq = 0 if not last_sched else last_sched.seq + 1
        
        for sched in unfinished_scheds:
            if sched.modelcode not in active_model_codes:
                # Unstarted schedule
                if str(sched.id) in unstarted_plans:
                    # User checked it -> create new schedule for today
                    
                    new_plan_val = sched.plan
                    try:
                        if unstarted_plans[str(sched.id)]:
                            new_plan_val = int(unstarted_plans[str(sched.id)])
                    except ValueError:
                        pass
                        
                    new_sched = WorkSched(
                        lineno=lineno,
                        seq=next_seq,
                        modelcode=sched.modelcode,
                        plan=new_plan_val,
                        act=0,
                        takttime=sched.takttime,
                        date=today_date
                    )
                    db.session.add(new_sched)
                    next_seq += 1
                
                # Close out yesterday's schedule
                sched.plan = sched.act
                
            else:
                # Active model on the conveyor
                max_var = 0
                if linestat.crsmodelcode == sched.modelcode and linestat.crsvar:
                    max_var = max(max_var, linestat.crsvar)
                if linestat.attmodelcode == sched.modelcode and linestat.attvar:
                    max_var = max(max_var, linestat.attvar)
                if linestat.gmsmodelcode == sched.modelcode and linestat.gmsvar:
                    max_var = max(max_var, linestat.gmsvar)
                if linestat.inmodelcode == sched.modelcode and linestat.invar:
                    max_var = max(max_var, linestat.invar)
                if linestat.outmodelcode == sched.modelcode and linestat.outvar:
                    max_var = max(max_var, linestat.outvar)
                    
                final_plan = max_var
                
                # If they updated the plan for the CRS model, check if it's higher
                if linestat.crsmodelcode == sched.modelcode and crs_new_plan:
                    try:
                        crs_plan_val = int(crs_new_plan)
                        if crs_plan_val > final_plan:
                            final_plan = crs_plan_val
                    except ValueError:
                        pass
                
                if final_plan > 0:
                    new_sched = WorkSched(
                        lineno=lineno,
                        seq=next_seq,
                        modelcode=sched.modelcode,
                        plan=final_plan,
                        act=0, 
                        takttime=sched.takttime,
                        date=today_date
                    )
                    db.session.add(new_sched)
                    next_seq += 1
                    
                sched.plan = sched.act
                
        db.session.commit()
        return jsonify({'success': True})
        
    return jsonify({'success': False, 'error': 'Invalid action'})

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
    return jsonify({'success': True, 'id': new_sched.id})

@admin_bp.route('/admin/api/schedule/<int:sid>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_schedule(sid):
    sched = db.get_or_404(WorkSched, sid)
    
    linestat = LineStat.query.filter_by(lineno=sched.lineno).first()
    is_on_belt = False
    if linestat:
        if linestat.crsmodelcode == sched.modelcode or linestat.attmodelcode == sched.modelcode or linestat.gmsmodelcode == sched.modelcode or linestat.inmodelcode == sched.modelcode or linestat.outmodelcode == sched.modelcode:
            is_on_belt = True

    is_locked = False
    if sched.act > 0:
        is_locked = True
    elif is_on_belt:
        if linestat.attmodelcode == sched.modelcode or linestat.gmsmodelcode == sched.modelcode or linestat.inmodelcode == sched.modelcode or linestat.outmodelcode == sched.modelcode:
            is_locked = True
        elif linestat.crsmodelcode == sched.modelcode and linestat.crsvar < sched.plan:
            is_locked = True

    is_queued_at_crs = is_on_belt and not is_locked

    if request.method == 'DELETE':
        if is_locked:
            return jsonify({'success': False, 'error': 'Cannot delete: This schedule is actively running on the conveyor belt or has already produced units.'})
            
        if is_queued_at_crs:
            linestat.crsmodelcode = None
            linestat.crsvar = 0
            if linestat.status == 'Work' and not linestat.attmodelcode and not linestat.gmsmodelcode and not linestat.inmodelcode and not linestat.outmodelcode:
                linestat.status = 'No Work'
                
        lineno = sched.lineno
        date_val = sched.date
        db.session.delete(sched)
        db.session.commit()

        # Re-sequence remaining entries for this line+date, 0-based
        remaining = WorkSched.query.filter_by(lineno=lineno, date=date_val).order_by(WorkSched.seq).all()
        for idx, s in enumerate(remaining):
            s.seq = idx
        db.session.commit()
        return jsonify({'success': True})

    data = request.get_json()
    if 'model_number' in data and data['model_number'] != sched.modelcode:
        if is_on_belt or sched.act > 0:
            return jsonify({'success': False, 'error': 'Cannot change the Model Code while it is on the conveyor belt or has produced units.'})
        sched.modelcode = data['model_number']
        
    if 'planned_qty' in data:
        if is_locked:
            return jsonify({'success': False, 'error': 'Plan is locked: This model has already started running (units deducted) or advanced past CRS.'})
        try:
            new_plan = int(data['planned_qty'])
            if is_queued_at_crs:
                linestat.crsvar = new_plan
            sched.plan = new_plan
        except ValueError:
            pass
            
    if 'takt_time' in data:
        sched.takttime = data['takt_time']
        
    db.session.commit()
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
    models = db.session.query(PartRef.modelcode).distinct().order_by(PartRef.modelcode).all()
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
    """Delete all BOM rows and modelref for the given model code."""
    deleted = PartRef.query.filter_by(modelcode=modelcode).delete()
    from app.models.modelref import ModelRef
    ModelRef.query.filter_by(modelcode=modelcode).delete()
    SPAMSIUniqueRef.query.filter_by(modelcode=modelcode).delete()
    SpamsoOutmodelRef.query.filter_by(modelcode=modelcode).delete()
    db.session.commit()
    if deleted == 0:
        return jsonify({'success': False, 'error': 'Model not found.'}), 404
    return jsonify({'success': True, 'deleted_parts': deleted})


@admin_bp.route('/admin/api/modelref/<modelcode>', methods=['GET'])
@login_required
def get_modelref(modelcode):
    from app.models.modelref import ModelRef
    ref = ModelRef.query.filter_by(modelcode=modelcode).first()
    if not ref:
        return jsonify({'found': False})
    data = ref.to_dict()
    unique_ref = SPAMSIUniqueRef.query.filter_by(modelcode=modelcode).first()
    data['spamsi_unique_code'] = unique_ref.unique_code if unique_ref else None
    return jsonify({'found': True, 'data': data})

@admin_bp.route('/admin/api/modelref', methods=['GET'])
@login_required
def get_all_modelrefs():
    from app.models.modelref import ModelRef
    refs = ModelRef.query.all()
    unique_codes = {
        unique_ref.modelcode: unique_ref.unique_code
        for unique_ref in SPAMSIUniqueRef.query.all()
    }
    entries = []
    for ref in refs:
        entry = ref.to_dict()
        entry['spamsi_unique_code'] = unique_codes.get(ref.modelcode)
        entries.append(entry)
    return jsonify({'entries': entries})

@admin_bp.route('/admin/api/modelref/<modelcode>', methods=['PUT'])
@login_required
@admin_required
def update_modelref(modelcode):
    from app.models.modelref import ModelRef
    data = request.get_json() or {}
    
    # Check if this is a new model being created
    ref = ModelRef.query.filter_by(modelcode=modelcode).first()
    is_new_model = ref is None
    
    unique_code = None
    if 'spamsi_unique_code' in data:
        unique_code = str(data['spamsi_unique_code'] or '').strip()
        
        # SPAMSI Unique Code is required for new models
        if is_new_model and not unique_code:
            return jsonify({
                'success': False,
                'error': 'SPAMSI Unique Code is required for new models.'
            }), 400
        
        if len(unique_code) > 4:
            return jsonify({
                'success': False,
                'error': 'SPAMSI Unique Code must be 4 characters or fewer.'
            }), 400
        if unique_code:
            assigned = SPAMSIUniqueRef.query.filter_by(unique_code=unique_code).first()
            if assigned and assigned.modelcode != modelcode:
                return jsonify({
                    'success': False,
                    'error': 'This SPAMSI Unique Code is already assigned to another model.'
                }), 409
    
    if not ref:
        ref = ModelRef(modelcode=modelcode)
        db.session.add(ref)
    
    # Keep the PLC-compatible string contract while enforcing configured values.
    if 'area' in data:
        requested_area = (data['area'] or '').strip()
        if requested_area:
            area = Area.query.filter_by(name=requested_area).first()
            retaining_inactive_area = (
                ref.area == requested_area and area is not None and not area.is_active
            )
            if area is None or (not area.is_active and not retaining_inactive_area):
                return jsonify({
                    'success': False,
                    'error': 'Select an active configured area.'
                }), 400
        data['area'] = requested_area or None

    # Update fields
    import re
    for field in ['area', 'serialstart', 'program_h', 'program_f', 
                  'gmstolpos', 'gmstolneg', 'op_current_base', 'op_current_tolpos', 'op_current_tolneg',
                  'in_power_base', 'in_power_tolpos', 'in_power_tolneg', 'temp_diff_base', 'temp_diff_tolpos', 'temp_diff_tolneg']:
        if field in data:
            val = data[field]
            if field in ['program_h', 'program_f']:
                if val == '':
                    val = None
                elif val is not None and not re.match(r'^\d{2}:\d{2}$', str(val)):
                    return jsonify({'success': False, 'error': f'Invalid format for {field}. Must be NN:NN.'}), 400
            elif val == '' and field not in ['area', 'serialstart']:
                val = 0
            setattr(ref, field, val)

    if 'spamsi_unique_code' in data:
        unique_ref = SPAMSIUniqueRef.query.filter_by(modelcode=modelcode).first()
        if unique_code:
            if unique_ref:
                unique_ref.unique_code = unique_code
            else:
                db.session.add(SPAMSIUniqueRef(
                    modelcode=modelcode,
                    unique_code=unique_code,
                ))
        elif unique_ref:
            db.session.delete(unique_ref)
    
    if 'spamso_outmodel' in data:
        spamso_outmodel_val = str(data['spamso_outmodel'] or '').strip() or None
        outmodel_ref = SpamsoOutmodelRef.query.filter_by(modelcode=modelcode).first()
        if spamso_outmodel_val:
            if outmodel_ref:
                outmodel_ref.outmodel = spamso_outmodel_val
            else:
                db.session.add(SpamsoOutmodelRef(
                    modelcode=modelcode,
                    outmodel=spamso_outmodel_val,
                ))
        elif outmodel_ref:
            db.session.delete(outmodel_ref)
    
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/admin/api/bom', methods=['GET'])
@login_required
def get_bom():
    modelcode = request.args.get('modelcode')
    if not modelcode:
        return jsonify({'parts': []})

    # Order by ID ascending first to ensure new entries go to the bottom of their group
    entries = PartRef.query.filter_by(modelcode=modelcode).order_by(PartRef.id).all()
    
    # Sort modules in the order: CRS, GMS, SPAMSI, SPAMSO, CB
    module_order = {'crs': 1, 'gms': 2, 'spamsi': 3, 'spamso': 4, 'cb': 5}
    entries.sort(key=lambda e: module_order.get((e.module or '').lower(), 99))
    
    from app.models.modelref import ModelRef
    model_config = {}
    ref = ModelRef.query.filter_by(modelcode=modelcode).first()
    if ref:
        model_config = ref.to_dict()

    return jsonify({
        'parts': [{
            'id': e.id,
            'module_code': e.module,
            'part_number': e.partno,
            'description': e.partdesc,
            'usage_qty': float(e.usage),
            'tag': e.tag,
        } for e in entries],
        'model_config': model_config
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
    return jsonify({'success': True, 'id': new_part.id})

@admin_bp.route('/admin/api/bom/<int:bid>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_bom(bid):
    part = db.get_or_404(PartRef, bid)
    if request.method == 'DELETE':
        db.session.delete(part)
        db.session.commit()
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
    return jsonify({'success': True})

# ── Model Reference (Serial Start) CRUD ─────────────────────────────────────

VALID_AREAS = ('Domestic', 'HongKong', 'Export', 'Taiwan')

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
    per_page = max(1, int(request.args.get('per_page', 50)))
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
        return jsonify({'success': True})
    
    data = request.get_json()
    fields = ['modelcode', 'serial', 'compmod', 'compserial', 'fan1mod', 'fan1serial', 'fan2mod', 'fan2serial']
    for f in fields:
        if f in data:
            setattr(record, f, data[f])
    db.session.commit()
    return jsonify({'success': True})


# ── GMS Data Viewer ───────────────────────────────────────────────────────────

@admin_bp.route('/admin/api/gms-data', methods=['GET'])
@login_required
def get_gms_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
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
            'remarks': '[Past NG History]' if ng.get(r.serial) else ''
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
        return jsonify({'success': True})
    
    data = request.get_json()
    if 'modelcode' in data: record.modelcode = data['modelcode']
    if 'serial' in data: record.serial = data['serial']
    if 'gascharge' in data: record.gascharge = data['gascharge']
    if 'status' in data: record.status = data['status']
    db.session.commit()
    return jsonify({'success': True})


# ── ATT / Safety Parts Data Viewer ───────────────────────────────────────────

@admin_bp.route('/admin/api/att-data', methods=['GET'])
@login_required
def get_att_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
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
            'lineno':    r.lineno or '',
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
    return jsonify({'success': True})



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
    from app.models.insp4 import INSP4
    from app.models.packaging import Packaging
    
    insp2_record = INSP2.query.filter_by(serial=serial).order_by(INSP2.id.desc()).first()
    insp3_run_record = INSP3Run.query.filter_by(serial=serial).order_by(INSP3Run.id.desc()).first()
    insp4_record = INSP4.query.filter_by(serial=serial).order_by(INSP4.id.desc()).first()
    pack_record = Packaging.query.filter_by(serial=serial).order_by(Packaging.id.desc()).first()
    
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
        
        'pack_status1': pack_record.status1 if pack_record else '',
        'pack_status2': pack_record.status2 if pack_record else '',
        'pack_status3': pack_record.status3 if pack_record else '',
        'pack_status4': pack_record.status4 if pack_record else '',
        'pack_inspector': pack_record.inspector if pack_record else '',
    }
    return render_template('admin/print_tag.html', unit=unit_data)

# ── New Quality Inspection Station APIs ───────────────────────────────────────


def _check_ng_history(records):
    return {}

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

@admin_bp.route('/admin/api/spamsi-data', methods=['GET'])
@login_required
def get_spamsi_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
    total, records = _get_paginated_data(
        SPAMSI, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{
            'id': r.id, 
            'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '', 
            'modelcode': r.modelcode, 
            'serial': r.serial, 
            'inspector': r.inspector or '—', 
            'inserial': r.inserial,
            'part1mod': r.part1mod, 'part1desc': r.part1desc, 'part1serial': r.part1serial,
            'part2mod': r.part2mod, 'part2desc': r.part2desc, 'part2serial': r.part2serial,
            'part3mod': r.part3mod, 'part3desc': r.part3desc, 'part3serial': r.part3serial,
            'part4mod': r.part4mod, 'part4desc': r.part4desc, 'part4serial': r.part4serial,
            'part5mod': r.part5mod, 'part5desc': r.part5desc, 'part5serial': r.part5serial,
            'part6mod': r.part6mod, 'part6desc': r.part6desc, 'part6serial': r.part6serial,
            'lineno': r.lineno
        } for r in records]
    })

@admin_bp.route('/admin/api/spamso-data', methods=['GET'])
@login_required
def get_spamso_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
    total, records = _get_paginated_data(
        SPAMSO, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{
            'id': r.id, 
            'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '', 
            'modelcode': r.modelcode, 
            'serial': r.serial, 
            'inspector': r.inspector or '—', 
            'outmodel': r.outmodel,
            'outserial': r.outserial,
            'part1mod': r.part1mod, 'part1desc': r.part1desc, 'part1serial': r.part1serial,
            'part2mod': r.part2mod, 'part2desc': r.part2desc, 'part2serial': r.part2serial,
            'part3mod': r.part3mod, 'part3desc': r.part3desc, 'part3serial': r.part3serial,
            'lineno': r.lineno
        } for r in records]
    })



@admin_bp.route('/admin/api/insp2-data', methods=['GET'])
@login_required
def get_insp2_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
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
    per_page = max(1, int(request.args.get('per_page', 50)))
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
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '', 'modelcode': r.modelcode, 'serial': r.serial, 'status': r.status, 'inspector': r.inspector or '—', 'insulation_resistance': r.insulation_resistance or '', 'withstand_voltage': r.withstand_voltage or '', 'leak_status': r.leak_status or '', 'leak_location': r.leak_location or '', 'prog_check_h': r.prog_check_h or '', 'prog_check_f': r.prog_check_f or '', 'airswing': r.airswing or '', 'comp_operation': r.comp_operation or '', 'fan_operation': r.fan_operation or '', 'evap_tubes': r.evap_tubes_cool or r.evap_tubes_heat or '', 'cond_tubes': r.cond_tubes_cool or r.cond_tubes_heat or '', 'operating_current': str(r.operating_current) if r.operating_current is not None else '', 'input_power': str(r.input_power) if r.input_power is not None else '', 'temp_diff': str(r.temp_diff) if r.temp_diff is not None else '', 'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')} for r in records]
    })




@admin_bp.route('/admin/api/packaging-data', methods=['GET'])
def get_packaging_data():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    sort_by = request.args.get('sort_by', 'time')
    sort_dir = request.args.get('sort_dir', 'desc')
    date_filter = request.args.get('date', '')
    serial_filter = request.args.get('serial', '')

    query = Packaging.query

    if date_filter:
        try:
            target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Packaging.time) == target_date)
        except ValueError:
            pass
    if serial_filter:
        query = query.filter(Packaging.serial.ilike(f'%{serial_filter}%'))

    if sort_by == 'time':
        order_col = Packaging.time.desc() if sort_dir == 'desc' else Packaging.time.asc()
    elif sort_by == 'modelcode':
        order_col = Packaging.modelcode.desc() if sort_dir == 'desc' else Packaging.modelcode.asc()
    elif sort_by == 'serial':
        order_col = Packaging.serial.desc() if sort_dir == 'desc' else Packaging.serial.asc()
    elif sort_by == 'status':
        order_col = Packaging.status1.desc() if sort_dir == 'desc' else Packaging.status1.asc()
    elif sort_by == 'inspector':
        order_col = Packaging.inspector.desc() if sort_dir == 'desc' else Packaging.inspector.asc()
    else:
        order_col = Packaging.time.desc()

    query = query.order_by(order_col)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '', 'modelcode': r.modelcode, 'serial': r.serial, 'status1': r.status1, 'status2': r.status2, 'status3': r.status3, 'status4': r.status4, 'inspector': r.inspector or '—'} for r in pagination.items]
    })

@admin_bp.route('/admin/api/packaging-data/<int:id>', methods=['PUT', 'DELETE'])
def handle_packaging_record(id):
    record = Packaging.query.get(id)
    if not record:
        return jsonify({'error': 'Record not found'}), 404

    if request.method == 'DELETE':
        db.session.delete(record)
        db.session.commit()
        return jsonify({'success': True})
    else:
        data = request.get_json() or {} or {}
        if 'status1' in data: record.status1 = data['status1']
        if 'status2' in data: record.status2 = data['status2']
        if 'status3' in data: record.status3 = data['status3']
        if 'status4' in data: record.status4 = data['status4']
        if 'inspector' in data: record.inspector = data['inspector']
        db.session.commit()
        return jsonify({'success': True, 'record': record.to_dict()})

@admin_bp.route('/admin/api/insp4-data', methods=['GET'])
@login_required
def get_insp4_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
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
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '', 'modelcode': r.modelcode, 'serial': r.serial, 'status': r.status, 'inspector': r.inspector or '—', 'insulation_resistance': r.insulation_resistance or '', 'operating_current': r.operating_current or '', 'nameplate_match': r.nameplate_match or '', 'model_label': r.model_label or '', 'manual_remote': r.manual_remote or '', 'manual_warranty': r.manual_warranty or '', 'manual_screws': r.manual_screws or '', 'grille_eel': r.grille_eel or '', 'grille_model': r.grille_model or '', 'grille_logo': r.grille_logo or '', 'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')} for r in records]
    })



@admin_bp.route('/admin/api/prod-tag-tracker', methods=['GET'])
@login_required
def get_prod_tag_tracker():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
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

    def standardize_status(st):
        if not st: return 'PENDING'
        st_upper = str(st).upper()
        if st_upper == 'GOOD': return 'GOOD'
        if st_upper in ('NG', 'NO GOOD', 'FAIL', 'FAILED'): return 'NO GOOD'
        return st_upper

    def get_latest_statuses(model):
        subquery = db.session.query(model.serial, func.max(model.time).label('maxtime')).filter(model.serial.in_(serials)).group_by(model.serial).subquery()
        records = db.session.query(model).join(subquery, db.and_(model.serial == subquery.c.serial, model.time == subquery.c.maxtime)).all()
        return {r.serial: r.status for r in records}

    att_status = get_latest_statuses(ATT)
    gms_status = get_latest_statuses(GMS)
    spamsi_status = get_latest_statuses(SPAMSI)
    spamso_status = get_latest_statuses(SPAMSO)
    insp2_status = get_latest_statuses(INSP2)
    insp3run_status = get_latest_statuses(INSP3Run)
    packaging_status = get_latest_statuses(Packaging)
    insp4_status = get_latest_statuses(INSP4)
    results = []
    for r in crs_records:
        s = r.serial
        # A serial is considered Ready to Print if ALL inspection stations are OK.
        stations = {
            'CRS': 'GOOD',
            'ATT': standardize_status(att_status.get(s)),
            'GMS': standardize_status(gms_status.get(s)),
            'SPAMSI': standardize_status(spamsi_status.get(s)),
            'SPAMSO': standardize_status(spamso_status.get(s)),
            'INSP2': standardize_status(insp2_status.get(s)),
            'INSP3Run': standardize_status(insp3run_status.get(s)),
            'INSP4': standardize_status(insp4_status.get(s)),
            'Packaging': standardize_status(packaging_status.get(s))
        }
        
        # Check if all required stations are GOOD/PASS/OK
        required_stations = ['CRS', 'ATT', 'GMS', 'SPAMSI', 'SPAMSO', 'INSP2', 'INSP3Run', 'INSP4', 'Packaging']
        all_good = True
        for st in required_stations:
            if stations[st].upper() not in ('GOOD', 'PASS', 'OK'):
                all_good = False
                break
                
        tag_status = 'READY' if all_good else 'NOT READY'
        
        results.append({
            'modelcode': r.modelcode,
            'serial': s,
            'crs': standardize_status(stations['CRS']),
            'att': standardize_status(stations['ATT']),
            'gms': standardize_status(stations['GMS']),
            'spamsi': standardize_status(stations['SPAMSI']),
            'spamso': standardize_status(stations['SPAMSO']),
            'insp2': standardize_status(stations['INSP2']),
            'insp3': standardize_status(stations['INSP3Run']),
            'insp4': standardize_status(stations['INSP4']),
            'packaging': standardize_status(stations['Packaging']),
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


# Areas are configuration labels. modelref.area remains the string consumed by
# the line-state stored procedure and is intentionally not a foreign key.
@admin_bp.route('/sys/api/areas', methods=['GET'])
@login_required
@admin_required
def get_areas():
    areas = Area.query.order_by(Area.id).all()
    return jsonify([{
        'id': area.id,
        'name': area.name,
        'description': area.description,
        'is_active': area.is_active,
        'created_at': str(area.created_at),
    } for area in areas])


@admin_bp.route('/sys/api/area', methods=['POST'])
@login_required
@admin_required
def create_area():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not name:
        return jsonify({'success': False, 'error': 'Area name is required.'}), 400
    if len(name) > 50:
        return jsonify({'success': False, 'error': 'Area name must be 50 characters or fewer.'}), 400
    if Area.query.filter_by(name=name).first():
        return jsonify({'success': False, 'error': f'Area "{name}" already exists.'}), 409

    area = Area(name=name, description=description, is_active=True)
    db.session.add(area)
    db.session.commit()
    return jsonify({'success': True, 'id': area.id})


@admin_bp.route('/sys/api/area/<int:area_id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def edit_delete_area(area_id):
    area = db.get_or_404(Area, area_id)
    from app.models.modelref import ModelRef
    referenced = ModelRef.query.filter_by(area=area.name).first()

    if request.method == 'DELETE':
        if referenced:
            return jsonify({
                'success': False,
                'error': 'This area is assigned to model references and cannot be deleted. Set it inactive instead.'
            }), 409
        db.session.delete(area)
        db.session.commit()
        return jsonify({'success': True})

    data = request.get_json() or {}
    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'success': False, 'error': 'Area name is required.'}), 400
        if len(name) > 50:
            return jsonify({'success': False, 'error': 'Area name must be 50 characters or fewer.'}), 400
        if name != area.name:
            if referenced:
                return jsonify({
                    'success': False,
                    'error': 'This area is assigned to model references and cannot be renamed.'
                }), 409
            if Area.query.filter_by(name=name).first():
                return jsonify({'success': False, 'error': f'Area "{name}" already exists.'}), 409
            area.name = name
    if 'description' in data:
        area.description = data['description'].strip()
    if 'is_active' in data:
        area.is_active = bool(data['is_active'])
    db.session.commit()
    return jsonify({'success': True})


@admin_bp.route('/api/areas/active', methods=['GET'])
@login_required
def get_active_areas():
    areas = Area.query.filter_by(is_active=True).order_by(Area.name).all()
    return jsonify([{'id': area.id, 'name': area.name} for area in areas])


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
    
    if 'username' in data and data['username'].strip():
        new_username = data['username'].strip()
        if new_username != user.username:
            existing = User.query.filter_by(username=new_username).first()
            if existing:
                return jsonify({'success': False, 'error': f"Username '{new_username}' is already in use."}), 400
            user.username = new_username

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
    spamsi_record = SPAMSI.query.filter_by(modelcode=model, serial=serial).first()
    spamso_record = SPAMSO.query.filter_by(modelcode=model, serial=serial).first()
    packaging_record = Packaging.query.filter_by(modelcode=model, serial=serial).first()
    
    for part in bom:
        p_serial = crs_parts_map.get(part.partno)
        mfg_date = parse_mfg_date(p_serial)
        
        arv_date = ""
        if part.module.upper() == 'CRS':
            arv_date = crs_record.time.strftime("%m/%d/%Y") if crs_record.time else ""
        elif part.module.upper() == 'SPAMSI':
            arv_date = spamsi_record.time.strftime("%m/%d/%Y") if spamsi_record and spamsi_record.time else ""
        elif part.module.upper() == 'SPAMSO':
            arv_date = spamso_record.time.strftime("%m/%d/%Y") if spamso_record and spamso_record.time else ""
        elif part.module.upper() == 'PACKAGING':
            arv_date = packaging_record.time.strftime("%m/%d/%Y") if packaging_record and packaging_record.time else ""
            
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

@admin_bp.route('/admin/api/linestat-viewer', methods=['GET'])
@login_required
@admin_required
def get_linestat_viewer():
    from app.models.linestat import LineStat
    try:
        entries = LineStat.query.order_by(LineStat.lineno).all()
        return jsonify([{
            'id': e.id,
            'lineno': e.lineno,
            'status': e.status,
            'crsmodelcode': e.crsmodelcode,
            'crsvar': e.crsvar,
            'attmodelcode': e.attmodelcode,
            'attvar': e.attvar,
            'gmsmodelcode': e.gmsmodelcode,
            'gmsvar': e.gmsvar,
            'inmodelcode': e.inmodelcode,
            'invar': e.invar,
            'inuniqe': e.inuniqe,
            'inpart1mod': e.inpart1mod,
            'inpart1desc': e.inpart1desc,
            'inpart2mod': e.inpart2mod,
            'inpart2desc': e.inpart2desc,
            'inpart3mod': e.inpart3mod,
            'inpart3desc': e.inpart3desc,
            'inpart4mod': e.inpart4mod,
            'inpart4desc': e.inpart4desc,
            'inpart5mod': e.inpart5mod,
            'inpart5desc': e.inpart5desc,
            'inpart6mod': e.inpart6mod,
            'inpart6desc': e.inpart6desc,
            'outmodelcode': e.outmodelcode,
            'outvar': e.outvar,
            'outpart1mod': e.outpart1mod,
            'outpart1desc': e.outpart1desc,
            'outpart2mod': e.outpart2mod,
            'outpart2desc': e.outpart2desc,
            'outpart3mod': e.outpart3mod,
            'outpart3desc': e.outpart3desc,
            'wcmodelcode': e.wcmodelcode,
            'wcvar': e.wcvar,
            'rimodelcode': e.rimodelcode,
            'rivar': e.rivar,
            'fimodelcode': e.fimodelcode,
            'fivar': e.fivar,
            'packmodelcode': e.packmodelcode,
            'packvar': e.packvar,
            'gascharge': float(e.gascharge) if e.gascharge is not None else 0.00,
            'updtime': e.updtime.strftime('%Y-%m-%d %H:%M:%S') if e.updtime else None,
            'compmod': e.compmod,
            'fan1mod': e.fan1mod,
            'fan2mod': e.fan2mod,
            'crspart1mod': e.crspart1mod,
            'crspart2mod': e.crspart2mod,
            'crspart3mod': e.crspart3mod,
            'crspart4mod': e.crspart4mod,
            'area': e.area,
            'serialstart': e.serialstart,
            'active_date': e.active_date.strftime('%Y-%m-%d') if e.active_date else None
        } for e in entries])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/api/conveyor/status/<line_code>', methods=['GET'])
@login_required
def get_conveyor_status(line_code):
    from app.models.linestat import LineStat
    try:
        stat = LineStat.query.filter_by(lineno=line_code).first()
        if not stat:
            return jsonify({'success': True, 'models': []})
        
        models = []
        if stat.packvar and stat.packvar > 0 and stat.packmodelcode:
            models.append({'model': stat.packmodelcode, 'station': 'PACK', 'qty': stat.packvar})
        if stat.fivar and stat.fivar > 0 and stat.fimodelcode:
            models.append({'model': stat.fimodelcode, 'station': 'FI', 'qty': stat.fivar})
        if stat.rivar and stat.rivar > 0 and stat.rimodelcode:
            models.append({'model': stat.rimodelcode, 'station': 'RI', 'qty': stat.rivar})
        if stat.wcvar and stat.wcvar > 0 and stat.wcmodelcode:
            models.append({'model': stat.wcmodelcode, 'station': 'WC', 'qty': stat.wcvar})
        if stat.outvar and stat.outvar > 0 and stat.outmodelcode:
            models.append({'model': stat.outmodelcode, 'station': 'SPAMSO', 'qty': stat.outvar})
        if stat.invar and stat.invar > 0 and stat.inmodelcode:
            models.append({'model': stat.inmodelcode, 'station': 'SPAMSI', 'qty': stat.invar})
        if stat.gmsvar and stat.gmsvar > 0 and stat.gmsmodelcode:
            models.append({'model': stat.gmsmodelcode, 'station': 'GMS', 'qty': stat.gmsvar})
        if stat.attvar and stat.attvar > 0 and stat.attmodelcode:
            models.append({'model': stat.attmodelcode, 'station': 'ATT', 'qty': stat.attvar})
        if stat.crsvar and stat.crsvar > 0 and stat.crsmodelcode:
            models.append({'model': stat.crsmodelcode, 'station': 'CRS', 'qty': stat.crsvar})
            
        return jsonify({'success': True, 'models': models})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/api/conveyor/action', methods=['POST'])
@login_required
@admin_required
def post_conveyor_action():
    try:
        data = request.get_json()
        line_code = data.get('line_code')
        action = data.get('action')
        
        if action == 'clear_all':
            from app.models.linestat import LineStat
            from app.models.worksched import WorkSched
            stat = LineStat.query.filter_by(lineno=line_code).first()
            if stat:
                stat.outvar = 0
                stat.invar = 0
                stat.gmsvar = 0
                stat.attvar = 0
                stat.crsvar = 0
                
            today_date = datetime.now().date()
            ghost_date = db.session.query(db.func.max(WorkSched.date)).filter(
                WorkSched.date < today_date,
                WorkSched.lineno == line_code
            ).scalar()
            
            if ghost_date:
                unfinished_scheds = WorkSched.query.filter(
                    WorkSched.lineno == line_code,
                    WorkSched.date == ghost_date,
                    WorkSched.act < WorkSched.plan
                ).all()
                for sched in unfinished_scheds:
                    sched.plan = sched.act
                    
            db.session.commit()
                
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ── SHIFTS API ───────────────────────────────────────────────────────────────

@admin_bp.route('/admin/api/shifts', methods=['GET', 'POST'])
@login_required
@admin_required
def api_shifts():
    if request.method == 'GET':
        try:
            shifts = Shift.query.order_by(Shift.start_time).all()
            return jsonify([s.to_dict() for s in shifts])
        except Exception as e:
            logging.error(f"Error fetching shifts: {e}")
            return jsonify({'error': str(e)}), 500

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or not data.get('name') or not data.get('start_time') or not data.get('end_time'):
                return jsonify({'success': False, 'error': 'Missing required fields'}), 400

            # Optional time formatting from string to time object if not handled natively
            try:
                start = datetime.strptime(data['start_time'], '%H:%M').time()
                end = datetime.strptime(data['end_time'], '%H:%M').time()
            except ValueError:
                start = datetime.strptime(data['start_time'], '%H:%M:%S').time()
                end = datetime.strptime(data['end_time'], '%H:%M:%S').time()

            new_shift = Shift(
                name=data['name'],
                start_time=start,
                end_time=end
            )
            db.session.add(new_shift)
            db.session.commit()
            return jsonify({'success': True, 'shift': new_shift.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/admin/api/shifts/<int:shift_id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def api_shift_detail(shift_id):
    shift = Shift.query.get_or_404(shift_id)

    if request.method == 'PUT':
        try:
            data = request.get_json()
            if 'name' in data:
                shift.name = data['name']
            if 'start_time' in data:
                try:
                    shift.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
                except ValueError:
                    shift.start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time()
            if 'end_time' in data:
                try:
                    shift.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
                except ValueError:
                    shift.end_time = datetime.strptime(data['end_time'], '%H:%M:%S').time()

            db.session.commit()
            return jsonify({'success': True, 'shift': shift.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    if request.method == 'DELETE':
        try:
            db.session.delete(shift)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

# ---------------------------------------------------------------------------
# SERIAL REFERENCE MANAGEMENT
# ---------------------------------------------------------------------------

from app.models.transfer_slip import TransferSlip
# ── FGCP: Transfer Slip Endpoints ─────────────────────────────────────────────

@admin_bp.route('/admin/api/transfer-slips/available-params', methods=['GET'])
@login_required
def get_transfer_slip_params():
    date_str = request.args.get('date', '').strip()
    if not date_str:
        return jsonify({'success': False, 'error': 'Missing date parameter'}), 400
        
    try:
        p_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400
        
    try:
        records = Packaging.query.filter(
            func.date(Packaging.time) == p_date
        ).all()
        
        lines = sorted(list(set(r.lineno for r in records if r.lineno)))
        models = sorted(list(set(r.modelcode for r in records if r.modelcode)))
        
        shifts_active = Shift.query.all()
        shift_names = set(s.name for s in shifts_active)
        
        ts_records = TransferSlip.query.with_entities(TransferSlip.shift).distinct().all()
        for ts in ts_records:
            if ts.shift:
                shift_names.add(ts.shift)
                
        shifts = sorted(list(shift_names))
        
        return jsonify({
            'success': True,
            'lines': lines,
            'models': models,
            'shifts': shifts
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/admin/api/transfer-slips', methods=['GET'])
@login_required
def get_transfer_slips():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
    
    date_filter = request.args.get('date', '').strip()
    line_filter = request.args.get('line', '').strip()
    ref_filter = request.args.get('ref', '').strip()
    
    query = TransferSlip.query
    
    if date_filter:
        try:
            parsed = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(func.date(TransferSlip.production_date) == parsed)
        except ValueError:
            pass
            
    if line_filter and line_filter.lower() != 'all':
        query = query.filter(TransferSlip.line == line_filter)
        
    if ref_filter:
        query = query.filter(TransferSlip.ref_number.ilike(f'%{ref_filter}%'))
        
    total = query.count()
    records = query.order_by(TransferSlip.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return jsonify({
        'success': True,
        'total': total,
        'page': page,
        'per_page': per_page,
        'records': [{
            'id': r.id,
            'ref_number': r.ref_number,
            'production_date': r.production_date.strftime('%Y-%m-%d'),
            'line': r.line,
            'shift': r.shift,
            'modelcode': r.modelcode,
            'total_qty': r.total_qty,
            'created_by': r.created_by
        } for r in records]
    })


@admin_bp.route('/admin/api/transfer-slips', methods=['POST'])
@login_required
def create_transfer_slip():
    data = request.get_json() or {}
    date_str = data.get('date')
    line = data.get('line')
    shift = data.get('shift')
    modelcode = data.get('modelcode')
    
    if not all([date_str, line, shift, modelcode]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
    try:
        p_date = datetime.strptime(str(date_str), '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    import json
    
    # Check already assigned serials for this date
    existing_slips = TransferSlip.query.filter(
        func.date(TransferSlip.production_date) == p_date
    ).all()
    
    assigned_serials = set()
    for slip in existing_slips:
        if slip.serials_json:
            try:
                sl_list = json.loads(slip.serials_json)
                assigned_serials.update(sl_list)
            except:
                pass

    # 1. Fetch serials from Packaging that passed
    pkg_records = Packaging.query.filter(
        func.date(Packaging.time) == p_date,
        Packaging.lineno == line,
        Packaging.modelcode == modelcode
    ).all()
    
    serials = [p.serial for p in pkg_records if p.status == 'GOOD' and p.serial not in assigned_serials]
    total_qty = len(serials)
    
    if total_qty == 0:
        return jsonify({'success': False, 'error': 'No completed units found for these parameters.'}), 404

    # 2. Generate Ref Number (Format: Line No. | Last 2 digit of year | Month | Series)
    # Series is 4-digit count of slips created in this month
    year2 = str(p_date.year)[-2:]
    month2 = f"{p_date.month:02d}"
    
    day_slips_count = TransferSlip.query.filter(
        func.date(TransferSlip.production_date) == p_date
    ).count()
    
    series4 = f"{day_slips_count + 1:04d}"
    ref_number = f"{line}{year2}{month2}{series4}"
    
    # 3. Create Slip
    import json
    new_slip = TransferSlip(
        ref_number=ref_number,
        production_date=p_date,
        line=line,
        shift=shift,
        modelcode=modelcode,
        total_qty=total_qty,
        created_by=session.get('user', 'System'),
        serials_json=json.dumps(serials)
    )
    
    db.session.add(new_slip)
    db.session.commit()
    
    return jsonify({'success': True, 'slip_id': new_slip.id, 'ref_number': new_slip.ref_number})


@admin_bp.route('/admin/print-transfer-slip/<int:slip_id>', methods=['GET'])
@login_required
def print_transfer_slip(slip_id):
    slip = TransferSlip.query.get_or_404(slip_id)
    import json
    serials = json.loads(slip.serials_json) if slip.serials_json else []
    
    # 5 serials per row, 22 rows per page = 110 serials per page
    rows = [serials[i:i+5] for i in range(0, len(serials), 5)]
    pages = [rows[i:i+22] for i in range(0, len(rows), 22)]
    total_pages = len(pages) if pages else 1
    
    print_date = datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    finished_date = slip.time.strftime('%m-%d-%Y') if slip.time else '--'
    start_time = '--:--:--'
    end_time = slip.time.strftime('%H:%M:%S') if slip.time else '--:--:--'

    return render_template(
        'admin/print_transfer_slip.html', 
        slip=slip, 
        pages=pages,
        total_pages=total_pages,
        print_date=print_date,
        finished_date=finished_date,
        start_time=start_time,
        end_time=end_time
    )

# ── FGCP: Print Reports & Tags Endpoints ──────────────────────────────────────

@admin_bp.route('/admin/api/qc-print-units', methods=['GET'])
@login_required
def get_qc_print_units():
    date_filter = request.args.get('date', '').strip()
    line_filter = request.args.get('line', '').strip()
    serial_filter = request.args.get('serial', '').strip()
    
    query = Packaging.query
    
    if date_filter:
        try:
            parsed = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(func.date(Packaging.time) == parsed)
        except ValueError:
            pass
            
    if line_filter and line_filter.lower() != 'all':
        query = query.filter(Packaging.lineno == line_filter)
        
    if serial_filter:
        query = query.filter(Packaging.serial.ilike(f'%{serial_filter}%'))
        
    records = query.order_by(Packaging.time.desc()).limit(100).all()
    
    return jsonify({
        'success': True,
        'records': [{
            'id': r.id,
            'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '',
            'modelcode': r.modelcode,
            'serial': r.serial,
            'line': r.lineno,
            'status': r.status
        } for r in records]
    })


@admin_bp.route('/admin/print-qc-report', methods=['GET'])
@login_required
def print_qc_report():
    serials_str = request.args.get('serials', '')
    if not serials_str:
        return "No serials provided", 400
        
    serial_list = [s.strip() for s in serials_str.split(',') if s.strip()]
    
    units_data = []
    
    # Import necessary models
    from app.models.crs import CRS
    from app.models.att import ATT
    from app.models.gms import GMS
    from app.models.spamsi import SPAMSI
    from app.models.spamso import SPAMSO
    from app.models.insp2 import INSP2
    from app.models.insp3_run import INSP3Run
    from app.models.insp4 import INSP4
    from app.models.packaging import Packaging
    
    for s in serial_list:
        crs = CRS.query.filter_by(serial=s).order_by(CRS.time.desc()).first()
        att = ATT.query.filter_by(serial=s).order_by(ATT.time.desc()).first()
        gms = GMS.query.filter_by(serial=s).order_by(GMS.time.desc()).first()
        spamsi = SPAMSI.query.filter_by(serial=s).order_by(SPAMSI.time.desc()).first()
        spamso = SPAMSO.query.filter_by(serial=s).order_by(SPAMSO.time.desc()).first()
        insp2 = INSP2.query.filter_by(serial=s).order_by(INSP2.time.desc()).first()
        insp3 = INSP3Run.query.filter_by(serial=s).order_by(INSP3Run.time.desc()).first()
        insp4 = INSP4.query.filter_by(serial=s).order_by(INSP4.time.desc()).first()
        pack = Packaging.query.filter_by(serial=s).order_by(Packaging.time.desc()).first()
        
        # Determine model
        model = ''
        if pack and pack.modelcode: model = pack.modelcode
        elif insp4 and insp4.modelcode: model = insp4.modelcode
        elif insp3 and insp3.modelcode: model = insp3.modelcode
        elif insp2 and insp2.modelcode: model = insp2.modelcode
        elif spamso and spamso.modelcode: model = spamso.modelcode
        elif spamsi and spamsi.modelcode: model = spamsi.modelcode
        elif gms and gms.modelcode: model = gms.modelcode
        elif crs and crs.modelcode: model = crs.modelcode
            
        units_data.append({
            'serial': s,
            'model': model,
            'crs_record': crs,
            'att_record': att,
            'gms_record': gms,
            'spamsi_record': spamsi,
            'spamso_record': spamso,
            'insp2_record': insp2,
            'insp3_record': insp3,
            'insp4_record': insp4,
            'pack_record': pack
        })
        
    return render_template('admin/qc_report_print.html', units_data=units_data, current_time=datetime.now())

