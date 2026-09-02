from . import db


class SPAMSIUniqueRef(db.Model):
    __tablename__ = 'spamsi_unique_refs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelcode = db.Column(db.String(14), nullable=False, unique=True)
    unique_code = db.Column(db.String(4), nullable=False, unique=True)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )
    updated_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=db.func.current_timestamp(),
        server_onupdate=db.func.current_timestamp(),
    )
