from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    """
    An outbound SMS/email notification record. `status` stays 'queued' until a
    real provider (e.g. Africa's Talking, SendGrid) is wired in — see README.
    """
    __tablename__ = "notifications"

    CHANNELS = ["sms", "email"]
    STATUSES = ["queued", "sent", "failed"]

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("applicants.id"), nullable=True)  # null = broadcast/bulk
    channel = db.Column(db.String(10), nullable=False, default="sms")
    message = db.Column(db.Text, nullable=False)
    audience_filter = db.Column(db.String(100), nullable=True)  # e.g. "all", "stage:matched"
    recipient_count = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), nullable=False, default="queued")
    sent_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    applicant = db.relationship("Applicant", backref="notifications")
    sender = db.relationship("User", foreign_keys=[sent_by])

    def __repr__(self):
        return f"<Notification {self.channel} to {self.recipient_count} [{self.status}]>"
