from app.models import db

class INSP2(db.Model):
    __tablename__ = 'insp2'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    status = db.Column(db.String(12), nullable=False)
    inspector = db.Column(db.String(20), nullable=True)
    time = db.Column(db.TIMESTAMP, nullable=False)
    test_wiring_seq = db.Column(db.String(4), nullable=True)
    test_no_touching = db.Column(db.String(4), nullable=True)
    test_no_misaligned = db.Column(db.String(4), nullable=True)
    test_no_lacking = db.Column(db.String(4), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
