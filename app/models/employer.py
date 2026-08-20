from datetime import datetime, timezone
from app.extensions import db


class Employer(db.Model):
    """An overseas employer that posts jobs through the agency."""
    __tablename__ = "employers"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=True)
    contact_person = db.Column(db.String(150), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(30), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    jobs = db.relationship("Job", backref="employer", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employer {self.company_name} ({self.country})>"
