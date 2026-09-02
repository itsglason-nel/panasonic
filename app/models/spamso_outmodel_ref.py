from . import db

class SpamsoOutmodelRef(db.Model):
    __tablename__ = 'spamso_outmodel_refs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False, unique=True)
    outmodel = db.Column(db.String(14), nullable=False)
    
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), server_onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'modelcode': self.modelcode,
            'outmodel': self.outmodel
        }
