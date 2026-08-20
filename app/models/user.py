from datetime import datetime, timezone, timedelta
import hashlib
import secrets
from flask_login import UserMixin
from app.extensions import db, bcrypt


class User(db.Model, UserMixin):
    """Login identity. Role decides whether this user is an applicant or an admin."""
    __tablename__ = "users"

    # Permission scopes an admin can be granted if they are not a super admin.
    PERMISSION_SCOPES = ["applicants", "documents", "cv", "jobs", "payments", "partners", "interviews", "reviews", "notifications"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=True)  # friendly display name, mainly for admin/staff accounts
    username = db.Column(db.String(50), unique=True, nullable=True, index=True)  # simple login handle, e.g. "tofik"
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="applicant")  # applicant | admin
    is_super_admin = db.Column(db.Boolean, default=False, nullable=False)  # full, unrestricted admin access
    permissions = db.Column(db.JSON, default=list)  # subset of PERMISSION_SCOPES, ignored if is_super_admin
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    reset_token_hash = db.Column(db.String(64), nullable=True, index=True)  # SHA-256 hex digest, never the raw token
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    applicant = db.relationship(
        "Applicant", backref="user", uselist=False, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def is_admin(self):
        return self.role == "admin"

    # --- Password reset ---
    RESET_TOKEN_TTL_MINUTES = 30

    def generate_reset_token(self):
        """Creates a one-time reset token. Returns the RAW token (put this in
        the email/link) while only its hash is stored in the database."""
        raw_token = secrets.token_urlsafe(32)
        self.reset_token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        self.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=self.RESET_TOKEN_TTL_MINUTES)
        return raw_token

    @staticmethod
    def verify_reset_token(raw_token):
        """Returns the matching User if the token is valid and unexpired, else None."""
        if not raw_token:
            return None
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        user = User.query.filter_by(reset_token_hash=token_hash).first()
        if not user or not user.reset_token_expires:
            return None
        expires = user.reset_token_expires
        if expires.tzinfo is None:  # SQLite stores naive datetimes
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            return None
        return user

    def clear_reset_token(self):
        self.reset_token_hash = None
        self.reset_token_expires = None

    def has_permission(self, scope):
        """Super admins can do everything; other admins need the scope explicitly granted."""
        if not self.is_admin():
            return False
        if self.is_super_admin:
            return True
        return scope in (self.permissions or [])

    # Flask-Login expects an `is_active` property/attribute
    @property
    def is_active(self):
        return self.is_active_account

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
