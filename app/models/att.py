from app.models import db

class ATT(db.Model):
    __tablename__ = 'att'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    status = db.Column(db.String(12), nullable=False)
    time = db.Column(db.TIMESTAMP, nullable=False)
    inspector = db.Column(db.String(20), nullable=True)
    lineno = db.Column(db.String(4), nullable=False)
    test_no_clogged = db.Column(db.String(4), nullable=True)
    test_no_leak = db.Column(db.String(4), nullable=True)
    test_exp_valve = db.Column(db.String(4), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
