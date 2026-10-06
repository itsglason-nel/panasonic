"""Admin routes — Administrator module page and CRUD APIs."""
import logging
from flask import Blueprint, session, render_template, jsonify, request, redirect, url_for
from datetime import datetime
from functools import wraps
from flask_login import login_required, current_user, logout_user
from sqlalchemy import func
import re

def parse_serial_dates(serial_str):
    mfg_date = ""
    arv_date = ""
    if not serial_str:
        return [mfg_date, arv_date]
        
    potential_date = serial_str.split('|')[0].strip()
    
    # Try 16-char format: MM/DD/YYMM/DD/YY
    match_16 = re.match(r'^(\d{2}/\d{2}/\d{2})(\d{2}/\d{2}/\d{2})', potential_date)
    if match_16:
        try:
            mfg_dt = datetime.strptime(match_16.group(1), "%m/%d/%y")
            mfg_date = mfg_dt.strftime("%m/%d/%Y")
        except ValueError:
            mfg_date = match_16.group(1)
            
        try:
            arv_dt = datetime.strptime(match_16.group(2), "%m/%d/%y")
            arv_date = arv_dt.strftime("%m/%d/%Y")
        except ValueError:
            arv_date = match_16.group(2)
            
        return [mfg_date, arv_date]

    # Try 8-char format: YYYYMMDD
    if len(potential_date) >= 8 and potential_date[:8].isdigit():
        try:
            dt = datetime.strptime(potential_date[:8], "%Y%m%d")
            mfg_date = dt.strftime("%m/%d/%Y")
        except ValueError:
            pass
            
    return [mfg_date, arv_date]

from app.models import db
from app.models.worksched import WorkSched
from app.models.linestat import LineStat

from app.models.partref import PartRef
from app.models.crs import CRS
from app.models.gms import GMS
from app.models.att import ATT
from app.models.spamsi import SPAMSI
from app.models.pit import PIT
from app.models.spamso import SPAMSO
from app.models.wci import WCI
from app.models.rit import RIT
from app.models.fit import FIT

from app.models.line import Line
from app.models.module import Module
from app.models.shift import Shift
from app.models.tag import Tag
from app.models.area import Area
from app.models.modelref import ModelRef

from app.models.user import User


logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator: allow only admin and super_admin roles."""
    @wraps(f)
    def decorated(*args, **kwargs):
        role = getattr(current_user, 'role', None)
        role_str = str(role).strip().lower() if role else 'none'
        if '.' in role_str:
            role_str = role_str.split('.')[-1]
            
        is_admin_prop = getattr(current_user, 'is_admin', False)
        
        if not current_user.is_authenticated or (role_str not in ('admin', 'super_admin') and not is_admin_prop):
            logger.warning(
                'Unauthorized admin API access attempt by user "%s" (role: %s) on %s',
                getattr(current_user, 'username', 'anonymous'),
                role,
                request.path,
            )

            return jsonify({'error': 'Forbidden — admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/admin')
@login_required
def admin_page():
    if current_user.role not in ('admin', 'supervisor', 'operator'):
        return redirect(url_for('scoreboard.all_lines'))
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
    
    if parsed_date:
        from sqlalchemy import or_, and_
        query = query.filter(
            or_(
                WorkSched.date == parsed_date,
                and_(WorkSched.date < parsed_date, WorkSched.act < WorkSched.plan)
            )
        )

    schedules = query.order_by(WorkSched.date.asc(), WorkSched.lineno, WorkSched.seq).all()

    # Build set of valid modelcodes for has_bom flag
    valid_models = set(
        mc for (mc,) in db.session.query(PartRef.modelcode).distinct().all()
    )

    from app.models.linestat import LineStat
    linestat_dict = {ls.lineno: ls for ls in LineStat.query.all()}

    crs_counts = {}
    schedule_dates = list(set([s.date for s in schedules]))
    if schedule_dates:
        from app.models.crs import CRS
        from sqlalchemy import func
        crs_query = db.session.query(func.date(CRS.time), CRS.modelcode, CRS.lineno, func.count(CRS.id)).filter(
            func.date(CRS.time).in_(schedule_dates)
        )
        if lineno_str:
            crs_query = crs_query.filter(CRS.lineno == lineno_str)
            
        for crs_date_str, modelcode, lineno, count in crs_query.group_by(func.date(CRS.time), CRS.modelcode, CRS.lineno).all():
            crs_counts[(str(crs_date_str), modelcode, lineno)] = count

    schedules_data = []
    total_qty = 0
    has_ghosts = False
    ghost_lines = {}  # track which lines have ghost data and from which date
    for s in schedules:
        is_ghost = False
        if parsed_date and s.date < parsed_date and s.act < s.plan:
            is_ghost = True
            has_ghosts = True
            ghost_lines[s.lineno] = str(s.date.strftime('%m/%d/%Y'))
            
        if not is_ghost:
            total_qty += s.plan
            
        is_locked = False
        is_queued_at_crs = False
        ls = linestat_dict.get(s.lineno)
        if ls:
            is_on_belt = (
                ls.crsmodelcode == s.modelcode or 
                ls.attmodelcode == s.modelcode or 
                ls.gmsmodelcode == s.modelcode or 
                ls.inmodelcode == s.modelcode or 
                ls.outmodelcode == s.modelcode or
                ls.wcimodelcode == s.modelcode or
                ls.ritmodelcode == s.modelcode or
                ls.fitmodelcode == s.modelcode or
                ls.pitmodelcode == s.modelcode
            )
            if s.act > 0:
                is_locked = True
            elif is_on_belt:
                if ls.crsmodelcode == s.modelcode:
                    if ls.crsvar < s.plan:
                        is_locked = True
                else:
                    # If it's on the belt but NO LONGER at CRS, it has definitely fully passed CRS and is actively running
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
            'crs_qty': crs_counts.get((str(s.date), s.modelcode, s.lineno), 0),
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

    # ── Build wip_status for ghost resolution ────────────────────────────────
    # When a specific line is queried and has ghost rows, populate wip_status
    # so the frontend showWipModal() opens instead of showLineStatusModal().
    if has_ghosts and lineno_str and lineno_str in ghost_lines:
        ghost_date_str = ghost_lines[lineno_str]
        ls = linestat_dict.get(lineno_str)

        active_models = []
        unstarted = []

        # Identify which ghost schedules are active on the belt vs unstarted
        for s_data in schedules_data:
            if not s_data['is_ghost'] or s_data['line_code'] != lineno_str:
                continue
            ghost_model = s_data['model_number']
            model_on_belt = False
            if ls:
                station_map = [
                    ('CRS', ls.crsmodelcode, ls.crsvar),
                    ('ATT', ls.attmodelcode, ls.attvar),
                    ('GMS', ls.gmsmodelcode, ls.gmsvar),
                    ('SPAMSI', ls.inmodelcode, ls.invar),
                    ('SPAMSO', ls.outmodelcode, ls.outvar),
                    ('WCI', ls.wcimodelcode, ls.wcivar),
                    ('RIT', ls.ritmodelcode, ls.ritvar),
                    ('FIT', ls.fitmodelcode, ls.fitvar),
                    ('PIT', ls.pitmodelcode, ls.pitvar),
                ]
                for st_name, st_model, st_var in station_map:
                    if st_model == ghost_model and st_var and st_var > 0:
                        model_on_belt = True
                        active_models.append({
                            'model': ghost_model,
                            'station': st_name,
                            'var': st_var,
                            'plan': s_data['planned_qty'],
                            'act': s_data['actual_qty'],
                        })

            if not model_on_belt:
                unstarted.append({
                    'id': s_data['id'],
                    'model': ghost_model,
                    'plan': s_data['planned_qty'] - s_data['actual_qty'],
                })

        wip_status = {
            'active_date': ghost_date_str,
            'active_models': active_models,
            'unstarted': unstarted,
        }

    # When viewing 'all' lines and multiple lines have ghosts, signal aggregate mode
    elif has_ghosts and line_id == 'all' and len(ghost_lines) > 0:
        lines_with_wip = [{'line': ln, 'date': dt} for ln, dt in ghost_lines.items()]
        wip_status = {
            'active_date': 'multiple',
            'lines_with_wip': lines_with_wip,
        }

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
    
    # Find the most recent date before today that has unfinished schedules
    ghost_date = db.session.query(db.func.max(WorkSched.date)).filter(
        WorkSched.date < today_date,
        WorkSched.lineno == lineno,
        WorkSched.act < WorkSched.plan
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
        
    if action in ['clear', 'continue']:
        linestat = LineStat.query.filter_by(lineno=lineno).first()
        active_model_codes = set()
        
        if linestat:
            if linestat.crsvar and linestat.crsvar > 0 and linestat.crsmodelcode:
                active_model_codes.add(linestat.crsmodelcode.strip())
            if linestat.attvar and linestat.attvar > 0 and linestat.attmodelcode:
                active_model_codes.add(linestat.attmodelcode.strip())
            if linestat.gmsvar and linestat.gmsvar > 0 and linestat.gmsmodelcode:
                active_model_codes.add(linestat.gmsmodelcode.strip())
            if linestat.invar and linestat.invar > 0 and linestat.inmodelcode:
                active_model_codes.add(linestat.inmodelcode.strip())
            if linestat.outvar and linestat.outvar > 0 and linestat.outmodelcode:
                active_model_codes.add(linestat.outmodelcode.strip())
            if linestat.wcivar and linestat.wcivar > 0 and linestat.wcimodelcode:
                active_model_codes.add(linestat.wcimodelcode.strip())
            if linestat.ritvar and linestat.ritvar > 0 and linestat.ritmodelcode:
                active_model_codes.add(linestat.ritmodelcode.strip())
            if linestat.fitvar and linestat.fitvar > 0 and linestat.fitmodelcode:
                active_model_codes.add(linestat.fitmodelcode.strip())
            if linestat.pitvar and linestat.pitvar > 0 and linestat.pitmodelcode:
                active_model_codes.add(linestat.pitmodelcode.strip())
                
        # Get next sequence number for today
        last_sched = WorkSched.query.filter_by(lineno=lineno, date=today_date).order_by(WorkSched.seq.desc()).first()
        next_seq = 0 if not last_sched else last_sched.seq + 1

        for sched in unfinished_scheds:
            s_model = sched.modelcode.strip() if sched.modelcode else ''
            if s_model not in active_model_codes:
                # Unstarted schedule
                if str(sched.id) in unstarted_plans:
                    # User checked it -> create new schedule for today
                    
                    new_plan_val = sched.plan
                    try:
                        if unstarted_plans[str(sched.id)]:
                            new_plan_val = int(unstarted_plans[str(sched.id)])
                    except ValueError:
                        pass
                    
                    # Fix 4: Check for existing today-schedule to avoid UniqueConstraint crash
                    existing = WorkSched.query.filter_by(lineno=lineno, date=today_date, modelcode=sched.modelcode).first()
                    if existing:
                        existing.plan += new_plan_val
                    else:
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
                if action == 'clear':
                    # Discard & Clear
                    sched.plan = sched.act
                elif action == 'continue':
                    max_var = 0
                    if linestat.crsmodelcode and linestat.crsmodelcode.strip() == s_model and linestat.crsvar:
                        max_var = max(max_var, linestat.crsvar)
                    if linestat.attmodelcode and linestat.attmodelcode.strip() == s_model and linestat.attvar:
                        max_var = max(max_var, linestat.attvar)
                    if linestat.gmsmodelcode and linestat.gmsmodelcode.strip() == s_model and linestat.gmsvar:
                        max_var = max(max_var, linestat.gmsvar)
                    if linestat.inmodelcode and linestat.inmodelcode.strip() == s_model and linestat.invar:
                        max_var = max(max_var, linestat.invar)
                    if linestat.outmodelcode and linestat.outmodelcode.strip() == s_model and linestat.outvar:
                        max_var = max(max_var, linestat.outvar)
                        
                    final_plan = max_var
                    
                    # If they updated the plan for the CRS model, check if it's higher
                    if linestat.crsmodelcode and linestat.crsmodelcode.strip() == s_model and crs_new_plan:
                        try:
                            crs_plan_val = int(crs_new_plan)
                            if crs_plan_val > final_plan:
                                final_plan = crs_plan_val
                        except ValueError:
                            pass
                    
                    if final_plan > 0:
                        # Fix 4: Check for existing today-schedule to avoid UniqueConstraint crash
                        existing = WorkSched.query.filter_by(lineno=lineno, date=today_date, modelcode=sched.modelcode).first()
                        if existing:
                            existing.plan += final_plan
                        else:
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

        if action == 'clear':
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
                linestat.inunique = None
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
                linestat.gmstolpos = 0
                linestat.gmstolneg = 0
                linestat.outmodel = None
                linestat.wcimodelcode = None
                linestat.wcivar = 0
                linestat.ritmodelcode = None
                linestat.ritvar = 0
                linestat.ritprogh = None
                linestat.ritprogf = None
                linestat.ritdata1 = None
                linestat.ritdata1tolpos = None
                linestat.ritdata1tolneg = None
                linestat.ritdata2 = None
                linestat.ritdata2tolpos = None
                linestat.ritdata2tolneg = None
                linestat.ritdata3 = None
                linestat.ritdata3tolpos = None
                linestat.ritdata3tolneg = None
                linestat.ritheat1 = None
                linestat.ritheat2 = None
                linestat.fitmodelcode = None
                linestat.fitvar = 0
                linestat.fitdata1 = None
                linestat.fitdata1tolpos = None
                linestat.fitdata1tolneg = None
                linestat.fitdata2 = None
                linestat.fitdata2tolpos = None
                linestat.fitdata2tolneg = None
                linestat.pitmodelcode = None
                linestat.pitvar = 0
                linestat.pittws = None
                linestat.updtime = datetime.now()
        elif action == 'continue':
            # Fix 3: Transition linestat.active_date to today so the SP's sequence
            # lookup finds today's newly created schedules instead of yesterday's.
            if linestat:
                from datetime import datetime
                linestat.active_date = today_date
                linestat.updtime = datetime.now()
        db.session.commit()
        
        # If the belt has no active models (all were unstarted ghost schedules),
        # initialize linestat from the new today-schedules at seq 0.
        # Otherwise, bump updtime so the PLC knows new queued work exists.
        try:
            if linestat and not active_model_codes:
                from app.services.linestat_monitor import initialize_line
                initialize_line(lineno)
            else:
                from app.services.linestat_monitor import force_restart_for_manual_edit
                force_restart_for_manual_edit()
        except Exception as _fr_err:
            logger.warning('linestat update failed after wip_resolve continue: %s', _fr_err)

        return jsonify({'success': True})
        
    return jsonify({'success': False, 'error': 'Invalid action'})

@admin_bp.route('/admin/api/next-sequence', methods=['GET'])
@login_required
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
    force = data.get('force', False)
    if not force:
        duplicate = WorkSched.query.filter_by(
            lineno=lineno,
            date=parsed_date,
            modelcode=modelcode
        ).first()
        if duplicate:
            return jsonify({
                'success': False,
                'error': 'duplicate',
                'requires_confirmation': True,
                'message': f'Model "{modelcode}" is already on the schedule for this day. Are you sure you want to add another sequence?'
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

    # Seed linestat only if the line is currently idle (No Work).
    # Lines that already have an active or WIP model are left untouched;
    # the new schedule sits in the worksched queue and the SP advances to it
    # automatically as each station completes its current model.
    try:
        from app.services.linestat_monitor import initialize_line
        ls = LineStat.query.filter_by(lineno=lineno).first()
        if not ls or ls.status == 'No Work':
            initialize_line(lineno)
    except Exception as _init_err:
        logger.warning('initialize_line failed after add_schedule: %s', _init_err)

    return jsonify({'success': True, 'id': new_sched.id})

@admin_bp.route('/admin/api/schedule/<int:sid>', methods=['PUT', 'DELETE'])
@login_required
def edit_delete_schedule(sid):
    sched = db.get_or_404(WorkSched, sid)
    
    linestat = LineStat.query.filter_by(lineno=sched.lineno).first()
    is_on_belt = False
    is_active_sched = False
    
    if linestat:
        station_models = [
            linestat.crsmodelcode, linestat.attmodelcode, linestat.gmsmodelcode,
            linestat.inmodelcode, linestat.outmodelcode, linestat.wcimodelcode,
            linestat.ritmodelcode, linestat.fitmodelcode, linestat.pitmodelcode
        ]
        if sched.modelcode in station_models:
            is_on_belt = True
            prev_incomplete = WorkSched.query.filter_by(lineno=sched.lineno, date=sched.date, modelcode=sched.modelcode).filter(WorkSched.seq < sched.seq, WorkSched.act < WorkSched.plan).first()
            if not prev_incomplete:
                is_active_sched = True

    is_locked = False
    if sched.act > 0:
        is_locked = True
    elif is_active_sched:
        if linestat.crsmodelcode == sched.modelcode:
            if linestat.crsvar < sched.plan:
                is_locked = True
        else:
            is_locked = True
            
    is_queued_at_crs = is_active_sched and not is_locked

    if request.method == 'DELETE':
        if is_locked:
            return jsonify({'success': False, 'error': 'Cannot delete: This schedule is actively running on the conveyor belt or has already produced units.'})
            
        if is_queued_at_crs:
            if linestat.crsmodelcode == sched.modelcode:
                linestat.crsmodelcode = None
                linestat.crsvar = 0
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
            if linestat.attmodelcode == sched.modelcode:
                linestat.attmodelcode = None
                linestat.attvar = 0
            if linestat.gmsmodelcode == sched.modelcode:
                linestat.gmsmodelcode = None
                linestat.gmsvar = 0
                linestat.gascharge = 0
                linestat.gmstolpos = 0
                linestat.gmstolneg = 0
            if linestat.inmodelcode == sched.modelcode:
                linestat.inmodelcode = None
                linestat.invar = 0
                linestat.inunique = None
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
            if linestat.outmodelcode == sched.modelcode:
                linestat.outmodelcode = None
                linestat.outvar = 0
                linestat.outmodel = None
                linestat.outpart1mod = None
                linestat.outpart1desc = None
                linestat.outpart2mod = None
                linestat.outpart2desc = None
                linestat.outpart3mod = None
                linestat.outpart3desc = None
            if linestat.wcimodelcode == sched.modelcode:
                linestat.wcimodelcode = None
                linestat.wcivar = 0
            if linestat.ritmodelcode == sched.modelcode:
                linestat.ritmodelcode = None
                linestat.ritvar = 0
                linestat.ritprogh = None
                linestat.ritprogf = None
                linestat.ritdata1 = None
                linestat.ritdata1tolpos = None
                linestat.ritdata1tolneg = None
                linestat.ritdata2 = None
                linestat.ritdata2tolpos = None
                linestat.ritdata2tolneg = None
                linestat.ritdata3 = None
                linestat.ritdata3tolpos = None
                linestat.ritdata3tolneg = None
                linestat.ritheat1 = None
                linestat.ritheat2 = None
            if linestat.fitmodelcode == sched.modelcode:
                linestat.fitmodelcode = None
                linestat.fitvar = 0
                linestat.fitdata1 = None
                linestat.fitdata1tolpos = None
                linestat.fitdata1tolneg = None
                linestat.fitdata2 = None
                linestat.fitdata2tolpos = None
                linestat.fitdata2tolneg = None
            if linestat.pitmodelcode == sched.modelcode:
                linestat.pitmodelcode = None
                linestat.pitvar = 0
                linestat.pittws = None

            # Evaluate if line is now completely empty
            if linestat.status == 'Work' and not any([
                linestat.crsmodelcode, linestat.attmodelcode, linestat.gmsmodelcode, 
                linestat.inmodelcode, linestat.outmodelcode, linestat.wcimodelcode, 
                linestat.ritmodelcode, linestat.fitmodelcode, linestat.pitmodelcode
            ]):
                linestat.status = 'No Work'
                linestat.active_date = None
                
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
        if is_active_sched or sched.act > 0:
            return jsonify({'success': False, 'error': 'Cannot change the Model Code while it is on the conveyor belt or has produced units.'})
        sched.modelcode = data['model_number']
        
    if 'planned_qty' in data:
        try:
            from sqlalchemy import text
            new_plan = int(data['planned_qty'])
            diff = new_plan - sched.plan
            
            if diff != 0:
                # ── Hard floor: count units that have physically entered the line ──
                # sched.act only reflects PIT-completed units. CRS is the entry
                # point, so any unit scanned there is already "in the pipeline".
                from sqlalchemy import text as sa_text
                crs_count = db.session.query(func.count(CRS.id)).filter(
                    CRS.modelcode == sched.modelcode,
                    CRS.lineno == sched.lineno,
                    func.date(CRS.time) == sched.date
                ).scalar() or 0
                floor = max(sched.act, crs_count)
                if diff < 0 and new_plan < floor:
                    return jsonify({'success': False, 'error': f'Cannot decrease plan below {floor} — {crs_count} unit(s) already scanned at CRS ({sched.act} completed at PIT).'})
                
                stations_to_awaken = []
                
                if linestat and is_active_sched:
                    stations = [
                        ('crs', 'crsmodelcode', 'crsvar'),
                        ('att', 'attmodelcode', 'attvar'),
                        ('gms', 'gmsmodelcode', 'gmsvar'),
                        ('in', 'inmodelcode', 'invar'),
                        ('out', 'outmodelcode', 'outvar'),
                        ('wci', 'wcimodelcode', 'wcivar'),
                        ('rit', 'ritmodelcode', 'ritvar'),
                        ('fit', 'fitmodelcode', 'fitvar'),
                        ('pit', 'pitmodelcode', 'pitvar')
                    ]
                    for st_prefix, code_attr, var_attr in stations:
                        current_code = getattr(linestat, code_attr)
                        current_var = getattr(linestat, var_attr)
                        
                        if current_code == sched.modelcode:
                            new_var = current_var + diff
                            if new_var < 0:
                                return jsonify({'success': False, 'error': f'Cannot decrease plan: {st_prefix.upper()} has already processed those units.'})
                            setattr(linestat, var_attr, new_var)
                        elif current_code is None and diff > 0:
                            stations_to_awaken.append((st_prefix, var_attr))
                        elif current_code != sched.modelcode and diff < 0:
                            if current_code is not None:
                                current_st_sched = WorkSched.query.filter_by(lineno=sched.lineno, date=sched.date, modelcode=current_code).order_by(WorkSched.seq.desc()).first()
                                if current_st_sched and current_st_sched.seq > sched.seq:
                                    return jsonify({'success': False, 'error': f'Cannot decrease plan: {st_prefix.upper()} has already moved past this schedule.'})

                sched.plan = new_plan
                db.session.commit()
                
                if linestat:
                    if linestat.status == 'No Work' and diff > 0:
                        from app.services.linestat_monitor import initialize_line
                        try:
                            initialize_line(sched.lineno)
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).error(f"Failed to initialize line on edit: {e}")
                    elif stations_to_awaken:
                        for st_prefix, var_attr in stations_to_awaken:
                            try:
                                db.session.execute(
                                    text(f"CALL sp_linestat_shift_sequence('{st_prefix}', :lineno, NULL)"),
                                    {'lineno': sched.lineno}
                                )
                                db.session.commit()
                                db.session.refresh(linestat)
                                if getattr(linestat, f"{st_prefix}modelcode") == sched.modelcode:
                                    setattr(linestat, var_attr, diff)
                                    db.session.commit()
                            except Exception as e:
                                import logging
                                logging.getLogger(__name__).error(f"Failed to awaken {st_prefix} on edit: {e}")
        except ValueError:
            pass
            
    if 'takt_time' in data:
        sched.takttime = data['takt_time']
        
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/admin/api/module-schedules', methods=['GET', 'PUT', 'DELETE'])
@login_required
def module_schedules():
    if request.method == 'GET':
        return jsonify({'module_schedules': []})
    return jsonify({'success': True})

def is_model_active_on_schedule(modelcode):
    from app.models.worksched import WorkSched
    return WorkSched.query.filter_by(modelcode=modelcode, finalized=False).first() is not None

@admin_bp.route('/admin/api/models', methods=['GET'])
@login_required
def get_models():
    models = db.session.query(PartRef.modelcode).distinct().order_by(PartRef.modelcode).all()
    
    from app.models.worksched import WorkSched
    active_models = db.session.query(WorkSched.modelcode).filter_by(finalized=False).distinct().all()
    active_set = {mcode for (mcode,) in active_models}
    
    return jsonify([{
        'id': mcode,
        'model_number': mcode,
        'is_on_schedule': mcode in active_set
    } for (mcode,) in models])

@admin_bp.route('/admin/api/model', methods=['POST'])
@login_required
def add_model():
    return jsonify({
        'success': False,
        'error': 'Manual model creation is not supported. Import models via the BOM Excel import feature.'
    }), 501

@admin_bp.route('/admin/api/model/<modelcode>', methods=['DELETE'])
@login_required
def delete_model(modelcode):
    """Delete all BOM rows and modelref for the given model code."""
    if is_model_active_on_schedule(modelcode):
        return jsonify({'success': False, 'error': 'Cannot delete: Model is currently active on the work schedule.'}), 400

    deleted = PartRef.query.filter_by(modelcode=modelcode).delete()
    from app.models.modelref import ModelRef
    ModelRef.query.filter_by(modelcode=modelcode).delete()
    # Outdoor Control Board partref row is already deleted by the PartRef.query above
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
    return jsonify({'found': True, 'data': data})

@admin_bp.route('/admin/api/modelref', methods=['GET'])
@login_required
def get_all_modelrefs():
    from app.models.modelref import ModelRef
    refs = ModelRef.query.all()
    entries = []
    for ref in refs:
        entries.append(ref.to_dict())
    return jsonify({'entries': entries})

@admin_bp.route('/admin/api/modelref/<modelcode>', methods=['PUT'])
@login_required
def update_modelref(modelcode):
    if is_model_active_on_schedule(modelcode):
        return jsonify({'success': False, 'error': 'Cannot edit: Model is currently active on the work schedule.'}), 400

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
            assigned = ModelRef.query.filter_by(spamsi_unique=unique_code).first()
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
                  'in_power_base', 'in_power_tolpos', 'in_power_tolneg', 'temp_diff_base', 'temp_diff_tolpos', 'temp_diff_tolneg',
                  'ritheat1', 'ritheat2', 'pittws']:
        if field in data:
            val = data[field]
            if field in ['program_h', 'program_f']:
                if val == '':
                    val = None
                elif val is not None and not re.match(r'^\d{2}:\d{2}$', str(val)):
                    return jsonify({'success': False, 'error': f'Invalid format for {field}. Must be NN:NN.'}), 400
            elif field in ['ritheat1', 'ritheat2', 'pittws']:
                val = 'ON' if val == 'ON' else None
            elif val == '' and field not in ['area', 'serialstart']:
                val = 0
            setattr(ref, field, val)

    if 'spamsi_unique_code' in data:
        ref.spamsi_unique = unique_code or None
    
    if 'spamso_outmodel' in data:
        spamso_outmodel_val = str(data['spamso_outmodel'] or '').strip() or None
        outmodel_ref = PartRef.query.filter_by(
            modelcode=modelcode, module='SPAMSO', tag='Outdoor Control Board'
        ).first()
        if spamso_outmodel_val:
            if outmodel_ref:
                outmodel_ref.partno = spamso_outmodel_val
            else:
                db.session.add(PartRef(
                    modelcode=modelcode,
                    module='SPAMSO',
                    partno=spamso_outmodel_val,
                    partdesc='Outdoor Control Board',
                    usage=1,
                    tag='Outdoor Control Board',
                ))
        elif outmodel_ref:
            db.session.delete(outmodel_ref)
            
    if 'gascharge_base' in data:
        base_val = data['gascharge_base']
        if base_val == '':
            base_val = 0
        gms_ref = PartRef.query.filter_by(modelcode=modelcode, module='GMS').first()
        if gms_ref:
            gms_ref.usage = float(base_val)
    
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/admin/api/model-gas-target/<modelcode>', methods=['GET'])
@login_required
def get_model_gas_target(modelcode):
    from app.models.partref import PartRef
    gms_ref = PartRef.query.filter_by(modelcode=modelcode, module='GMS').first()
    target = float(gms_ref.usage) if gms_ref and gms_ref.usage is not None else 0.00
    return jsonify({'target_charge': target})

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
def add_bom():
    data = request.get_json()
    modelcode = data.get('modelcode', '')
    
    if is_model_active_on_schedule(modelcode):
        return jsonify({'success': False, 'message': 'Cannot add parts: Model is currently active on the work schedule.'})

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
def edit_delete_bom(bid):
    part = db.get_or_404(PartRef, bid)
    
    if is_model_active_on_schedule(part.modelcode):
        action = 'delete' if request.method == 'DELETE' else 'edit'
        return jsonify({'success': False, 'error': f'Cannot {action} part: Model is currently active on the work schedule.'}), 400

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
            'lineno':     r.lineno or '',
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
            'part4mod':   r.part4mod or '—',
            'part4desc':  r.part4desc or '—',
            'part4serial': r.part4serial or '—',
            'comp_det':    parse_serial_dates(r.compserial),
            'fan1_det':    parse_serial_dates(r.fan1serial),
            'fan2_det':    parse_serial_dates(r.fan2serial),
            'part1_det':   parse_serial_dates(r.part1serial),
            'part2_det':   parse_serial_dates(r.part2serial),
            'part3_det':   parse_serial_dates(r.part3serial),
            'part4_det':   parse_serial_dates(r.part4serial),
            'inspector':  r.inspector or '—',
        } for r in records],
    })

def _trigger_pdf_bg(serial):
    if not serial: return
    import threading
    from flask import current_app
    from app.services.pdf_generator import generate_tag_pdf
    app = getattr(current_app, '_get_current_object')()
    def _gen():
        with app.app_context():
            generate_tag_pdf(serial, port=8080)
    threading.Thread(target=_gen, daemon=True).start()

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
    _trigger_pdf_bg(record.serial)
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
            'lineno':    r.lineno or '',
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
    _trigger_pdf_bg(record.serial)
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
            'overallstatus': r.overallstatus or r.status,
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
    _trigger_pdf_bg(record.serial)
    return jsonify({'success': True})



# ── Print Production Tag ──────────────────────────────────────────────────────

@admin_bp.route('/admin/print-tag/<serial>', methods=['GET'])
@login_required
def print_tag(serial):
    """Render the Production Information Tag for a specific serial number."""
    unit_data = _get_tag_data(serial)
    return render_template('admin/print_tag.html', unit=unit_data)

@admin_bp.route('/internal/print-tag/<serial>', methods=['GET'])
def internal_print_tag(serial):
    """Internal route for headless PDF generation without login requirement."""
    if request.remote_addr != '127.0.0.1':
        from flask import abort
        abort(403)
    unit_data = _get_tag_data(serial)
    return render_template('admin/print_tag.html', unit=unit_data)

@admin_bp.route('/admin/api/trigger-pdf/<serial>', methods=['POST'])
@login_required
def trigger_pdf(serial):
    """Trigger the automated generation of the Production Information Tag PDF for a unit.
    This can be called when a unit finishes PIT or from the UI."""
    from app.services.pdf_generator import generate_tag_pdf
    from flask import request
    # Extract port from the request host to ensure we hit the right local server instance
    try:
        port = int(request.host.split(':')[1]) if ':' in request.host else 80
    except ValueError:
        port = 8080
    
    success = generate_tag_pdf(serial, port=port)
    if success:
        return jsonify({'success': True, 'message': f'PDF generated successfully for {serial}.'})
    else:
        return jsonify({'success': False, 'error': 'Failed to generate PDF. Check logs.'}), 500

def _get_tag_data(serial):
    """Gather data from CRS, GMS, ATT, WCI for a specific serial number."""
    # Gather data from CRS, GMS, ATT, WCI
    crs_record = CRS.query.filter_by(serial=serial).order_by(CRS.id.desc()).first()
    gms_record = GMS.query.filter_by(serial=serial).order_by(GMS.id.desc()).first()
    att_record = ATT.query.filter_by(serial=serial).order_by(ATT.id.desc()).first()
    
    from app.models.wci import WCI
    from app.models.rit import RIT
    from app.models.fit import FIT
    from app.models.pit import PIT
    
    wci_record = WCI.query.filter_by(serial=serial).order_by(WCI.id.desc()).first()
    rit_record = RIT.query.filter_by(serial=serial).order_by(RIT.id.desc()).first()
    fit_record = FIT.query.filter_by(serial=serial).order_by(FIT.id.desc()).first()
    pit_record = PIT.query.filter_by(serial=serial).order_by(PIT.id.desc()).first()
    
    # Determine the time to calculate shift (Day/Night) and Date
    production_time = crs_record.time if crs_record else datetime.now()
    
    from app.models.shift import Shift
    db_shifts = Shift.query.all()
    
    prod_time = production_time.time()
    shift = None
    
    for s in db_shifts:
        if s.is_overnight:
            # Shift crosses midnight (e.g., 22:00 to 06:00)
            if prod_time >= s.start_time or prod_time <= s.end_time:
                shift = s.name.upper()
                break
        else:
            # Shift within the same day (e.g., 06:00 to 14:00)
            if s.start_time <= prod_time <= s.end_time:
                shift = s.name.upper()
                break
                
    # Fallback to hardcoded logic if database fails to match
    if not shift:
        shift = 'NIGHT' if (production_time.hour >= 18 or production_time.hour < 6) else 'DAY'
        
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
        
        'wci_status': wci_record.overallstatus if wci_record else '',
        'wci_inspector': wci_record.inspector if wci_record else '',
        'wci_status1': wci_record.status1 if wci_record else '',
        'wci_status2': wci_record.status2 if wci_record else '',
        'wci_status3': wci_record.status3 if wci_record else '',
        'wci_status4': wci_record.status4 if wci_record else '',
        'wci_status5': wci_record.status5 if wci_record else '',
        'wci_status6': wci_record.status6 if wci_record else '',
        'wci_status7': wci_record.status7 if wci_record else '',
        'insp2_no_lacking': '',  # wci has no test_no_lacking after insp2→wci schema rename; key kept for template forward-compat
        
        'rit_status': rit_record.overallstatus if rit_record else '',
        'rit_inspector': rit_record.inspector if rit_record else '',
        'rit_status1': rit_record.status1 if rit_record else '',
        'rit_status2': rit_record.status2 if rit_record else '',
        'rit_status3': rit_record.status3 if rit_record else '',
        'rit_status4': rit_record.status4 if rit_record else '',
        'rit_status5': rit_record.status5 if rit_record else '',
        'rit_status6': rit_record.status6 if rit_record else '',
        'rit_status7': rit_record.status7 if rit_record else '',
        'rit_status8': rit_record.status8 if rit_record else '',
        'rit_status9': rit_record.status9 if rit_record else '',
        'rit_status10': rit_record.status10 if rit_record else '',
        'rit_data1': rit_record.data1 if rit_record else '',
        'rit_data2': rit_record.data2 if rit_record else '',
        'rit_data3': rit_record.data3 if rit_record else '',
        'rit_progh': rit_record.progh if rit_record else '',
        'rit_progf': rit_record.progf if rit_record else '',
        
        'fit_status': fit_record.overallstatus if fit_record else '',
        'fit_inspector': fit_record.inspector if fit_record else '',
        'fit_status1': fit_record.status1 if fit_record else '',
        'fit_status2': fit_record.status2 if fit_record else '',
        'fit_status3': fit_record.status3 if fit_record else '',
        'fit_status4': fit_record.status4 if fit_record else '',
        'fit_status5': fit_record.status5 if fit_record else '',
        'fit_status6': fit_record.status6 if fit_record else '',
        'fit_status7': fit_record.status7 if fit_record else '',
        'fit_status8': fit_record.status8 if fit_record else '',
        'fit_status9': fit_record.status9 if fit_record else '',
        'fit_status10': fit_record.status10 if fit_record else '',
        'fit_data1': float(fit_record.data1) if fit_record and fit_record.data1 is not None else '',
        'fit_data2': float(fit_record.data2) if fit_record and fit_record.data2 is not None else '',
        'insp4_nameplate': '',      # insp4→fit schema rename replaced these named cols with status1–status10
        'insp4_label': '',
        'insp4_manual_remote': '',
        'insp4_manual_warranty': '',
        'insp4_manual_screws': '',
        'insp4_grille_eel': '',
        'insp4_grille_model': '',
        'insp4_grille_logo': '',
        
        'pit_status1': pit_record.status1 if pit_record else '',
        'pit_status2': pit_record.status2 if pit_record else '',
        'pit_status3': pit_record.status3 if pit_record else '',
        'pit_status4': pit_record.status4 if pit_record else '',
        'pit_inspector': pit_record.inspector if pit_record else '',
    }
    return unit_data

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
            'inserial_det': parse_serial_dates(r.inserial),
            'part1mod': r.part1mod, 'part1desc': r.part1desc, 'part1serial': r.part1serial, 'part1_det': parse_serial_dates(r.part1serial),
            'part2mod': r.part2mod, 'part2desc': r.part2desc, 'part2serial': r.part2serial, 'part2_det': parse_serial_dates(r.part2serial),
            'part3mod': r.part3mod, 'part3desc': r.part3desc, 'part3serial': r.part3serial, 'part3_det': parse_serial_dates(r.part3serial),
            'part4mod': r.part4mod, 'part4desc': r.part4desc, 'part4serial': r.part4serial, 'part4_det': parse_serial_dates(r.part4serial),
            'part5mod': r.part5mod, 'part5desc': r.part5desc, 'part5serial': r.part5serial, 'part5_det': parse_serial_dates(r.part5serial),
            'part6mod': r.part6mod, 'part6desc': r.part6desc, 'part6serial': r.part6serial, 'part6_det': parse_serial_dates(r.part6serial),
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
            'outserial_det': parse_serial_dates(r.outserial),
            'part1mod': r.part1mod, 'part1desc': r.part1desc, 'part1serial': r.part1serial, 'part1_det': parse_serial_dates(r.part1serial),
            'part2mod': r.part2mod, 'part2desc': r.part2desc, 'part2serial': r.part2serial, 'part2_det': parse_serial_dates(r.part2serial),
            'part3mod': r.part3mod, 'part3desc': r.part3desc, 'part3serial': r.part3serial, 'part3_det': parse_serial_dates(r.part3serial),
            'lineno': r.lineno
        } for r in records]
    })



@admin_bp.route('/admin/api/wci-data', methods=['GET'])
@login_required
def get_wci_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
    total, records = _get_paginated_data(
        WCI, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'lineno': r.lineno or '—', 'time': r.time.strftime('%Y-%m-%d %H:%M:%S'), 'modelcode': r.modelcode, 'serial': r.serial, 'overallstatus': r.overallstatus, 'inspector': r.inspector or '—', 'status1': r.status1 or '', 'status2': r.status2 or '', 'status3': r.status3 or '', 'status4': r.status4 or '', 'status5': r.status5 or '', 'status6': r.status6 or '', 'status7': r.status7 or '', 'remarks': 'Past NG History' if ng.get(r.serial) else 'No remarks'} for r in records]
    })

@admin_bp.route('/admin/api/rit-data', methods=['GET'])
@login_required
def get_rit_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
    total, records = _get_paginated_data(
        RIT, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '', 'modelcode': r.modelcode, 'serial': r.serial, 'overallstatus': r.overallstatus, 'inspector': r.inspector or '—', 'status1': r.status1 or '', 'status2': r.status2 or '', 'status3': r.status3 or '', 'status4': r.status4 or '', 'status5': r.status5 or '', 'status6': r.status6 or '', 'status7': r.status7 or '', 'status8': r.status8 or '', 'status9': r.status9 or '', 'status10': r.status10 or '', 'data1': str(r.data1) if r.data1 is not None else '', 'data2': str(r.data2) if r.data2 is not None else '', 'data3': str(r.data3) if r.data3 is not None else '', 'progh': r.progh or '', 'progf': r.progf or '', 'lineno': r.lineno or ''} for r in records]
    })




@admin_bp.route('/admin/api/pit-data', methods=['GET'])
def get_pit_data():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    sort_by = request.args.get('sort_by', 'time')
    sort_dir = request.args.get('sort_dir', 'desc')
    date_filter = request.args.get('date', '')
    serial_filter = request.args.get('serial', '')

    query = PIT.query

    if date_filter:
        try:
            target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(db.func.date(PIT.time) == target_date)
        except ValueError:
            pass
    if serial_filter:
        query = query.filter(PIT.serial.ilike(f'%{serial_filter}%'))

    if sort_by == 'time':
        order_col = PIT.time.desc() if sort_dir == 'desc' else PIT.time.asc()
    elif sort_by == 'modelcode':
        order_col = PIT.modelcode.desc() if sort_dir == 'desc' else PIT.modelcode.asc()
    elif sort_by == 'serial':
        order_col = PIT.serial.desc() if sort_dir == 'desc' else PIT.serial.asc()
    elif sort_by == 'status':
        order_col = PIT.status1.desc() if sort_dir == 'desc' else PIT.status1.asc()
    elif sort_by == 'status2':
        order_col = PIT.status2.desc() if sort_dir == 'desc' else PIT.status2.asc()
    elif sort_by == 'status3':
        order_col = PIT.status3.desc() if sort_dir == 'desc' else PIT.status3.asc()
    elif sort_by == 'status4':
        order_col = PIT.status4.desc() if sort_dir == 'desc' else PIT.status4.asc()
    elif sort_by == 'inspector':
        order_col = PIT.inspector.desc() if sort_dir == 'desc' else PIT.inspector.asc()
    elif sort_by == 'overallstatus':
        order_col = PIT.overallstatus.desc() if sort_dir == 'desc' else PIT.overallstatus.asc()
    elif sort_by == 'id':
        order_col = PIT.id.desc() if sort_dir == 'desc' else PIT.id.asc()
    else:
        order_col = PIT.time.desc()

    query = query.order_by(order_col)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'records': [{'id': r.id, 'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '', 'modelcode': r.modelcode, 'serial': r.serial, 'overallstatus': r.overallstatus, 'status1': r.status1, 'status2': r.status2, 'status3': r.status3, 'status4': r.status4, 'inspector': r.inspector or '—', 'lineno': r.lineno or '—'} for r in pagination.items]
    })

@admin_bp.route('/admin/api/pit-data/<int:id>', methods=['PUT', 'DELETE'])
def handle_pit_record(id):
    record = PIT.query.get(id)
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
        _trigger_pdf_bg(record.serial)
        return jsonify({'success': True, 'record': record.to_dict()})

@admin_bp.route('/admin/api/fit-data', methods=['GET'])
@login_required
def get_fit_data():
    page = max(1, int(request.args.get('page', 1)))
    per_page = max(1, int(request.args.get('per_page', 50)))
    total, records = _get_paginated_data(
        FIT, page, per_page, 
        request.args.get('date', '').strip(), 
        request.args.get('serial', '').strip(),
        request.args.get('sort_by', 'time').strip(),
        request.args.get('sort_dir', 'desc').strip()
    )
    ng = _check_ng_history(records)
    return jsonify({
        'total': total, 'page': page, 'per_page': per_page,
        'records': [{'id': r.id, 'lineno': r.lineno or '—', 'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '', 'modelcode': r.modelcode, 'serial': r.serial, 'overallstatus': r.overallstatus, 'inspector': r.inspector or '—', 'status1': r.status1 or '', 'status2': r.status2 or '', 'status3': r.status3 or '', 'data1': float(r.data1) if r.data1 is not None else '', 'data2': float(r.data2) if r.data2 is not None else '', 'status4': r.status4 or '', 'status5': r.status5 or '', 'status6': r.status6 or '', 'status7': r.status7 or '', 'status8': r.status8 or '', 'status9': r.status9 or '', 'status10': r.status10 or '', 'remarks': 'Past NG History' if ng.get(r.serial) else 'No remarks'} for r in records]
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
        res = {}
        for r in records:
            val = getattr(r, 'overallstatus', None)
            if not val:
                val = getattr(r, 'status', None)
            res[r.serial] = val
        return res

    att_status = get_latest_statuses(ATT)
    gms_status = get_latest_statuses(GMS)
    spamsi_status = get_latest_statuses(SPAMSI)
    spamso_status = get_latest_statuses(SPAMSO)
    wci_status = get_latest_statuses(WCI)
    rit_status = get_latest_statuses(RIT)
    pit_status = get_latest_statuses(PIT)
    fit_status = get_latest_statuses(FIT)
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
            'WCI': standardize_status(wci_status.get(s)),
            'RIT': standardize_status(rit_status.get(s)),
            'FIT': standardize_status(fit_status.get(s)),
            'PIT': standardize_status(pit_status.get(s))
        }
        
        # Check if all required stations are GOOD/PASS/OK
        required_stations = ['CRS', 'ATT', 'GMS', 'SPAMSI', 'SPAMSO', 'WCI', 'RIT', 'FIT', 'PIT']
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
            'wci': standardize_status(stations['WCI']),
            'rit': standardize_status(stations['RIT']),
            'fit': standardize_status(stations['FIT']),
            'pit': standardize_status(stations['PIT']),
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
    
    # Fetch all station records for this serial to populate the QC report fully
    from app.models.att import ATT
    from app.models.spamsi import SPAMSI
    from app.models.spamso import SPAMSO
    from app.models.wci import WCI
    from app.models.rit import RIT
    from app.models.fit import FIT
    from app.models.pit import PIT
    
    att_record = ATT.query.filter_by(serial=serial).order_by(ATT.time.desc()).first()
    spamsi_record = SPAMSI.query.filter((SPAMSI.serial == serial) | (SPAMSI.inserial == serial)).order_by(SPAMSI.time.desc()).first()
    spamso_record = SPAMSO.query.filter((SPAMSO.serial == serial) | (SPAMSO.outserial == serial)).order_by(SPAMSO.time.desc()).first()
    wci_record = WCI.query.filter_by(serial=serial).order_by(WCI.time.desc()).first()
    rit_record = RIT.query.filter_by(serial=serial).order_by(RIT.time.desc()).first()
    fit_record = FIT.query.filter_by(serial=serial).order_by(FIT.time.desc()).first()
    pit_record = PIT.query.filter_by(serial=serial).order_by(PIT.time.desc()).first()

    parts_list = []
    
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
    pit_record = PIT.query.filter_by(modelcode=model, serial=serial).first()
    
    for part in bom:
        p_serial = crs_parts_map.get(part.partno)
        parsed_dates = parse_serial_dates(p_serial)
        mfg_date = parsed_dates[0]
        barcode_arv_date = parsed_dates[1]
        
        arv_date = barcode_arv_date

        parts_list.append({
            'partno': part.partno,
            'partdesc': part.partdesc,
            'module': part.module,
            'mfg_date': mfg_date,
            'arv_date': arv_date
        })
        
    units_data = [{
        'serial': serial,
        'model': model,
        'crs_record': crs_record,
        'att_record': att_record,
        'gms_record': gms_record,
        'spamsi_record': spamsi_record,
        'spamso_record': spamso_record,
        'wci_record': wci_record,
        'rit_record': rit_record,
        'fit_record': fit_record,
        'pit_record': pit_record,
        'gas_charge': gas_charge,
        'parts_list': parts_list
    }]
        
    return render_template(
        'admin/qc_report_print.html',
        units_data=units_data,
        current_time=datetime.now()
    )

@admin_bp.route('/admin/api/linestat-viewer', methods=['GET'])
@login_required
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
            'inunique': e.inunique,
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
            'outmodel': e.outmodel,
            # outpart1-3 mod/desc columns are RESERVED — not populated or displayed
            'wcimodelcode': e.wcimodelcode,
            'wcivar': e.wcivar,
            'ritmodelcode': e.ritmodelcode,
            'ritvar': e.ritvar,
            'fitmodelcode': e.fitmodelcode,
            'fitvar': e.fitvar,
            'pitmodelcode': e.pitmodelcode,
            'pitvar': e.pitvar,
            'pittws': e.pittws,
            'gascharge': float(e.gascharge) if e.gascharge is not None else 0.00,
            'gmstolpos': float(e.gmstolpos) if e.gmstolpos is not None else 0.00,
            'gmstolneg': float(e.gmstolneg) if e.gmstolneg is not None else 0.00,
            'updtime': e.updtime.strftime('%Y-%m-%d %H:%M:%S') if e.updtime else None,
            'compmod': e.compmod,
            'fan1mod': e.fan1mod,
            'fan2mod': e.fan2mod,
            'crspart1mod': e.crspart1mod,
            'crspart1desc': e.crspart1desc,
            'crspart2mod': e.crspart2mod,
            'crspart2desc': e.crspart2desc,
            'crspart3mod': e.crspart3mod,
            'crspart3desc': e.crspart3desc,
            'crspart4mod': e.crspart4mod,
            'crspart4desc': e.crspart4desc,
            'area': e.area,
            'serialstart': e.serialstart,
            'active_date': e.active_date.strftime('%Y-%m-%d') if e.active_date else None,
            'reserve1': e.reserve1,
            'ritprogh': e.ritprogh,
            'ritprogf': e.ritprogf,
            'ritdata1': float(e.ritdata1) if e.ritdata1 is not None else None,
            'ritdata1tolpos': float(e.ritdata1tolpos) if e.ritdata1tolpos is not None else None,
            'ritdata1tolneg': float(e.ritdata1tolneg) if e.ritdata1tolneg is not None else None,
            'ritdata2': float(e.ritdata2) if e.ritdata2 is not None else None,
            'ritdata2tolpos': float(e.ritdata2tolpos) if e.ritdata2tolpos is not None else None,
            'ritdata2tolneg': float(e.ritdata2tolneg) if e.ritdata2tolneg is not None else None,
            'ritdata3': float(e.ritdata3) if e.ritdata3 is not None else None,
            'ritdata3tolpos': float(e.ritdata3tolpos) if e.ritdata3tolpos is not None else None,
            'ritdata3tolneg': float(e.ritdata3tolneg) if e.ritdata3tolneg is not None else None,
            'ritheat1': e.ritheat1,
            'ritheat2': e.ritheat2,
            'fitdata1': float(e.fitdata1) if e.fitdata1 is not None else None,
            'fitdata1tolpos': float(e.fitdata1tolpos) if e.fitdata1tolpos is not None else None,
            'fitdata1tolneg': float(e.fitdata1tolneg) if e.fitdata1tolneg is not None else None,
            'fitdata2': float(e.fitdata2) if e.fitdata2 is not None else None,
            'fitdata2tolpos': float(e.fitdata2tolpos) if e.fitdata2tolpos is not None else None,
            'fitdata2tolneg': float(e.fitdata2tolneg) if e.fitdata2tolneg is not None else None
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
        if stat.pitvar and stat.pitvar > 0 and stat.pitmodelcode:
            models.append({'model': stat.pitmodelcode, 'station': 'PIT', 'qty': stat.pitvar})
        if stat.fitvar and stat.fitvar > 0 and stat.fitmodelcode:
            models.append({'model': stat.fitmodelcode, 'station': 'FI', 'qty': stat.fitvar})
        if stat.ritvar and stat.ritvar > 0 and stat.ritmodelcode:
            models.append({'model': stat.ritmodelcode, 'station': 'RI', 'qty': stat.ritvar})
        if stat.wcivar and stat.wcivar > 0 and stat.wcimodelcode:
            models.append({'model': stat.wcimodelcode, 'station': 'WC', 'qty': stat.wcivar})
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
        # Frontend JS sends {line_id: lineCode, action: 'clear'}
        line_code = data.get('line_code') or data.get('line_id')
        action = data.get('action')
        
        if action in ('clear', 'clear_all'):
            from app.models.linestat import LineStat
            from app.models.worksched import WorkSched
            
            stat = LineStat.query.filter_by(lineno=line_code).first()
            if stat:
                # WIPE EVERY STATION COMPLETELY
                stat.status = 'No Work'
                
                stat.crsvar = 0
                stat.crsmodelcode = None
                
                stat.wcivar = 0
                stat.wcimodelcode = None
                
                stat.attvar = 0
                stat.attmodelcode = None
                
                stat.gmsvar = 0
                stat.gmsmodelcode = None
                
                stat.ritvar = 0
                stat.ritmodelcode = None
                
                stat.fitvar = 0
                stat.fitmodelcode = None
                
                stat.pitvar = 0
                stat.pitmodelcode = None
                
                stat.invar = 0
                stat.inmodelcode = None
                
                stat.outvar = 0
                stat.outmodelcode = None
                
            # Permanently discard ALL unfinished schedules across ALL past dates
            # (and today) so they no longer appear as "Past Work" or Ghost Data
            unfinished_scheds = WorkSched.query.filter(
                WorkSched.lineno == line_code,
                WorkSched.act < WorkSched.plan
            ).all()
            
            for sched in unfinished_scheds:
                sched.plan = sched.act
                
            db.session.commit()

        elif action == 'readd_all':
            # Fix 2: Carry over all unfinished past schedules to today
            from app.models.linestat import LineStat
            from app.models.worksched import WorkSched
            from datetime import datetime
            
            today_date = datetime.now().date()
            lineno = line_code if str(line_code).startswith('L') else f"L{line_code}"
            
            # Find the most recent past date with unfinished schedules
            ghost_date = db.session.query(db.func.max(WorkSched.date)).filter(
                WorkSched.date < today_date,
                WorkSched.lineno == lineno
            ).scalar()
            
            if not ghost_date:
                return jsonify({'success': False, 'error': 'No past schedules found.'})
            
            unfinished = WorkSched.query.filter(
                WorkSched.lineno == lineno,
                WorkSched.date == ghost_date,
                WorkSched.act < WorkSched.plan
            ).order_by(WorkSched.seq.asc()).all()
            
            if not unfinished:
                return jsonify({'success': False, 'error': 'No unfinished schedules to carry over.'})
            
            # Get next sequence for today
            last_sched = WorkSched.query.filter_by(lineno=lineno, date=today_date).order_by(WorkSched.seq.desc()).first()
            next_seq = 0 if not last_sched else last_sched.seq + 1
            
            for sched in unfinished:
                remaining = sched.plan - sched.act
                if remaining <= 0:
                    continue
                
                # Fix 4: Avoid UniqueConstraint crash on duplicate (lineno, date, modelcode)
                existing = WorkSched.query.filter_by(lineno=lineno, date=today_date, modelcode=sched.modelcode).first()
                if existing:
                    existing.plan += remaining
                else:
                    new_sched = WorkSched(
                        lineno=lineno,
                        seq=next_seq,
                        modelcode=sched.modelcode,
                        plan=remaining,
                        act=0,
                        takttime=sched.takttime,
                        date=today_date
                    )
                    db.session.add(new_sched)
                    next_seq += 1
                
                # Close out the ghost schedule
                sched.plan = sched.act
            
            # Fix 3: Transition linestat.active_date to today
            stat = LineStat.query.filter_by(lineno=lineno).first()
            if stat:
                stat.active_date = today_date
                stat.updtime = datetime.now()
            
            db.session.commit()
            
            # Initialize the line from the new today-schedules if idle,
            # or bump updtime if belt is still running
            try:
                has_active_belt = stat and any([
                    stat.crsvar and stat.crsvar > 0,
                    stat.attvar and stat.attvar > 0,
                    stat.gmsvar and stat.gmsvar > 0,
                    stat.invar and stat.invar > 0,
                    stat.outvar and stat.outvar > 0,
                    stat.wcivar and stat.wcivar > 0,
                    stat.ritvar and stat.ritvar > 0,
                    stat.fitvar and stat.fitvar > 0,
                    stat.pitvar and stat.pitvar > 0,
                ])
                if not has_active_belt:
                    from app.services.linestat_monitor import initialize_line
                    initialize_line(lineno)
                else:
                    from app.services.linestat_monitor import force_restart_for_manual_edit
                    force_restart_for_manual_edit()
            except Exception as _init_err:
                logger.warning('linestat update failed after readd_all: %s', _init_err)
                
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ── SHIFTS API ───────────────────────────────────────────────────────────────

@admin_bp.route('/admin/api/shifts', methods=['GET', 'POST'])
@login_required
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

@admin_bp.route('/admin/api/transfer-slips/available-dates', methods=['GET'])
@login_required
def get_transfer_slip_available_dates():
    try:
        # Fetch all distinct dates where PIT overallstatus is GOOD
        records = PIT.query.with_entities(func.date(PIT.time)).filter(
            PIT.overallstatus == 'GOOD'
        ).distinct().all()
        
        # Sort newest first
        dates = sorted([r[0].strftime('%Y-%m-%d') for r in records if r[0]], reverse=True)
        return jsonify({'success': True, 'dates': dates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
        records = PIT.query.filter(
            func.date(PIT.time) == p_date
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

    # 1. Fetch serials from PIT that passed
    pit_records = PIT.query.filter(
        func.date(PIT.time) == p_date,
        PIT.lineno == line,
        PIT.modelcode == modelcode
    ).all()
    
    serials = [p.serial for p in pit_records if p.overallstatus == 'GOOD' and p.serial not in assigned_serials]
    total_qty = len(serials)
    
    if total_qty == 0:
        return jsonify({'success': False, 'error': 'No completed units found for these parameters.'}), 404

    # 2. Generate Ref Number (Format: Line No. | Last 2 digit of year | Month | Series)
    # Series is 4-digit count of slips created in this month
    year2 = str(p_date.year)[-2:]
    month2 = f"{p_date.month:02d}"
    
    prefix = f"{line}{year2}{month2}"
    month_slips_count = TransferSlip.query.filter(
        TransferSlip.ref_number.startswith(prefix)
    ).count()
    
    series4 = f"{month_slips_count + 1:04d}"
    ref_number = f"{prefix}{series4}"
    
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
    
    # 4. Trigger CSV Generation automatically on manual creation
    from app.services.csv_generator import generate_transfer_slip_csv
    generate_transfer_slip_csv(new_slip.id)
    
    return jsonify({'success': True, 'slip_id': new_slip.id, 'ref_number': new_slip.ref_number})

@admin_bp.route('/admin/api/trigger-transfer-csv/<int:slip_id>', methods=['POST'])
@login_required
def trigger_transfer_csv(slip_id):
    """Trigger the generation of the Transfer Slip CSV manually."""
    from app.services.csv_generator import generate_transfer_slip_csv
    success = generate_transfer_slip_csv(slip_id)
    if success:
        return jsonify({'success': True, 'message': 'CSV generated successfully on the server.'})
    else:
        return jsonify({'success': False, 'error': 'Failed to generate CSV. Check server logs.'}), 500


@admin_bp.route('/admin/print-transfer-slip/<int:slip_id>', methods=['GET'])
@login_required
def print_transfer_slip(slip_id):
    slip = TransferSlip.query.get_or_404(slip_id)
    import json
    serials = json.loads(slip.serials_json) if slip.serials_json else []
    
    # Smart Pagination Logic
    rows = [serials[i:i+5] for i in range(0, len(serials), 5)]
    pages = []
    
    if len(rows) <= 12:
        # Fits completely on Page 1 along with the signature footer
        pages.append(rows)
        rows = []
    else:
        # Does not fit on Page 1 with footer. Page 1 gets 18 rows (no footer).
        pages.append(rows[:18])
        rows = rows[18:]
        
    # Handle subsequent pages (No metadata header, so they can fit more rows)
    # A full middle page can fit 28 rows.
    # The last page (needs signature footer) can fit 22 rows.
    while rows:
        if len(rows) <= 22:
            pages.append(rows)
            break
        else:
            pages.append(rows[:28])
            rows = rows[28:]
            
    total_pages = len(pages) if pages else 1
    
    print_date = datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    finished_date = slip.time.strftime('%m-%d-%Y') if slip.time else '--'
    
    # Calculate real start and end times from PIT
    start_time = '--:--:--'
    end_time = '--:--:--'
    
    if serials:
        pit_records = PIT.query.filter(PIT.serial.in_(serials)).all()
        pit_times = [p.time for p in pit_records if p.time]
        if pit_times:
            end_time = max(pit_times).strftime('%H:%M:%S')
            
        from app.models.crs import CRS
        crs_records = CRS.query.filter(CRS.serial.in_(serials)).all()
        crs_times = [c.time for c in crs_records if c.time]
        if crs_times:
            start_time = min(crs_times).strftime('%H:%M:%S')

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
    
    query = PIT.query
    
    if date_filter:
        try:
            parsed = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(func.date(PIT.time) == parsed)
        except ValueError:
            pass
            
    if line_filter and line_filter.lower() != 'all':
        query = query.filter(PIT.lineno == line_filter)
        
    if serial_filter:
        query = query.filter(PIT.serial.ilike(f'%{serial_filter}%'))
        
    records = query.order_by(PIT.time.desc()).limit(100).all()
    
    return jsonify({
        'success': True,
        'records': [{
            'id': r.id,
            'time': r.time.strftime('%Y-%m-%d %H:%M:%S') if r.time else '',
            'modelcode': r.modelcode,
            'serial': r.serial,
            'line': r.lineno,
            'status': r.overallstatus
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
    from app.models.wci import WCI
    from app.models.rit import RIT
    from app.models.fit import FIT
    from app.models.pit import PIT
    
    for s in serial_list:
        crs = CRS.query.filter_by(serial=s).order_by(CRS.time.desc()).first()
        att = ATT.query.filter_by(serial=s).order_by(ATT.time.desc()).first()
        gms = GMS.query.filter_by(serial=s).order_by(GMS.time.desc()).first()
        spamsi = SPAMSI.query.filter((SPAMSI.serial == s) | (SPAMSI.inserial == s)).order_by(SPAMSI.time.desc()).first()
        spamso = SPAMSO.query.filter((SPAMSO.serial == s) | (SPAMSO.outserial == s)).order_by(SPAMSO.time.desc()).first()
        wci = WCI.query.filter_by(serial=s).order_by(WCI.time.desc()).first()
        rit = RIT.query.filter_by(serial=s).order_by(RIT.time.desc()).first()
        fit = FIT.query.filter_by(serial=s).order_by(FIT.time.desc()).first()
        pit = PIT.query.filter_by(serial=s).order_by(PIT.time.desc()).first()
        
        # Determine model
        model = ''
        if pit and pit.modelcode: model = pit.modelcode
        elif fit and fit.modelcode: model = fit.modelcode
        elif rit and rit.modelcode: model = rit.modelcode
        elif wci and wci.modelcode: model = wci.modelcode
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
            'wci_record': wci,
            'rit_record': rit,
            'fit_record': fit,
            'pit_record': pit
        })
        
    return render_template('admin/qc_report_print.html', units_data=units_data, current_time=datetime.now())

