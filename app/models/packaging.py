from sqlalchemy import Integer, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from app.models import db
from datetime import datetime

class Packaging(db.Model):
    __tablename__ = 'packaging'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    modelcode: Mapped[str | None] = mapped_column(String(14))
    serial: Mapped[str | None] = mapped_column(String(14))
    status1: Mapped[str | None] = mapped_column(String(12))
    status2: Mapped[str | None] = mapped_column(String(12))
    status3: Mapped[str | None] = mapped_column(String(12))
    status4: Mapped[str | None] = mapped_column(String(12))
    time: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    inspector: Mapped[str | None] = mapped_column(String(20))
    lineno: Mapped[str] = mapped_column(String(4), nullable=False)

    @property
    def status(self):
        statuses = [self.status1, self.status2, self.status3, self.status4]
        if any(s in ['NG', 'NO GOOD'] for s in statuses if s):
            return 'NG'
        if all(s == 'GOOD' for s in statuses if s):
            return 'GOOD'
        return 'PENDING'

    def to_dict(self):
        return {
            'id': self.id,
            'modelcode': self.modelcode,
            'serial': self.serial,
            'status1': self.status1,
            'status2': self.status2,
            'status3': self.status3,
            'status4': self.status4,
            'time': self.time.strftime('%Y-%m-%d %H:%M:%S') if self.time else None,
            'inspector': self.inspector,
            'lineno': self.lineno
        }
