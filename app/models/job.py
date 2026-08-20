from datetime import datetime, timezone
from app.extensions import db


class Job(db.Model):
    """A job opening. Bilingual fields per the brief's dual-content DB strategy."""
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("employers.id"), nullable=False)

    title_am = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    description_am = db.Column(db.Text, nullable=True)
    description_en = db.Column(db.Text, nullable=True)

    category = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=False)
    salary_amount = db.Column(db.Numeric(10, 2), nullable=True)
    salary_currency = db.Column(db.String(10), default="USD")
    positions_available = db.Column(db.Integer, default=1)
    contract_duration_months = db.Column(db.Integer, nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    posted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    closes_at = db.Column(db.DateTime, nullable=True)

    applications = db.relationship("Application", backref="job", lazy="dynamic")

    def title(self, lang="am"):
        return self.title_en if lang == "en" else self.title_am

    def description(self, lang="am"):
        return self.description_en if lang == "en" else self.description_am

    def __repr__(self):
        return f"<Job {self.title_en} @ {self.country}>"
