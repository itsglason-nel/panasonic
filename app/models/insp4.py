from app.models import db

class INSP4(db.Model):
    __tablename__ = 'insp4'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    status = db.Column(db.String(12), nullable=False)
    inspector = db.Column(db.String(20), nullable=True)
    time = db.Column(db.TIMESTAMP, nullable=False)
    insulation_resistance = db.Column(db.String(20), nullable=True)
    operating_current = db.Column(db.String(20), nullable=True)
    nameplate_match = db.Column(db.String(4), nullable=True)
    model_label = db.Column(db.String(4), nullable=True)
    manual_remote = db.Column(db.String(4), nullable=True)
    manual_warranty = db.Column(db.String(4), nullable=True)
    manual_screws = db.Column(db.String(4), nullable=True)
    grille_eel = db.Column(db.String(4), nullable=True)
    grille_model = db.Column(db.String(4), nullable=True)
    grille_logo = db.Column(db.String(4), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
