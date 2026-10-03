from app.models import db

class PIT(db.Model):
    __tablename__ = 'pit'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=True)
    serial = db.Column(db.String(14), nullable=True)
    
    status1 = db.Column(db.String(12), nullable=True)
    status2 = db.Column(db.String(12), nullable=True)
    status3 = db.Column(db.String(12), nullable=True)
    status4 = db.Column(db.String(12), nullable=True)
    
    overallstatus = db.Column(db.String(12), nullable=True)
    time = db.Column(db.TIMESTAMP, nullable=True)
    inspector = db.Column(db.String(20), nullable=True)
    lineno = db.Column(db.String(4), nullable=False)
