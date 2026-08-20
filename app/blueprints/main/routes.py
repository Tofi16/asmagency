from flask import render_template, redirect, url_for, session, request
from sqlalchemy import func
from app.blueprints.main import main_bp
from app.models.job import Job
from app.models.partner import Partner
from app.models.cv_profile import CVProfile
from app.models.applicant import Applicant


@main_bp.route("/")
def index():
    partners = Partner.query.filter_by(is_active=True).order_by(Partner.name).limit(6).all()

    country_rows = (
        Job.query.with_entities(Job.country, func.sum(Job.positions_available))
        .filter_by(is_active=True).group_by(Job.country)
        .order_by(func.sum(Job.positions_available).desc()).limit(8).all()
    )
    open_countries = [{"country": c, "positions": p or 0} for c, p in country_rows]

    return render_template("main/index.html", partners=partners, open_countries=open_countries)


@main_bp.route("/about")
def about():
    return render_template("main/about.html")


@main_bp.route("/services")
def services():
    return render_template("main/services.html")


@main_bp.route("/jobs")
def jobs():
    q = request.args.get("q", "").strip()
    country = request.args.get("country", "").strip()

    query = Job.query.filter_by(is_active=True)
    if q:
        query = query.filter(
            (Job.title_am.ilike(f"%{q}%")) | (Job.title_en.ilike(f"%{q}%"))
        )
    if country:
        query = query.filter_by(country=country)

    job_list = query.order_by(Job.posted_at.desc()).all()
    countries = [row[0] for row in Job.query.with_entities(Job.country).distinct()]
    return render_template("main/jobs.html", jobs=job_list, q=q, country=country, countries=countries)


@main_bp.route("/contact")
def contact():
    return render_template("main/contact.html")


@main_bp.route("/faq")
def faq():
    return render_template("main/faq.html")


@main_bp.route("/how-it-works")
def how_it_works():
    return render_template("main/how_it_works.html")


@main_bp.route("/document-checklist")
def document_checklist():
    return render_template("main/checklist.html")


@main_bp.route("/verify/<application_no>")
def verify_cv(application_no):
    profile = CVProfile.query.filter_by(application_no=application_no).first()
    return render_template("main/verify.html", profile=profile, application_no=application_no)


@main_bp.route("/set-language/<lang>")
def set_language(lang):
    if lang in ("am", "en"):
        session["lang"] = lang
    return redirect(request.referrer or url_for("main.index"))
