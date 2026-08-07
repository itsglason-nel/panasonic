from app.models import db

class ModelRef(db.Model):
    """Serial start reference — stores the serial prefix per model/area.
    area values: 'Domestic', 'HongKong', 'Export', 'Taiwan'
    serialstart: fixed prefix digits (e.g. '10277' for Export CW-HU70AA)
    """
    __tablename__ = 'modelref'

    id          = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    modelcode   = db.Column(db.String(14), nullable=True)
    area        = db.Column(db.String(14), nullable=True)
    serialstart = db.Column(db.String(6),  nullable=True)

