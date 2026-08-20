from flask import Blueprint

applicant_bp = Blueprint("applicant", __name__)

from app.blueprints.applicant import routes  # noqa: E402,F401


@applicant_bp.context_processor
def inject_applicant_nav_counts():
    from flask_login import current_user
    if current_user.is_authenticated and current_user.applicant:
        return {"pending_docs": current_user.applicant.documents.filter_by(status="pending").count()}
    return {}
