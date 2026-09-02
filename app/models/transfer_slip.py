from app.models import db
import datetime

class TransferSlip(db.Model):
    __tablename__ = 'transfer_slips'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ref_number = db.Column(db.String(20), unique=True, nullable=False)
    production_date = db.Column(db.Date, nullable=False)
    line = db.Column(db.String(10), nullable=False)
    shift = db.Column(db.String(10), nullable=False)
    modelcode = db.Column(db.String(20), nullable=False)
    total_qty = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.String(50), nullable=True)
    time = db.Column(db.TIMESTAMP, default=datetime.datetime.now)
    serials_json = db.Column(db.Text, nullable=False) # JSON array of serial strings
