from app.models import db

class INSP3Run(db.Model):
    __tablename__ = 'insp3_run'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False)
    serial = db.Column(db.String(14), nullable=False)
    status = db.Column(db.String(12), nullable=False)
    inspector = db.Column(db.String(20), nullable=True)
    time = db.Column(db.TIMESTAMP, nullable=False)
    insulation_resistance = db.Column(db.String(20), nullable=True)
    withstand_voltage = db.Column(db.String(20), nullable=True)
    leak_status = db.Column(db.String(10), nullable=True)
    leak_location = db.Column(db.String(60), nullable=True)
    prog_check_h = db.Column(db.String(20), nullable=True)
    prog_check_f = db.Column(db.String(20), nullable=True)
    airswing = db.Column(db.String(4), nullable=True)
    comp_operation = db.Column(db.String(4), nullable=True)
    fan_operation = db.Column(db.String(4), nullable=True)
    evap_tubes = db.Column(db.String(20), nullable=True)
    cond_tubes = db.Column(db.String(20), nullable=True)
    operating_current = db.Column(db.String(20), nullable=True)
    input_power = db.Column(db.String(20), nullable=True)
    temp_diff = db.Column(db.String(20), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
