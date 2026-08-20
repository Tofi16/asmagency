from datetime import datetime, timezone
from app.extensions import db


class Application(db.Model):
    """An applicant's application to one specific job posting."""
    __tablename__ = "applications"

    STATUSES = ["submitted", "under_review", "matched", "rejected", "withdrawn"]

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("applicants.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)

    status = db.Column(db.String(30), nullable=False, default="submitted")
    notes = db.Column(db.Text, nullable=True)

    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("applicant_id", "job_id", name="uq_applicant_job"),
    )

    def __repr__(self):
        return f"<Application applicant={self.applicant_id} job={self.job_id} [{self.status}]>"
