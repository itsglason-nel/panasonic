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
from app.models.wci import WCI
from app.models.rit import RIT
from app.models.fit import FIT
from app.models.pit import PIT
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
    date_str = request.args.get('date', '').strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    line_no = request.args.get('line')
    if line_no == 'all':
        line_no = None
    
    target_date = None
    if date_str:
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

    query = WorkSched.query
    if target_date:
        from sqlalchemy import or_, and_
        query = query.filter(
            or_(
                WorkSched.date == target_date,
                and_(WorkSched.date < target_date, WorkSched.act < WorkSched.plan)
            )
        )
    if line_no:
        query = query.filter_by(lineno=line_no)
        
    schedule = query.order_by(WorkSched.lineno, WorkSched.date.asc(), WorkSched.seq.asc()).all()
    
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

    # Calculate WIP directly from LineStat vars
    wip = {
        'crs': 0, 'att': 0, 'gms': 0, 'spamsi': 0, 'spamso': 0,
        'wc': 0, 'ri': 0, 'fi': 0, 'pit': 0,
        'models': {
            'crs': '—', 'att': '—', 'gms': '—', 'spamsi': '—', 'spamso': '—',
            'wc': '—', 'ri': '—', 'fi': '—', 'pit': '—'
        }
    }
    
    # Query the latest active linestat for the current line(s)
    # If line_no is provided, fetch just that line, else fetch all active lines and sum the WIP
    linestat_query = LineStat.query.filter_by(status='Work')
    if line_no:
        linestat_query = linestat_query.filter_by(lineno=line_no)
        
    active_linestats = linestat_query.all()
    
    for ls in active_linestats:
        wip['crs'] += (ls.crsvar or 0)
        wip['att'] += (ls.attvar or 0)
        wip['gms'] += (ls.gmsvar or 0)
        wip['spamsi'] += (ls.invar or 0)
        wip['spamso'] += (ls.outvar or 0)
        wip['wc'] += (ls.wcivar or 0)
        wip['ri'] += (ls.ritvar or 0)
        wip['fi'] += (ls.fitvar or 0)
        wip['pit'] += (ls.pitvar or 0)
        
    # Get active models for WIP (take from the first active linestat if available, or fetch last from tables if needed)
    # To keep it consistent, we pull the modelcode from linestat directly
    if active_linestats:
        if len(active_linestats) == 1 or line_no:
            ls = sorted(active_linestats, key=lambda x: x.id, reverse=True)[0]
            wip['models'] = {
            'crs': ls.crsmodelcode or '—',
            'att': ls.attmodelcode or ls.crsmodelcode or '—',
            'gms': ls.gmsmodelcode or ls.crsmodelcode or '—',
            'spamsi': ls.inmodelcode or ls.crsmodelcode or '—',
            'spamso': ls.outmodelcode or ls.crsmodelcode or '—',
            'wc': ls.wcimodelcode or ls.crsmodelcode or '—',
            'ri': ls.ritmodelcode or ls.crsmodelcode or '—',
            'fi': ls.fitmodelcode or ls.crsmodelcode or '—',
            'pit': ls.pitmodelcode or ls.crsmodelcode or '—'
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
    date_str = request.args.get('date', '').strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    model_filter = request.args.get('model', '').strip()
    sort_order = request.args.get('sort', 'desc').strip().lower()
    
    target_date = None
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    query = CRS.query
    if target_date:
        query = query.filter(func.date(CRS.time) == target_date)
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
            pit_rec = PIT.query.filter_by(serial=serial).order_by(PIT.time.desc()).first()
            if pit_rec:
                pack_statuses = [pit_rec.status1, pit_rec.status2, pit_rec.status3, pit_rec.status4]
                if any(s in ['NG', 'NO GOOD'] for s in pack_statuses if s):
                    status = 'NO GOOD'
                    remarks = 'NO GOOD AT PIT'

        if status == 'GOOD':
            fit_rec = FIT.query.filter_by(serial=serial).order_by(FIT.time.desc()).first()
            if fit_rec and fit_rec.overallstatus in ['NG', 'NO GOOD']:
                status = 'NO GOOD'
                remarks = 'NO GOOD AT FINAL INSP'
                
        if status == 'GOOD':
            rit_rec = RIT.query.filter_by(serial=serial).order_by(RIT.time.desc()).first()
            if rit_rec and rit_rec.overallstatus in ['NG', 'NO GOOD']:
                status = 'NO GOOD'
                remarks = 'NO GOOD AT RUNNING INSP'

        if status == 'GOOD':
            wci_rec = WCI.query.filter_by(serial=serial).order_by(WCI.time.desc()).first()
            if wci_rec and wci_rec.overallstatus in ['NG', 'NO GOOD']:
                status = 'NO GOOD'
                remarks = 'NO GOOD AT WIRING'

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
        
    date_str = request.args.get('date', '').strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    target_date = None
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400

    query = db.session.query(CRS.modelcode)
    if target_date:
        query = query.filter(func.date(CRS.time) == target_date)
    if line_no:
        query = query.filter(CRS.lineno == line_no)
        
    models = query.distinct().all()
    
    return jsonify({
        'success': True,
        'models': [m[0] for m in models if m[0]]
    })
