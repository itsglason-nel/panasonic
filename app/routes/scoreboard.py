from flask import Blueprint, jsonify, render_template, request, current_app
from app.models import db
from app.models.worksched import WorkSched
from app.models.line import Line
from datetime import datetime, date, time
from app.models.shift import Shift
from app.models.crs import CRS
from app.models.att import ATT
from app.models.gms import GMS
from app.models.spamsi import SPAMSI
from app.models.spamso import SPAMSO
from app.models.insp2 import INSP2
from app.models.insp3_run import INSP3Run
from app.models.insp4 import INSP4
from app.models.packaging import Packaging
from app.models.linestat import LineStat

from sqlalchemy import func

scoreboard_bp = Blueprint('scoreboard', __name__)

@scoreboard_bp.route('/scoreboard', methods=['GET'])
def all_lines():
    """Renders the main scoreboard dashboard displaying all active lines."""
    lines = Line.query.filter_by(is_active=True).order_by(Line.lineno).all()
    return render_template('scoreboard/all_lines.html', lines=lines)

@scoreboard_bp.route('/scoreboard/line/<line_no>', methods=['GET'])
def line_scoreboard(line_no):
    """Renders a detailed scoreboard for a specific line."""
    line = Line.query.filter_by(lineno=line_no, is_active=True).first_or_404()
    return render_template('scoreboard/line.html', line=line)

@scoreboard_bp.route('/api/scoreboard/data', methods=['GET'])
def get_scoreboard_data():
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    line_no = request.args.get('line')
    if line_no == 'all':
        line_no = None
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400
        
    now = datetime.now()
    current_time = now.time()
    shifts = Shift.query.all()
    
    shift_name = 'DAY'
    shift_start = '06:00'
    for s in shifts:
        s_start = s.start_time
        s_end = s.end_time
        
        if s_start <= s_end:
            if s_start <= current_time <= s_end:
                shift_name = s.name
                shift_start = s.start_time.strftime('%H:%M')
                break
        else: # Night shift crosses midnight
            if current_time >= s_start or current_time <= s_end:
                shift_name = s.name
                shift_start = s.start_time.strftime('%H:%M')
                break

    query = WorkSched.query.filter_by(date=target_date)
    if line_no:
        query = query.filter_by(lineno=line_no)
        
    schedule = query.order_by(WorkSched.lineno, WorkSched.seq).all()
    
    data = []
    active_seq_found = False
    
    for sched in schedule:
        status = 'WAITING'
        if sched.act >= sched.plan:
            status = 'DONE'
        elif sched.act > 0 or not active_seq_found:
            status = 'ON-GOING'
            active_seq_found = True
            
        data.append({
            'id': sched.id,
            'lineno': sched.lineno,
            'seq': sched.seq,
            'modelcode': sched.modelcode,
            'plan': sched.plan,
            'actual': sched.act,
            'takt_time': sched.takttime,
            'status': status
        })

    # Calculate WIP
    wip = {}
    
    def get_count_with_lineno(table):
        query = db.session.query(func.count(table.id)).filter(func.date(table.time) == target_date)
        if line_no:
            query = query.filter(table.lineno == line_no)
        return query.scalar() or 0
        
    def get_count_no_lineno(table):
        return db.session.query(func.count(table.id)).filter(func.date(table.time) == target_date).scalar() or 0

    c_crs = get_count_with_lineno(CRS)
    c_att = get_count_with_lineno(ATT)
    c_gms = get_count_with_lineno(GMS)
    c_spamsi = get_count_no_lineno(SPAMSI)
    c_spamso = get_count_no_lineno(SPAMSO)
    c_wc = get_count_no_lineno(INSP2)
    c_ri = get_count_no_lineno(INSP3Run)
    c_fi = get_count_no_lineno(INSP4)
    c_pack = get_count_with_lineno(Packaging)

    # Get active models for WIP
    def get_active_model(model_class, has_lineno=True):
        q = model_class.query
        if line_no and has_lineno:
            q = q.filter_by(lineno=line_no)
        res = q.order_by(model_class.time.desc()).first()
        return res.modelcode if res else '—'

    wip = {
        'att': max(0, c_crs - c_att),
        'gms': max(0, c_att - c_gms),
        'spamsi': max(0, c_gms - c_spamsi),
        'spamso': max(0, c_spamsi - c_spamso),
        'wc': max(0, c_spamso - c_wc),
        'ri': max(0, c_wc - c_ri),
        'fi': max(0, c_ri - c_fi),
        'pack': max(0, c_fi - c_pack),
        'models': {
            'att': get_active_model(ATT),
            'gms': get_active_model(GMS),
            'spamsi': get_active_model(SPAMSI, has_lineno=False),
            'spamso': get_active_model(SPAMSO, has_lineno=False),
            'wc': get_active_model(INSP2, has_lineno=False),
            'ri': get_active_model(INSP3Run, has_lineno=False),
            'fi': get_active_model(INSP4, has_lineno=False),
            'pack': get_active_model(Packaging)
        }
    }
        
    return jsonify({
        'success': True,
        'date': date_str,
        'shift_name': shift_name,
        'shift_start': shift_start,
        'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'data': data,
        'wip': wip
    })

