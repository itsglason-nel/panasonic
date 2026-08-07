from app.models import db

class SPAMS(db.Model):
    __tablename__ = 'spams'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    status = db.Column(db.String(12), nullable=False)
    inspector = db.Column(db.String(20), nullable=True)
    time = db.Column(db.TIMESTAMP, nullable=False)
    remarks = db.Column(db.Text, nullable=True)
