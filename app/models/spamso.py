from app.models import db

class SPAMSO(db.Model):
    __tablename__ = 'spamso'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14))
    serial = db.Column(db.String(14))
    outmodel = db.Column(db.String(14))
    outserial = db.Column(db.String(30))
    
    part1mod = db.Column(db.String(14))
    part1desc = db.Column(db.String(30))
    part1serial = db.Column(db.String(34))
    
    part2mod = db.Column(db.String(14))
    part2desc = db.Column(db.String(30))
    part2serial = db.Column(db.String(34))
    
    part3mod = db.Column(db.String(14))
    part3desc = db.Column(db.String(30))
    part3serial = db.Column(db.String(34))
    
    time = db.Column(db.TIMESTAMP)
    inspector = db.Column(db.String(20))
    lineno = db.Column(db.String(4))

    @property
    def status(self):
        return 'GOOD'
