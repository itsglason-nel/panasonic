from app.models import db

class GMS(db.Model):
    __tablename__ = 'gms'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    gascharge = db.Column(db.Numeric(4, 2), nullable=False)
    status = db.Column(db.String(12), nullable=False)
    time = db.Column(db.TIMESTAMP, nullable=False)
    inspector = db.Column(db.String(20), nullable=True)
    lineno = db.Column(db.String(4), nullable=False, default='L1')
