from app.models import db

class RIT(db.Model):
    __tablename__ = 'rit'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    
    status1 = db.Column(db.String(12), nullable=True)
    status2 = db.Column(db.String(12), nullable=True)
    status3 = db.Column(db.String(12), nullable=True)
    status4 = db.Column(db.String(12), nullable=True)
    status5 = db.Column(db.String(12), nullable=True)
    status6 = db.Column(db.String(12), nullable=True)
    status7 = db.Column(db.String(12), nullable=True)
    status8 = db.Column(db.String(12), nullable=True)
    status9 = db.Column(db.String(12), nullable=True)
    data1 = db.Column(db.Numeric(4, 2), nullable=True)
    status10 = db.Column(db.String(12), nullable=True)
    data2 = db.Column(db.Numeric(4, 2), nullable=True)
    data3 = db.Column(db.Numeric(4, 2), nullable=True)
    
    progh = db.Column(db.String(6), nullable=True)
    progf = db.Column(db.String(6), nullable=True)
    
    overallstatus = db.Column(db.String(12), nullable=True)
    time = db.Column(db.TIMESTAMP, nullable=False)
    inspector = db.Column(db.String(20), nullable=True)
    lineno = db.Column(db.String(4), nullable=True)
