from app.models import db

class WorkSched(db.Model):
    __tablename__ = 'worksched'

    id           = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    lineno       = db.Column(db.String(4),   nullable=False)
    seq          = db.Column(db.SmallInteger, nullable=False)
    modelcode    = db.Column(db.String(14),  nullable=False)
    plan         = db.Column(db.Integer,     nullable=False)
    act          = db.Column(db.Integer,     nullable=False)
    takttime     = db.Column(db.Integer,     nullable=False)
    date         = db.Column(db.Date,        nullable=False, server_default=db.text('(CURRENT_DATE)'))

    # ── Finalization (scoreboard history log) ──────────────────────────────────
    finalized    = db.Column(db.Boolean,     nullable=False, default=False)
    finalized_at = db.Column(db.DateTime,    nullable=True)
    finalized_by = db.Column(db.String(50),  nullable=True)

    # ── Database-level uniqueness — prevents duplicates even under race conditions ──
    __table_args__ = (
        db.UniqueConstraint('lineno', 'date', 'modelcode', name='uq_worksched_line_date_model'),
    )


