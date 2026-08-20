from datetime import datetime, timezone
from app.extensions import db


class Review(db.Model):
    """A post-deployment rating — from the employer or logged by the agency."""
    __tablename__ = "reviews"

    REVIEWER_TYPES = ["employer", "agency"]

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("applicants.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.String(500), nullable=True)
    reviewer_type = db.Column(db.String(20), nullable=False, default="agency")
    logged_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    applicant = db.relationship("Applicant", backref="reviews")

    def __repr__(self):
        return f"<Review applicant={self.applicant_id} rating={self.rating}>"
