from app.models import db

class ATT(db.Model):
    __tablename__ = 'att'

    id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=True)
    serial    = db.Column(db.String(14), nullable=True)
    status1   = db.Column(db.String(12), nullable=True)   # No Clogged
    status2   = db.Column(db.String(12), nullable=True)   # No Leak
    status3   = db.Column(db.String(12), nullable=True)   # Exp Valve
    time      = db.Column(db.TIMESTAMP, nullable=True)
    inspector = db.Column(db.String(20), nullable=True)
    lineno    = db.Column(db.String(4), nullable=False)
    brazzer1  = db.Column(db.String(20), nullable=True)   # Condenser Prep
    brazzer2  = db.Column(db.String(20), nullable=True)   # Evaporator Prep
    brazzer3  = db.Column(db.String(20), nullable=True)   # Compressor Brazing
    brazzer4  = db.Column(db.String(20), nullable=True)   # Brazing 1
    brazzer5  = db.Column(db.String(20), nullable=True)   # Brazing 2
    brazzer6  = db.Column(db.String(20), nullable=True)   # Tube Crimping
    brazzer7  = db.Column(db.String(20), nullable=True)   # 4-Way Valve / Expansion

    @property
    def status(self):
        """Computed overall status: GOOD only if all three sub-statuses are GOOD."""
        vals = [self.status1, self.status2, self.status3]
        if all(v and v.upper() == 'GOOD' for v in vals):
            return 'GOOD'
        if any(v and v.upper() in ('NO GOOD', 'NG', 'FAIL') for v in vals):
            return 'NO GOOD'
        return 'PENDING'
