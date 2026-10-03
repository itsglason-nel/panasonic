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
    inunique = db.Column(db.String(4), nullable=True)
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
    # RESERVED — outpart columns below are retained in the schema but have no active
    # function. They are not populated by the stored procedure or displayed in the UI.
    outpart1mod = db.Column(db.String(14), nullable=True)   # RESERVED
    outpart1desc = db.Column(db.String(30), nullable=True)  # RESERVED
    outpart2mod = db.Column(db.String(14), nullable=True)   # RESERVED
    outpart2desc = db.Column(db.String(30), nullable=True)  # RESERVED
    outpart3mod = db.Column(db.String(14), nullable=True)   # RESERVED
    outpart3desc = db.Column(db.String(30), nullable=True)  # RESERVED

    # WCI
    wcimodelcode = db.Column(db.String(14), nullable=True)
    wcivar = db.Column(db.Integer, nullable=True)

    # RIT
    ritmodelcode = db.Column(db.String(14), nullable=True)
    ritvar = db.Column(db.Integer, nullable=True)
    ritprogh = db.Column(db.String(6), nullable=True)
    ritprogf = db.Column(db.String(6), nullable=True)
    ritdata1 = db.Column(db.Numeric(4,2), nullable=True)
    ritdata1tolpos = db.Column(db.Numeric(4,2), nullable=True)
    ritdata1tolneg = db.Column(db.Numeric(4,2), nullable=True)
    ritdata2 = db.Column(db.Numeric(4,2), nullable=True)
    ritdata2tolpos = db.Column(db.Numeric(4,2), nullable=True)
    ritdata2tolneg = db.Column(db.Numeric(4,2), nullable=True)
    ritdata3 = db.Column(db.Numeric(4,2), nullable=True)
    ritdata3tolpos = db.Column(db.Numeric(4,2), nullable=True)
    ritdata3tolneg = db.Column(db.Numeric(4,2), nullable=True)
    ritheat1 = db.Column(db.String(2), nullable=True)
    ritheat2 = db.Column(db.String(2), nullable=True)

    # FIT
    fitmodelcode = db.Column(db.String(14), nullable=True)
    fitvar = db.Column(db.Integer, nullable=True)
    fitdata1 = db.Column(db.Numeric(4,2), nullable=True)
    fitdata1tolpos = db.Column(db.Numeric(4,2), nullable=True)
    fitdata1tolneg = db.Column(db.Numeric(4,2), nullable=True)
    fitdata2 = db.Column(db.Numeric(4,2), nullable=True)
    fitdata2tolpos = db.Column(db.Numeric(4,2), nullable=True)
    fitdata2tolneg = db.Column(db.Numeric(4,2), nullable=True)

    # PIT
    pitmodelcode = db.Column(db.String(14), nullable=True)
    pitvar = db.Column(db.Integer, nullable=True)
    pittws = db.Column(db.String(2), nullable=True)
