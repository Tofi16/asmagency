from datetime import datetime, timezone
from app.extensions import db


class Interview(db.Model):
    """A scheduled interview between an applicant and an employer/partner."""
    __tablename__ = "interviews"

    MODES = ["video", "phone", "in_person"]
    STATUSES = ["scheduled", "completed", "cancelled", "no_show"]

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("applicants.id"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    mode = db.Column(db.String(20), nullable=False, default="video")
    status = db.Column(db.String(20), nullable=False, default="scheduled")
    notes = db.Column(db.String(500), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    applicant = db.relationship("Applicant", backref="interviews")

    def __repr__(self):
        return f"<Interview applicant={self.applicant_id} at {self.scheduled_at} [{self.status}]>"
