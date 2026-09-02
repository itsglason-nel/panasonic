import sys
sys.path.insert(0, '.')
from app import create_app, db
from app.models.worksched import WorkSched
from app.models.linestat import LineStat
from datetime import date

app = create_app()
with app.app_context():
    today = date.today()
    lineno = 'L1'
    modelcode = 'TEST-1234'
    plan = 20
    
    # Check if we already have it
    sched = WorkSched.query.filter_by(lineno=lineno, date=today, modelcode=modelcode).first()
    if not sched:
        # Find next seq
        max_seq = db.session.query(db.func.max(WorkSched.seq)).filter_by(lineno=lineno, date=today).scalar()
        seq = 0 if max_seq is None else max_seq + 1
        
        sched = WorkSched(
            lineno=lineno,
            seq=seq,
            modelcode=modelcode,
            plan=plan,
            act=5,
            takttime=60,
            date=today
        )
        db.session.add(sched)
    else:
        sched.plan = plan
        sched.act = 5
        
    ls = LineStat.query.filter_by(lineno=lineno).first()
    if not ls:
        ls = LineStat(id=1, lineno=lineno, status='Work', active_date=today)
        db.session.add(ls)
        
    ls.status = 'Work'
    ls.active_date = today
    ls.crsmodelcode = modelcode
    ls.crsvar = 10  # 10 passed CRS
    ls.attmodelcode = modelcode
    ls.attvar = 12  # 8 passed ATT
    ls.gmsmodelcode = modelcode
    ls.gmsvar = 15  # 5 passed GMS
    
    db.session.commit()
    print("Successfully added test WIMP and updated LineStat!")
    print(f"Model: {modelcode}")
    print(f"Plan: {plan}")
    print(f"Passed CRS: 10 (Remaining: 10)")
    print(f"Passed ATT: 8 (Remaining: 12)")
    print(f"Passed GMS: 5 (Remaining: 15)")
