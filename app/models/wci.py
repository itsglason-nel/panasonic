from app.models import db

class WCI(db.Model):
    __tablename__ = 'wci'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    status1 = db.Column(db.String(12), nullable=False)
    status2 = db.Column(db.String(12), nullable=False)
    status3 = db.Column(db.String(12), nullable=False)
    status4 = db.Column(db.String(12), nullable=False)
    status5 = db.Column(db.String(12), nullable=True)
    status6 = db.Column(db.String(12), nullable=True)
    status7 = db.Column(db.String(12), nullable=True)
    overallstatus = db.Column(db.String(12), nullable=True)
    inspector = db.Column(db.String(20), nullable=True)
    time = db.Column(db.TIMESTAMP, nullable=False)
    lineno = db.Column(db.String(4), nullable=True)
