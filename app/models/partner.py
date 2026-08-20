from datetime import datetime, timezone
from app.extensions import db


class Partner(db.Model):
    """A partner recruitment/placement agency abroad that candidates are placed through."""
    __tablename__ = "partners"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(150), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    cv_profiles = db.relationship("CVProfile", backref="partner", lazy="dynamic")

    def __repr__(self):
        return f"<Partner {self.name} ({self.country})>"