@scoreboard_bp.route('/api/scoreboard/logs', methods=['GET'])
def get_scoreboard_logs():
    line_no = request.args.get('line')
    if line_no == 'all':
        line_no = None
        
    limit = request.args.get('limit', 15, type=int)
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    model_filter = request.args.get('model', '').strip()
    sort_order = request.args.get('sort', 'desc').strip().lower()
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    query = CRS.query.filter(func.date(CRS.time) == target_date)
    if line_no:
        query = query.filter(CRS.lineno == line_no)
    
    if model_filter and model_filter != 'all':
        query = query.filter(CRS.modelcode == model_filter)
        
    if sort_order == 'asc':
        query = query.order_by(CRS.time.asc())
    else:
        query = query.order_by(CRS.time.desc())
        
    recent_crs = query.limit(limit).all()
    
    logs = []
    for c in recent_crs:
        serial = c.serial
        model = c.modelcode
        status = 'GOOD'
        remarks = 'GOOD'
        
        # Check downstream stations for failures
        if status == 'GOOD':
            pack_rec = Packaging.query.filter_by(serial=serial).order_by(Packaging.time.desc()).first()
            if pack_rec:
                pack_statuses = [pack_rec.status1, pack_rec.status2, pack_rec.status3, pack_rec.status4]
                if any(s in ['NG', 'NO GOOD'] for s in pack_statuses if s):
                    status = 'NO GOOD'
                    remarks = 'NO GOOD AT PACKAGING'

        if status == 'GOOD':
            insp4_rec = INSP4.query.filter_by(serial=serial).order_by(INSP4.time.desc()).first()
            if insp4_rec and insp4_rec.status in ['NG', 'NO GOOD']:
                status = 'NO GOOD'
                remarks = insp4_rec.remarks or 'NO GOOD AT FINAL INSP'
                
        if status == 'GOOD':
            insp3_rec = INSP3Run.query.filter_by(serial=serial).order_by(INSP3Run.time.desc()).first()
            if insp3_rec and insp3_rec.status in ['NG', 'NO GOOD']:
                status = 'NO GOOD'
                remarks = insp3_rec.remarks or 'NO GOOD AT RUNNING INSP'

        if status == 'GOOD':
            insp2_rec = INSP2.query.filter_by(serial=serial).order_by(INSP2.time.desc()).first()
            if insp2_rec and insp2_rec.status in ['NG', 'NO GOOD']:
                status = 'NO GOOD'
                remarks = insp2_rec.remarks or 'NO GOOD AT WIRING'

        if status == 'GOOD':
            gms_rec = GMS.query.filter_by(serial=serial).order_by(GMS.time.desc()).first()
            if gms_rec and gms_rec.status in ['NG', 'NO GOOD']:
                status = 'NO GOOD'
                remarks = 'NO GOOD AT GAS CHARGING'

        logs.append({
            'time': c.time.strftime('%H:%M:%S') if c.time else '',
            'model': model,
            'serial': serial,
            'status': status,
            'remarks': remarks
        })
        
    return jsonify({
        'success': True,
        'logs': logs
    })

@scoreboard_bp.route('/api/scoreboard/models', methods=['GET'])
def get_scoreboard_models():
    line_no = request.args.get('line')
    if line_no == 'all':
        line_no = None
        
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    query = db.session.query(CRS.modelcode).filter(func.date(CRS.time) == target_date)
    if line_no:
        query = query.filter(CRS.lineno == line_no)
        
    models = query.distinct().all()
    
    return jsonify({
        'success': True,
        'models': [m[0] for m in models if m[0]]
    })
