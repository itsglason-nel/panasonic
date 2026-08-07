from app.models import db

class PartRef(db.Model):
    """BOM parts reference — formerly mapped to `modelref`, now `partref`."""
    __tablename__ = 'partref'

    id        = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    module    = db.Column(db.String(8),  nullable=False)
    partno    = db.Column(db.String(14), nullable=False)
    partdesc  = db.Column(db.String(60), nullable=False)
    usage     = db.Column(db.Float,      nullable=False)
    tag       = db.Column(db.String(14), nullable=False)
