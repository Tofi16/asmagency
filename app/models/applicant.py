from datetime import datetime, timezone
from app.extensions import db


class Applicant(db.Model):
    """Extended profile + pipeline state for a User with role='applicant'."""
    __tablename__ = "applicants"

    PIPELINE_STAGES = [
        "registered", "screening", "matched", "visa_processing",
        "contract", "travel_ready", "deployed",
    ]
    PIPELINE_LABELS_AM = {
        "registered": "ተመዝግቧል", "screening": "በማጣራት ላይ", "matched": "ከአሰሪ ጋር ተጣምሯል",
        "visa_processing": "የቪዛ ሂደት ላይ", "contract": "ውል ላይ", "travel_ready": "ለጉዞ ዝግጁ",
        "deployed": "ተሰማርቷል",
    }
    PIPELINE_LABELS_EN = {
        "registered": "Registered", "screening": "Screening", "matched": "Matched",
        "visa_processing": "Visa Processing", "contract": "Contract",
        "travel_ready": "Travel Ready", "deployed": "Deployed",
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    full_name = db.Column(db.String(150), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    passport_number = db.Column(db.String(50), unique=True, nullable=True)
    region = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    education_level = db.Column(db.String(100), nullable=True)
    work_experience = db.Column(db.Text, nullable=True)
    preferred_country = db.Column(db.String(100), nullable=True)
    preferred_job_category = db.Column(db.String(100), nullable=True)

    pipeline_status = db.Column(db.String(30), nullable=False, default="registered")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    documents = db.relationship(
        "Document", backref="applicant", lazy="dynamic", cascade="all, delete-orphan"
    )
    applications = db.relationship(
        "Application", backref="applicant", lazy="dynamic", cascade="all, delete-orphan"
    )
    payments = db.relationship(
        "Payment", backref="applicant", lazy="dynamic", cascade="all, delete-orphan"
    )

    def pipeline_progress_percent(self):
        if self.pipeline_status not in self.PIPELINE_STAGES:
            return 0
        idx = self.PIPELINE_STAGES.index(self.pipeline_status)
        return round((idx + 1) / len(self.PIPELINE_STAGES) * 100)

    def pipeline_label(self, lang="am"):
        labels = self.PIPELINE_LABELS_EN if lang == "en" else self.PIPELINE_LABELS_AM
        return labels.get(self.pipeline_status, self.pipeline_status)

    def __repr__(self):
        return f"<Applicant {self.full_name} [{self.pipeline_status}]>"
