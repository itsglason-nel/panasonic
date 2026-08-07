from app.models import db
import json
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # CREATE, UPDATE, DELETE
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)  # JSON string of changes
    timestamp = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<AuditLog {self.action} on {self.table_name}:{self.record_id} by {self.username}>'

def log_audit(username, action, table_name, record_id, details=None):
    """Helper function to create an audit log entry."""
    try:
        if isinstance(details, dict) or isinstance(details, list):
            details = json.dumps(details)
            
        log = AuditLog(
            username=username,
            action=action,
            table_name=table_name,
            record_id=str(record_id),
            details=details,
            timestamp=datetime.now()
        )
        db.session.add(log)
    except Exception as e:
        print(f"Failed to write audit log: {e}")
