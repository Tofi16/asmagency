from flask import jsonify
from app.blueprints.api import api_bp
from app.models.job import Job


@api_bp.route("/jobs")
def list_jobs():
    jobs = Job.query.filter_by(is_active=True).order_by(Job.posted_at.desc()).all()
    return jsonify([
        {
            "id": j.id,
            "title_am": j.title_am,
            "title_en": j.title_en,
            "country": j.country,
            "category": j.category,
            "positions_available": j.positions_available,
            "employer": j.employer.company_name,
        }
        for j in jobs
    ])


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok"})
