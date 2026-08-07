"""Line model — production lines managed by super_admin."""
from app.models import db


class Line(db.Model):
    __tablename__ = 'lines'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lineno     = db.Column(db.String(4), nullable=False, unique=True)
    name       = db.Column(db.String(50), nullable=False)
    is_active  = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False,
                           server_default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Line {self.lineno} ({self.name})>'
