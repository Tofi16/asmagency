import os
from flask import Flask, render_template, session

from config import config_by_name
from app.extensions import db, migrate, login_manager, csrf, bcrypt, cache, limiter


def create_app(config_name=None):
    """Application factory."""
    config_name = config_name or os.environ.get("FLASK_CONFIG", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    if hasattr(config_by_name[config_name], "init_app"):
        config_by_name[config_name].init_app(app)

    # --- Init extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "እባክዎ ለመቀጠል መጀመሪያ ይግቡ። / Please log in to continue."
    login_manager.login_message_category = "warning"

    # --- User loader (imported here to dodge circular imports) ---
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Register blueprints ---
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.applicant import applicant_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(applicant_bp, url_prefix="/applicant")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    # Vercel has no persistent local database. Bootstrap the temporary SQLite
    # fallback so the public app can serve requests without a configured DB.
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        from app import models  # noqa: F401
        with app.app_context():
            db.create_all()

    # --- Bilingual helper + globals available in every template ---
    @app.context_processor
    def inject_globals():
        def t(am_text, en_text):
            """Return am_text or en_text depending on the session language."""
            return en_text if session.get("lang") == "en" else am_text

        return {
            "t": t,
            "current_lang": session.get("lang", "am"),
            "company_name": app.config["COMPANY_NAME"],
            "company_phone": app.config["COMPANY_PHONE"],
            "company_email": app.config["COMPANY_EMAIL"],
            "company_address_am": app.config["COMPANY_ADDRESS_AM"],
            "company_address_en": app.config["COMPANY_ADDRESS_EN"],
        }

    # --- Error handlers ---
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # --- Make sure the upload folder exists ---
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app
