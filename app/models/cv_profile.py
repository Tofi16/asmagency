from datetime import datetime, timezone, date
from app.extensions import db


class CVProfile(db.Model):
    """
    The detailed, employer-facing CV/job-application sheet for one applicant —
    mirrors the standard agency CV format (bilingual EN/AR, passport info,
    languages, skills grid, work history, emergency contact).
    """
    __tablename__ = "cv_profiles"

    MARITAL_STATUSES = ["single", "married", "divorced", "widowed"]
    LANGUAGE_LEVELS = ["none", "fair", "good", "fluent"]
    SKILL_LEVELS = ["poor", "fair", "good", "excellent"]
    DEFAULT_LANGUAGES = ["Arabic", "English"]
    DEFAULT_SKILLS = ["Care of the Elderly", "Baby Sitting", "Cleaning", "Washing", "Cooking"]

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("applicants.id"), nullable=False, unique=True)
    partner_id = db.Column(db.Integer, db.ForeignKey("partners.id"), nullable=True)

    application_no = db.Column(db.String(20), unique=True)
    post_applied_for = db.Column(db.String(100))
    monthly_salary = db.Column(db.Numeric(10, 2))
    salary_currency = db.Column(db.String(10), default="USD")
    contract_period_years = db.Column(db.Integer)

    religion = db.Column(db.String(50))
    place_of_birth = db.Column(db.String(100))
    marital_status = db.Column(db.String(20))
    weight_kg = db.Column(db.Numeric(5, 1))
    height_m = db.Column(db.Numeric(3, 2))

    passport_issue_place = db.Column(db.String(100))
    passport_issue_date = db.Column(db.Date)
    passport_expiry_date = db.Column(db.Date)

    languages = db.Column(db.JSON, default=list)      # [{"language": "Arabic", "level": "fair"}, ...]
    skills = db.Column(db.JSON, default=list)          # [{"skill": "Cooking", "level": "good"}, ...]
    work_history = db.Column(db.JSON, default=list)    # [{"period": "2021-2023", "country": "UAE"}, ...]

    emergency_contact_name = db.Column(db.String(150))
    emergency_contact_address = db.Column(db.String(255))
    emergency_contact_phone = db.Column(db.String(30))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    applicant = db.relationship("Applicant", backref=db.backref("cv_profile", uselist=False))

    def age(self):
        dob = self.applicant.date_of_birth if self.applicant else None
        if not dob:
            return None
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def __repr__(self):
        return f"<CVProfile {self.application_no} for applicant_id={self.applicant_id}>"
