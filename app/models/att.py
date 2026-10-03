from app.models import db

class ATT(db.Model):
    __tablename__ = 'att'

    id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=True)
    serial    = db.Column(db.String(14), nullable=True)
    status1   = db.Column(db.String(12), nullable=True)   # No Clogged
    status2   = db.Column(db.String(12), nullable=True)   # No Leak
    status3   = db.Column(db.String(12), nullable=True)   # Exp Valve
    overallstatus = db.Column(db.String(12), nullable=True)
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
        """Computed overall status: GOOD only if all three sub-statuses are GOOD or PASS."""
        if self.overallstatus:
            return self.overallstatus
        vals = [self.status1, self.status2, self.status3]
        
        # If any sub-status explicitly fails, the whole unit fails.
        if any(v and v.upper() in ('NO GOOD', 'NG', 'FAIL', 'FAILED') for v in vals):
            return 'NO GOOD'
            
        # Filter out empty, N/A, and REVIEW values when checking for a clean sweep
        active_vals = [v for v in vals if v and v.upper() not in ('N/A', 'REVIEW', 'NONE', '-')]
        
        # If there is at least one passing value and no failing values, it is GOOD
        if active_vals and all(v.upper() in ('GOOD', 'PASS', 'OK') for v in active_vals):
            return 'GOOD'
            
        return 'PENDING'
