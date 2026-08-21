import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-this-before-deploying")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads ---
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(basedir, "app", "static", "uploads")
    )
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5MB

    # --- Session / cookies ---
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"

    # --- Rate limiting ---
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    # --- Caching ---
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = 300

    # --- Company info (used across templates) ---
    COMPANY_NAME = "ASM Foreign Employment Agency"
    COMPANY_PHONE = "+251979104070"
    COMPANY_EMAIL = "asmagency5@gmail.com"
    COMPANY_ADDRESS_AM = "አዲስ አበባ፣ አየርጤና፣ ግራር አየለ ህንፃ፣ 3ኛ ፎቅ"
    COMPANY_ADDRESS_EN = "Addis Ababa, Ayertena, Grar Ayele Building, 3rd Floor"


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "dev.db")
    )


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_PRISMA_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("POSTGRES_URL_NON_POOLING")
    )
    SESSION_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        database_url = app.config.get("SQLALCHEMY_DATABASE_URI")
        if database_url and database_url.startswith("postgres://"):
            app.config["SQLALCHEMY_DATABASE_URI"] = database_url.replace(
                "postgres://", "postgresql://", 1
            )
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL or a Vercel Postgres URL variable must be set in production"
            )
        if os.environ.get("SECRET_KEY", "dev-key-change-this-before-deploying") == "dev-key-change-this-before-deploying":
            raise RuntimeError("SECRET_KEY must be overridden in production")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
