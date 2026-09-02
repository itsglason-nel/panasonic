from app.models import db
from datetime import time

class Shift(db.Model):
    __tablename__ = 'shifts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    @property
    def is_overnight(self):
        if self.start_time and self.end_time:
            return self.end_time < self.start_time
        return False
        
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_time': self.start_time.strftime('%H:%M:%S') if self.start_time else '',
            'end_time': self.end_time.strftime('%H:%M:%S') if self.end_time else '',
            'is_overnight': self.is_overnight
        }
