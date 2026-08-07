"""Module model — dynamic modules managed by super_admin."""
from app.models import db

class Module(db.Model):
    __tablename__ = 'modules'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name       = db.Column(db.String(50), nullable=False, unique=True)
    description= db.Column(db.String(255), nullable=True)
    is_active  = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False,
                           server_default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Module {self.name}>'
