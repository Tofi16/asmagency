from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    """Who did what, when — for compliance and internal accountability."""
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)          # e.g. "document.verify", "payment.status_change"
    target_type = db.Column(db.String(50), nullable=True)       # e.g. "Document", "Applicant"
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    actor = db.relationship("User", foreign_keys=[actor_id])

    def __repr__(self):
        return f"<AuditLog {self.action} by user={self.actor_id} at {self.created_at}>"
