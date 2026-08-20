"""Import every model so Flask-Migrate/Alembic can discover them via `flask db migrate`."""
from app.models.user import User
from app.models.applicant import Applicant
from app.models.document import Document
from app.models.employer import Employer
from app.models.job import Job
from app.models.application import Application
from app.models.payment import Payment
from app.models.partner import Partner
from app.models.cv_profile import CVProfile
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.interview import Interview
from app.models.review import Review

__all__ = [
    "User", "Applicant", "Document", "Employer", "Job",
    "Application", "Payment", "Partner", "CVProfile",
    "AuditLog", "Notification", "Interview", "Review",
]
