from . import db
from .spamsi_unique_ref import SPAMSIUniqueRef
from .spamso_outmodel_ref import SpamsoOutmodelRef

class ModelRef(db.Model):
    __tablename__ = 'modelref'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False, unique=True)
    
    area = db.Column(db.String(14), nullable=True)
    serialstart = db.Column(db.String(6), nullable=True)
    
    program_h = db.Column(db.String(6), nullable=True)
    program_f = db.Column(db.String(6), nullable=True)
    
    gmstolpos = db.Column(db.Numeric(4, 2), default=0)
    gmstolneg = db.Column(db.Numeric(4, 2), default=0)
    
    op_current_base = db.Column(db.Numeric(8, 2), default=0)
    op_current_tolpos = db.Column(db.Numeric(2, 0), default=0)
    op_current_tolneg = db.Column(db.Numeric(2, 0), default=0)
    
    in_power_base = db.Column(db.Numeric(8, 2), default=0)
    in_power_tolpos = db.Column(db.Numeric(2, 0), default=0)
    in_power_tolneg = db.Column(db.Numeric(2, 0), default=0)
    
    temp_diff_base = db.Column(db.Numeric(8, 2), default=0)
    temp_diff_tolpos = db.Column(db.Numeric(2, 0), default=0)
    temp_diff_tolneg = db.Column(db.Numeric(2, 0), default=0)
    
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), server_onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        # Query for SPAMSI unique code, which is stored in a separate reference table.
        spamsi_ref = SPAMSIUniqueRef.query.filter_by(modelcode=self.modelcode).first()
        spamso_ref = SpamsoOutmodelRef.query.filter_by(modelcode=self.modelcode).first()
        
        return {
            'id': self.id,
            'modelcode': self.modelcode,
            'area': self.area,
            'serialstart': self.serialstart,
            'spamsi_unique_code': spamsi_ref.unique_code if spamsi_ref else None,
            'spamso_outmodel': spamso_ref.outmodel if spamso_ref else None,
            'program_h': self.program_h,
            'program_f': self.program_f,
            'gmstolpos': float(self.gmstolpos) if self.gmstolpos is not None else 0,
            'gmstolneg': float(self.gmstolneg) if self.gmstolneg is not None else 0,
            'op_current_base': float(self.op_current_base) if self.op_current_base is not None else 0,
            'op_current_tolpos': float(self.op_current_tolpos) if self.op_current_tolpos is not None else 0,
            'op_current_tolneg': float(self.op_current_tolneg) if self.op_current_tolneg is not None else 0,
            'in_power_base': float(self.in_power_base) if self.in_power_base is not None else 0,
            'in_power_tolpos': float(self.in_power_tolpos) if self.in_power_tolpos is not None else 0,
            'in_power_tolneg': float(self.in_power_tolneg) if self.in_power_tolneg is not None else 0,
            'temp_diff_base': float(self.temp_diff_base) if self.temp_diff_base is not None else 0,
            'temp_diff_tolpos': float(self.temp_diff_tolpos) if self.temp_diff_tolpos is not None else 0,
            'temp_diff_tolneg': float(self.temp_diff_tolneg) if self.temp_diff_tolneg is not None else 0
        }
