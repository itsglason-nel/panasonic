from app.models import db

class SPAMSI(db.Model):
    __tablename__ = 'spamsi'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14))
    serial = db.Column(db.String(14))
    inserial = db.Column(db.String(14))
    
    part1mod = db.Column(db.String(14))
    part1desc = db.Column(db.String(30))
    part1serial = db.Column(db.String(34))
    
    part2mod = db.Column(db.String(14))
    part2desc = db.Column(db.String(30))
    part2serial = db.Column(db.String(34))
    
    part3mod = db.Column(db.String(14))
    part3desc = db.Column(db.String(30))
    part3serial = db.Column(db.String(34))
    
    part4mod = db.Column(db.String(14))
    part4desc = db.Column(db.String(30))
    part4serial = db.Column(db.String(34))
    
    part5mod = db.Column(db.String(14))
    part5desc = db.Column(db.String(30))
    part5serial = db.Column(db.String(34))
    
    part6mod = db.Column(db.String(14))
    part6desc = db.Column(db.String(30))
    part6serial = db.Column(db.String(34))
    
    time = db.Column(db.TIMESTAMP)
    inspector = db.Column(db.String(20))
    lineno = db.Column(db.String(4))

    @property
    def status(self):
        return 'GOOD'
