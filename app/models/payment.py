import uuid
from datetime import datetime, timezone
from app.extensions import db


class Payment(db.Model):
    """A payment record — registration, processing, visa, service, or ticket fees."""
    __tablename__ = "payments"

    PAYMENT_TYPES = ["registration", "processing", "document", "visa", "service", "ticket"]
    METHODS = ["telebirr", "cbe_birr", "bank_transfer", "cash"]
    STATUSES = ["pending", "completed", "failed", "refunded"]

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("applicants.id"), nullable=False)

    payment_type = db.Column(db.String(30), nullable=False)
    method = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default="ETB")
    status = db.Column(db.String(20), nullable=False, default="pending")

    receipt_number = db.Column(
        db.String(50), unique=True, default=lambda: f"ASM-{uuid.uuid4().hex[:8].upper()}"
    )
    transaction_ref = db.Column(db.String(100), nullable=True)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Payment {self.receipt_number} {self.amount}{self.currency} [{self.status}]>"
