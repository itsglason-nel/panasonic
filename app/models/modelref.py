from . import db
from .partref import PartRef

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
    
    op_current_base = db.Column(db.Numeric(4, 2), default=0)
    op_current_tolpos = db.Column(db.Numeric(4, 2), default=0)
    op_current_tolneg = db.Column(db.Numeric(4, 2), default=0)
    
    in_power_base = db.Column(db.Numeric(4, 2), default=0)
    in_power_tolpos = db.Column(db.Numeric(4, 2), default=0)
    in_power_tolneg = db.Column(db.Numeric(4, 2), default=0)
    
    temp_diff_base = db.Column(db.Numeric(4, 2), default=0)
    temp_diff_tolpos = db.Column(db.Numeric(4, 2), default=0)
    temp_diff_tolneg = db.Column(db.Numeric(4, 2), default=0)
    
    ritheat1 = db.Column(db.String(2), nullable=True)
    ritheat2 = db.Column(db.String(2), nullable=True)
    
    pittws = db.Column(db.String(2), nullable=True)
    
    spamsi_unique = db.Column(db.String(4), unique=True, nullable=True)
    
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), server_onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        # Outmodel is now sourced from partref with tag='Outdoor Control Board'
        outmodel_ref = PartRef.query.filter_by(
            modelcode=self.modelcode, module='SPAMSO', tag='Outdoor Control Board'
        ).first()
        
        # Gas charge base is sourced from partref with module='GMS'
        gms_ref = PartRef.query.filter_by(
            modelcode=self.modelcode, module='GMS'
        ).first()
        
        return {
            'id': self.id,
            'modelcode': self.modelcode,
            'area': self.area,
            'serialstart': self.serialstart,
            'spamsi_unique_code': self.spamsi_unique,
            'spamso_outmodel': outmodel_ref.partno if outmodel_ref else None,
            'gascharge_base': float(gms_ref.usage) if gms_ref and gms_ref.usage is not None else 0.00,
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
            'temp_diff_tolneg': float(self.temp_diff_tolneg) if self.temp_diff_tolneg is not None else 0,
            'ritheat1': self.ritheat1,
            'ritheat2': self.ritheat2,
            'pittws': self.pittws
        }
