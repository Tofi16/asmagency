import uuid
from datetime import datetime, timezone
from app.extensions import db


class Document(db.Model):
    """An uploaded file (passport, education certificate, etc.) tied to an applicant."""
    __tablename__ = "documents"

    ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB, matches Config.MAX_CONTENT_LENGTH

    DOC_TYPES = ["photo_portrait", "photo_full", "passport", "education", "experience", "medical", "other"]
    DOC_TYPE_LABELS_AM = {
        "photo_portrait": "የቁም ፎቶ", "photo_full": "ጉርድ ፎቶ (ሙሉ ቁመት)", "passport": "የፓስፖርት ኮፒ",
        "education": "የትምህርት ማስረጃ", "experience": "የስራ ልምድ ማስረጃ", "medical": "የህክምና ማስረጃ", "other": "ሌላ",
    }
    DOC_TYPE_LABELS_EN = {
        "photo_portrait": "Portrait Photo", "photo_full": "Full-Length Photo", "passport": "Passport Copy",
        "education": "Education Certificate", "experience": "Experience Letter", "medical": "Medical Report", "other": "Other",
    }

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("applicants.id"), nullable=False)

    doc_type = db.Column(db.String(50), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(
        db.String(255), nullable=False, unique=True, default=lambda: uuid.uuid4().hex
    )
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|verified|rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    review_note = db.Column(db.String(500), nullable=True)

    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Document {self.doc_type} [{self.status}]>"
