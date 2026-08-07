from app.models import db

class CRS(db.Model):
    __tablename__ = 'crs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    compmod = db.Column(db.String(14), nullable=False)
    compserial = db.Column(db.String(30), nullable=False)
    fan1mod = db.Column(db.String(14), nullable=True)
    fan1serial = db.Column(db.String(60), nullable=True)
    fan2mod = db.Column(db.String(14), nullable=True)   # optional — NULL if not present
    fan2serial = db.Column(db.String(60), nullable=True)
    part1mod = db.Column(db.String(14), nullable=True)
    part1desc = db.Column(db.String(30), nullable=True)
    part1serial = db.Column(db.String(34), nullable=True)
    part2mod = db.Column(db.String(14), nullable=True)
    part2desc = db.Column(db.String(30), nullable=True)
    part2serial = db.Column(db.String(34), nullable=True)
    part3mod = db.Column(db.String(14), nullable=True)
    part3desc = db.Column(db.String(30), nullable=True)
    part3serial = db.Column(db.String(34), nullable=True)
    part4mod = db.Column(db.String(14), nullable=True)
    part4desc = db.Column(db.String(30), nullable=True)
    part4serial = db.Column(db.String(34), nullable=True)
    time = db.Column(db.TIMESTAMP, nullable=False)
    inspector = db.Column(db.String(20), nullable=True)
    lineno = db.Column(db.String(4), nullable=False)
