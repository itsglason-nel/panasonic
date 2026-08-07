from app.models import db

class Repair(db.Model):
    __tablename__ = 'repair'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    station_origin = db.Column(db.String(30), nullable=True)
    defect_type = db.Column(db.String(60), nullable=True)
    action_taken = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(12), nullable=False)
    inspector = db.Column(db.String(20), nullable=True)
    time = db.Column(db.TIMESTAMP, nullable=False)
    remarks = db.Column(db.Text, nullable=True)
