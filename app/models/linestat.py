from app.models import db

class LineStat(db.Model):
    __tablename__ = 'linestat'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    updtime = db.Column(db.TIMESTAMP, server_default=db.text('CURRENT_TIMESTAMP'))
    lineno = db.Column(db.String(4), nullable=True)
    active_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(12), server_default='No Work')
    
    crsmodelcode = db.Column(db.String(14), nullable=True)
    compmod = db.Column(db.String(14), nullable=True)
    fan1mod = db.Column(db.String(14), nullable=True)
    fan2mod = db.Column(db.String(14), nullable=True)
    crspart1mod = db.Column(db.String(14), nullable=True)
    crspart1desc = db.Column(db.String(30), nullable=True)
    crspart2mod = db.Column(db.String(14), nullable=True)
    crspart2desc = db.Column(db.String(30), nullable=True)
    crspart3mod = db.Column(db.String(14), nullable=True)
    crspart3desc = db.Column(db.String(30), nullable=True)
    crspart4mod = db.Column(db.String(14), nullable=True)
    crspart4desc = db.Column(db.String(30), nullable=True)
    area = db.Column(db.String(14), nullable=True)
    serialstart = db.Column(db.String(6), nullable=True)
    crsvar = db.Column(db.Integer, nullable=True)
    reserve1 = db.Column(db.String(20), nullable=True)
    
    attmodelcode = db.Column(db.String(14), nullable=True)
    attvar = db.Column(db.Integer, nullable=True)
    
    gmsmodelcode = db.Column(db.String(14), nullable=True)
    gmsvar = db.Column(db.Integer, nullable=True)
    gascharge = db.Column(db.Numeric(4, 2), nullable=False, default=0.00)
    gmstolpos = db.Column(db.Numeric(4, 2), nullable=True, default=0)
    gmstolneg = db.Column(db.Numeric(4, 2), nullable=True, default=0)

    # SPAMSI (Indoor)
    inmodelcode = db.Column(db.String(14), nullable=True)
    invar = db.Column(db.Integer, nullable=True)
    inuniqe = db.Column(db.String(4), nullable=True)
    inpart1mod = db.Column(db.String(14), nullable=True)
    inpart1desc = db.Column(db.String(30), nullable=True)
    inpart2mod = db.Column(db.String(14), nullable=True)
    inpart2desc = db.Column(db.String(30), nullable=True)
    inpart3mod = db.Column(db.String(14), nullable=True)
    inpart3desc = db.Column(db.String(30), nullable=True)
    inpart4mod = db.Column(db.String(14), nullable=True)
    inpart4desc = db.Column(db.String(30), nullable=True)
    inpart5mod = db.Column(db.String(14), nullable=True)
    inpart5desc = db.Column(db.String(30), nullable=True)
    inpart6mod = db.Column(db.String(14), nullable=True)
    inpart6desc = db.Column(db.String(30), nullable=True)
    
    # SPAMSO (Outdoor)
    outmodelcode = db.Column(db.String(14), nullable=True)
    outvar = db.Column(db.Integer, nullable=True)
    outmodel = db.Column(db.String(14), nullable=True)
    outpart1mod = db.Column(db.String(14), nullable=True)
    outpart1desc = db.Column(db.String(30), nullable=True)
    outpart2mod = db.Column(db.String(14), nullable=True)
    outpart2desc = db.Column(db.String(30), nullable=True)
    outpart3mod = db.Column(db.String(14), nullable=True)
    outpart3desc = db.Column(db.String(30), nullable=True)

    # WIRING & CONSTRUCTION
    wcmodelcode = db.Column(db.String(14), nullable=True)
    wcvar = db.Column(db.Integer, nullable=True)

    # RUNNING INSPECTION
    rimodelcode = db.Column(db.String(14), nullable=True)
    rivar = db.Column(db.Integer, nullable=True)
    ri_progh = db.Column(db.String(6), nullable=True)
    ri_progf = db.Column(db.String(6), nullable=True)
    ri_opcur = db.Column(db.Numeric(8,2), nullable=True)
    ri_opcur_pos = db.Column(db.Numeric(2,0), nullable=True)
    ri_opcur_neg = db.Column(db.Numeric(2,0), nullable=True)
    ri_oppow = db.Column(db.Numeric(8,2), nullable=True)
    ri_oppow_pos = db.Column(db.Numeric(2,0), nullable=True)
    ri_oppow_neg = db.Column(db.Numeric(2,0), nullable=True)
    ri_tempdiff = db.Column(db.Numeric(8,2), nullable=True)
    ri_tempdiff_pos = db.Column(db.Numeric(2,0), nullable=True)
    ri_tempdiff_neg = db.Column(db.Numeric(2,0), nullable=True)

    # FINAL INSPECTION
    fimodelcode = db.Column(db.String(14), nullable=True)
    fivar = db.Column(db.Integer, nullable=True)
    fi_opcur = db.Column(db.Numeric(5,2), nullable=True)
    fi_oppow = db.Column(db.Numeric(5,2), nullable=True)

    # PACKAGING
    packmodelcode = db.Column(db.String(14), nullable=True)
    packvar = db.Column(db.Integer, nullable=True)
