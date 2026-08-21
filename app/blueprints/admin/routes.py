import os
import uuid
from datetime import date, datetime

from flask import render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app.blueprints.admin import admin_bp
from app.extensions import db
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
from app.utils.decorators import admin_required, permission_required, super_admin_required
from app.utils.audit import log_action
from app.utils.cv_docx import build_cv_docx
from app.utils.storage import UploadStorageError, save_upload


def _shift_month(dt, n):
    """Return the first of the month that is n months after dt (n may be negative)."""
    month = dt.month - 1 + n
    year = dt.year + month // 12
    month = month % 12 + 1
    return dt.replace(year=year, month=month, day=1)


@admin_bp.context_processor
def inject_admin_shared():
    """Available on every admin page: pending-doc badge count + a nav visibility helper."""
    if not (current_user.is_authenticated and current_user.is_admin()):
        return {}
    return {
        "pending_docs_count": Document.query.filter_by(status="pending").count(),
        "can": current_user.has_permission,  # use in templates as {% if can('documents') %}
    }


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    stats = {
        "total_users": User.query.filter_by(role="applicant").count(),
        "pending_docs": Document.query.filter_by(status="pending").count(),
        "deployed_total": Applicant.query.filter_by(pipeline_status="deployed").count(),
        "revenue_total": db.session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.status == "completed").scalar(),
    }
    pipeline_counts = dict(
        db.session.query(Applicant.pipeline_status, func.count(Applicant.id))
        .group_by(Applicant.pipeline_status).all()
    )

    # --- Chart 1: new registrations per month, last 6 months (portable across SQLite/Postgres) ---
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month_starts = [_shift_month(today, -i) for i in range(5, -1, -1)]
    month_labels = [m.strftime("%b") for m in month_starts]
    month_counts = [0] * 6

    created_dates = [row[0] for row in db.session.query(Applicant.created_at).all()]
    for created_at in created_dates:
        for i in range(6):
            start = month_starts[i]
            end = month_starts[i + 1] if i + 1 < 6 else _shift_month(month_starts[-1], 1)
            if start <= created_at < end:
                month_counts[i] += 1
                break

    # --- Chart 2: deployed applicants by destination country ---
    country_rows = (
        db.session.query(Job.country, func.count(func.distinct(Applicant.id)))
        .join(Application, Application.job_id == Job.id)
        .join(Applicant, Applicant.id == Application.applicant_id)
        .filter(Applicant.pipeline_status == "deployed")
        .group_by(Job.country)
        .order_by(func.count(func.distinct(Applicant.id)).desc())
        .all()
    )
    country_labels = [r[0] for r in country_rows]
    country_counts = [r[1] for r in country_rows]

    return render_template(
        "admin/dashboard.html", stats=stats, pipeline_counts=pipeline_counts,
        stages=Applicant.PIPELINE_STAGES,
        month_labels=month_labels, month_counts=month_counts,
        country_labels=country_labels, country_counts=country_counts,
    )


@admin_bp.route("/applicants")
@login_required
@admin_required
@permission_required("applicants")
def applicants():
    all_applicants = Applicant.query.order_by(Applicant.created_at.desc()).all()
    review_avgs = dict(
        db.session.query(Review.applicant_id, func.avg(Review.rating))
        .group_by(Review.applicant_id).all()
    )
    return render_template("admin/applicants.html", applicants=all_applicants,
                            stages=Applicant.PIPELINE_STAGES, review_avgs=review_avgs)


@admin_bp.route("/applicants/<int:applicant_id>/advance", methods=["POST"])
@login_required
@admin_required
@permission_required("applicants")
def advance_pipeline(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    new_status = request.form.get("status")
    if new_status in Applicant.PIPELINE_STAGES:
        old_status = applicant.pipeline_status
        applicant.pipeline_status = new_status
        log_action("applicant.pipeline_advance", "Applicant", applicant.id,
                   f"{old_status} -> {new_status}")
        db.session.commit()
        flash("የማመልከቻ ደረጃ ተሻሽሏል። / Pipeline stage updated.", "success")
    return redirect(url_for("admin.applicants"))


@admin_bp.route("/documents")
@login_required
@admin_required
@permission_required("documents")
def documents():
    pending = Document.query.filter_by(status="pending").order_by(Document.uploaded_at.asc()).all()
    return render_template(
        "admin/documents.html", documents=pending,
        doc_labels_am=Document.DOC_TYPE_LABELS_AM, doc_labels_en=Document.DOC_TYPE_LABELS_EN,
    )


@admin_bp.route("/documents/<int:doc_id>/verify", methods=["POST"])
@login_required
@admin_required
@permission_required("documents")
def verify_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    action = request.form.get("action")
    doc.status = "verified" if action == "approve" else "rejected"
    log_action("document.verify", "Document", doc.id, f"action={action}")
    db.session.commit()
    flash("ሰነድ ሁኔታ ተስተካክሏል። / Document status updated.", "success")
    return redirect(url_for("admin.documents"))


@admin_bp.route("/jobs", methods=["GET", "POST"])
@login_required
@admin_required
@permission_required("jobs")
def jobs():
    if request.method == "POST":
        employer_id = request.form.get("employer_id")
        employer = Employer.query.get(employer_id) if employer_id else None
        if not employer:
            flash("እባክዎ አሰሪ ይምረጡ። / Please choose an employer.", "danger")
            return redirect(url_for("admin.jobs"))

        job = Job(
            employer_id=employer.id,
            title_am=request.form.get("title_am", "").strip(),
            title_en=request.form.get("title_en", "").strip(),
            country=request.form.get("country", "").strip(),
            category=request.form.get("category", "").strip() or None,
            positions_available=int(request.form.get("positions_available") or 1),
        )
        db.session.add(job)
        db.session.flush()
        log_action("job.create", "Job", job.id, job.title_en)
        db.session.commit()
        flash("አዲስ የስራ ማስታወቂያ ተጨምሯል። / New job posting added.", "success")
        return redirect(url_for("admin.jobs"))

    all_jobs = Job.query.order_by(Job.posted_at.desc()).all()
    employers = Employer.query.order_by(Employer.company_name).all()
    return render_template("admin/jobs.html", jobs=all_jobs, employers=employers)


@admin_bp.route("/payments")
@login_required
@admin_required
@permission_required("payments")
def payments():
    all_payments = Payment.query.order_by(Payment.created_at.desc()).all()
    return render_template("admin/payments.html", payments=all_payments)


@admin_bp.route("/finance")
@login_required
@admin_required
@permission_required("payments")
def finance():
    by_type = dict(
        db.session.query(Payment.payment_type, func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.status == "completed").group_by(Payment.payment_type).all()
    )
    outstanding = (
        db.session.query(Applicant, func.coalesce(func.sum(Payment.amount), 0))
        .join(Payment, Payment.applicant_id == Applicant.id)
        .filter(Payment.status == "pending")
        .group_by(Applicant.id)
        .all()
    )
    total_completed = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == "completed").scalar()
    total_pending = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == "pending").scalar()

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month_starts = [_shift_month(today, -i) for i in range(5, -1, -1)]
    month_labels = [m.strftime("%b") for m in month_starts]
    month_totals = [0] * 6
    paid_rows = db.session.query(Payment.paid_at, Payment.amount).filter(Payment.status == "completed", Payment.paid_at.isnot(None)).all()
    for paid_at, amount in paid_rows:
        for i in range(6):
            start = month_starts[i]
            end = month_starts[i + 1] if i + 1 < 6 else _shift_month(month_starts[-1], 1)
            if start <= paid_at < end:
                month_totals[i] += float(amount)
                break

    return render_template(
        "admin/finance.html", by_type=by_type, outstanding=outstanding,
        total_completed=total_completed, total_pending=total_pending,
        month_labels=month_labels, month_totals=month_totals,
    )


# ---------------------------------------------------------------------------
# CV Builder — professional employer-facing candidate CV sheet
# ---------------------------------------------------------------------------

def _next_application_no():
    last = CVProfile.query.order_by(CVProfile.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"{next_num:05d}"


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


# The 3 photo slots a CV needs for a professional, employer-ready look.
# Keys are the <input name="..."> in cv_form.html; values are the Document.doc_type
# they map to (passport reuses the same doc_type as the general "Passport Copy"
# upload on the applicant's own dashboard — see _save_cv_photo).
CV_PHOTO_FIELDS = {
    "photo_portrait": "photo_portrait",  # small ID/portrait photo
    "photo_full": "photo_full",          # full-length photo
    "photo_passport": "passport",        # passport bio-page scan
}


def _save_cv_photo(applicant, doc_type, file):
    """Save (or replace) one admin-uploaded CV photo. Returns (Document, error_message).

    Unlike self-service applicant uploads (Document.status starts 'pending'
    until admin review), a photo an admin attaches directly here is auto-marked
    'verified' — the admin choosing the file *is* the review."""
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in Document.ALLOWED_EXTENSIONS:
        return None, "የማይፈቀድ የፋይል አይነት (jpg, png, pdf ብቻ)። / File type not allowed (jpg, png, pdf only)."

    try:
        stored_name, file_path, file_size = save_upload(file, folder="asm-agency/cv")
    except UploadStorageError as exc:
        return None, str(exc)

    # Replace the existing photo of this type in place — a CV should show
    # only its current photo, not pile up old ones every time it's edited.
    existing = (
        applicant.documents.filter_by(doc_type=doc_type)
        .order_by(Document.uploaded_at.desc()).first()
    )
    old_path = existing.file_path if existing else None

    if existing:
        doc = existing
    else:
        doc = Document(applicant_id=applicant.id, doc_type=doc_type)
        db.session.add(doc)

    doc.original_filename = secure_filename(file.filename)
    doc.stored_filename = stored_name
    doc.file_path = file_path
    doc.file_size = file_size
    doc.status = "verified"
    doc.reviewed_by = current_user.id
    doc.reviewed_at = datetime.utcnow()
    doc.uploaded_at = datetime.utcnow()

    if old_path and old_path != file_path and os.path.exists(old_path):
        try:
            os.remove(old_path)
        except OSError:
            pass  # stale file left on disk is a minor cleanup issue, not worth failing the request over

    return doc, None


@admin_bp.route("/cv")
@login_required
@admin_required
@permission_required("cv")
def cv_list():
    profiles = (
        CVProfile.query.join(Applicant)
        .order_by(func.lower(Applicant.full_name))
        .all()
    )
    applicants_without_cv = (
        Applicant.query.filter(~Applicant.id.in_(
            db.session.query(CVProfile.applicant_id)
        )).order_by(func.lower(Applicant.full_name)).all()
    )
    return render_template("admin/cv_list.html", profiles=profiles, applicants_without_cv=applicants_without_cv)


@admin_bp.route("/cv/<int:applicant_id>", methods=["GET", "POST"])
@login_required
@admin_required
@permission_required("cv")
def cv_form(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    profile = applicant.cv_profile

    if request.method == "POST":
        is_new = profile is None
        if profile is None:
            profile = CVProfile(applicant_id=applicant.id, application_no=_next_application_no())
            db.session.add(profile)

        # --- photos (Small ID, Full-length, Passport scan) — all optional; only
        #     replace a slot if a new file was actually chosen this submit ---
        photo_errors = []
        for field_name, doc_type in CV_PHOTO_FIELDS.items():
            file = request.files.get(field_name)
            if file and file.filename:
                _doc, err = _save_cv_photo(applicant, doc_type, file)
                if err:
                    photo_errors.append(err)
        for err in photo_errors:
            flash(err, "danger")

        # --- application info ---
        profile.post_applied_for = request.form.get("post_applied_for", "").strip()
        profile.monthly_salary = request.form.get("monthly_salary") or None
        profile.salary_currency = request.form.get("salary_currency", "USD")
        profile.contract_period_years = request.form.get("contract_period_years") or None
        partner_id = request.form.get("partner_id")
        profile.partner_id = int(partner_id) if partner_id else None

        # --- personal info (some fields live on Applicant, some on CVProfile) ---
        applicant.full_name = request.form.get("full_name", applicant.full_name).strip()
        dob = _parse_date(request.form.get("date_of_birth"))
        if dob:
            applicant.date_of_birth = dob
        applicant.gender = request.form.get("gender") or applicant.gender
        applicant.passport_number = request.form.get("passport_number") or applicant.passport_number
        applicant.education_level = request.form.get("education_level") or applicant.education_level

        profile.religion = request.form.get("religion", "").strip() or None
        profile.place_of_birth = request.form.get("place_of_birth", "").strip() or None
        profile.marital_status = request.form.get("marital_status") or None
        profile.weight_kg = request.form.get("weight_kg") or None
        profile.height_m = request.form.get("height_m") or None

        # --- passport details ---
        profile.passport_issue_place = request.form.get("passport_issue_place", "").strip() or None
        profile.passport_issue_date = _parse_date(request.form.get("passport_issue_date"))
        profile.passport_expiry_date = _parse_date(request.form.get("passport_expiry_date"))

        # --- languages (fixed rows submitted as language_<name>) ---
        languages = []
        for lang in CVProfile.DEFAULT_LANGUAGES:
            level = request.form.get(f"language_{lang.lower()}")
            if level and level != "none":
                languages.append({"language": lang, "level": level})
        profile.languages = languages

        # --- skills grid ---
        skills = []
        for skill in CVProfile.DEFAULT_SKILLS:
            key = skill.lower().replace(" ", "_")
            level = request.form.get(f"skill_{key}")
            if level:
                skills.append({"skill": skill, "level": level})
        profile.skills = skills

        # --- work history (up to 5 rows) ---
        history = []
        for i in range(1, 6):
            period = request.form.get(f"history_period_{i}", "").strip()
            country = request.form.get(f"history_country_{i}", "").strip()
            if period or country:
                history.append({"period": period, "country": country})
        profile.work_history = history

        # --- emergency contact ---
        profile.emergency_contact_name = request.form.get("emergency_contact_name", "").strip() or None
        profile.emergency_contact_address = request.form.get("emergency_contact_address", "").strip() or None
        profile.emergency_contact_phone = request.form.get("emergency_contact_phone", "").strip() or None

        db.session.flush()
        log_action("cv.create" if is_new else "cv.update", "CVProfile", profile.id, applicant.full_name)
        db.session.commit()
        flash("የCV መገለጫ ተቀምጧል። / CV profile saved.", "success")
        return redirect(url_for("admin.cv_form", applicant_id=applicant.id))

    partners = Partner.query.filter_by(is_active=True).order_by(Partner.name).all()
    portrait_doc = applicant.documents.filter_by(doc_type="photo_portrait").order_by(Document.uploaded_at.desc()).first()
    full_doc = applicant.documents.filter_by(doc_type="photo_full").order_by(Document.uploaded_at.desc()).first()
    passport_doc = applicant.documents.filter_by(doc_type="passport").order_by(Document.uploaded_at.desc()).first()
    return render_template(
        "admin/cv_form.html", applicant=applicant, profile=profile, partners=partners,
        portrait_doc=portrait_doc, full_doc=full_doc, passport_doc=passport_doc,
    )


@admin_bp.route("/cv/<int:applicant_id>/print")
@login_required
@admin_required
@permission_required("cv")
def cv_print(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    profile = applicant.cv_profile
    if profile is None:
        flash("እባክዎ መጀመሪያ የCV መገለጫ ይሙሉ። / Please fill in the CV profile first.", "warning")
        return redirect(url_for("admin.cv_form", applicant_id=applicant.id))

    portrait_doc = applicant.documents.filter_by(doc_type="photo_portrait", status="verified").first()
    full_doc = applicant.documents.filter_by(doc_type="photo_full", status="verified").first()
    passport_doc = applicant.documents.filter_by(doc_type="passport", status="verified").first()
    verify_url = url_for("main.verify_cv", application_no=profile.application_no, _external=True)
    return render_template(
        "admin/cv_print.html", applicant=applicant, profile=profile,
        portrait_doc=portrait_doc, full_doc=full_doc, passport_doc=passport_doc,
        verify_url=verify_url,
    )


@admin_bp.route("/cv/<int:applicant_id>/export/docx")
@login_required
@admin_required
@permission_required("cv")
def cv_export_docx(applicant_id):
    applicant = Applicant.query.get_or_404(applicant_id)
    profile = applicant.cv_profile
    if profile is None:
        flash("እባክዎ መጀመሪያ የCV መገለጫ ይሙሉ። / Please fill in the CV profile first.", "warning")
        return redirect(url_for("admin.cv_form", applicant_id=applicant.id))

    portrait_doc = applicant.documents.filter_by(doc_type="photo_portrait", status="verified").first()
    full_doc = applicant.documents.filter_by(doc_type="photo_full", status="verified").first()
    passport_doc = applicant.documents.filter_by(doc_type="passport", status="verified").first()

    buffer = build_cv_docx(
        applicant, profile,
        company_name=current_app.config.get("COMPANY_NAME", "ASM Foreign Employment Agency"),
        company_phone=current_app.config.get("COMPANY_PHONE", ""),
        company_email=current_app.config.get("COMPANY_EMAIL", ""),
        company_address_en=current_app.config.get("COMPANY_ADDRESS_EN", ""),
        portrait_doc=portrait_doc, full_doc=full_doc, passport_doc=passport_doc,
    )
    safe_name = "".join(c for c in applicant.full_name if c.isalnum() or c in " _-").strip().replace(" ", "_")
    filename = f"CV_{safe_name or applicant.id}_{profile.application_no}.docx"
    return send_file(
        buffer, as_attachment=True, download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# ---------------------------------------------------------------------------
# Partner agencies
# ---------------------------------------------------------------------------

@admin_bp.route("/partners", methods=["GET", "POST"])
@login_required
@admin_required
@permission_required("partners")
def partners():
    if request.method == "POST":
        partner = Partner(
            name=request.form.get("name", "").strip(),
            country=request.form.get("country", "").strip(),
            contact_person=request.form.get("contact_person", "").strip() or None,
            contact_email=request.form.get("contact_email", "").strip() or None,
            contact_phone=request.form.get("contact_phone", "").strip() or None,
        )
        db.session.add(partner)
        db.session.flush()
        log_action("partner.create", "Partner", partner.id, partner.name)
        db.session.commit()
        flash("አዲስ አጋር ኤጀንሲ ተጨምሯል። / New partner agency added.", "success")
        return redirect(url_for("admin.partners"))

    all_partners = Partner.query.order_by(Partner.created_at.desc()).all()
    return render_template("admin/partners.html", partners=all_partners)


# ---------------------------------------------------------------------------
# Interviews
# ---------------------------------------------------------------------------

@admin_bp.route("/interviews", methods=["GET", "POST"])
@login_required
@admin_required
@permission_required("interviews")
def interviews():
    if request.method == "POST":
        applicant_id = request.form.get("applicant_id")
        applicant = Applicant.query.get(applicant_id) if applicant_id else None
        scheduled_raw = request.form.get("scheduled_at")
        if not applicant or not scheduled_raw:
            flash("እባክዎ አመልካች እና ቀን/ሰዓት ይምረጡ። / Please choose an applicant and a date/time.", "danger")
            return redirect(url_for("admin.interviews"))
        try:
            scheduled_at = datetime.strptime(scheduled_raw, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("የቀን/ሰዓት ቅርጸት ትክክል አይደለም። / Invalid date/time format.", "danger")
            return redirect(url_for("admin.interviews"))

        interview = Interview(
            applicant_id=applicant.id, scheduled_at=scheduled_at,
            mode=request.form.get("mode", "video"),
            notes=request.form.get("notes", "").strip() or None,
            created_by=current_user.id,
        )
        db.session.add(interview)
        db.session.flush()
        log_action("interview.schedule", "Interview", interview.id, applicant.full_name)
        db.session.commit()
        flash("ቃለ መጠይቅ ተይዞልታል። / Interview scheduled.", "success")
        return redirect(url_for("admin.interviews"))

    upcoming = Interview.query.filter(Interview.status == "scheduled").order_by(Interview.scheduled_at.asc()).all()
    past = Interview.query.filter(Interview.status != "scheduled").order_by(Interview.scheduled_at.desc()).limit(20).all()
    all_applicants = Applicant.query.order_by(Applicant.full_name).all()
    return render_template("admin/interviews.html", upcoming=upcoming, past=past, applicants=all_applicants)


@admin_bp.route("/interviews/<int:interview_id>/status", methods=["POST"])
@login_required
@admin_required
@permission_required("interviews")
def update_interview_status(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    new_status = request.form.get("status")
    if new_status in Interview.STATUSES:
        interview.status = new_status
        log_action("interview.status_update", "Interview", interview.id, new_status)
        db.session.commit()
        flash("የቃለ መጠይቅ ሁኔታ ተስተካክሏል። / Interview status updated.", "success")
    return redirect(url_for("admin.interviews"))


# ---------------------------------------------------------------------------
# Reviews — post-deployment ratings
# ---------------------------------------------------------------------------

@admin_bp.route("/reviews", methods=["GET", "POST"])
@login_required
@admin_required
@permission_required("reviews")
def reviews():
    if request.method == "POST":
        applicant_id = request.form.get("applicant_id")
        applicant = Applicant.query.get(applicant_id) if applicant_id else None
        rating = request.form.get("rating")
        if not applicant or not rating:
            flash("እባክዎ አመልካች እና ደረጃ ይምረጡ። / Please choose an applicant and a rating.", "danger")
            return redirect(url_for("admin.reviews"))

        review = Review(
            applicant_id=applicant.id, rating=int(rating),
            comment=request.form.get("comment", "").strip() or None,
            reviewer_type=request.form.get("reviewer_type", "agency"),
            logged_by=current_user.id,
        )
        db.session.add(review)
        db.session.flush()
        log_action("review.add", "Review", review.id, f"{applicant.full_name}: {rating}/5")
        db.session.commit()
        flash("ግምገማ ተመዝግቧል። / Review recorded.", "success")
        return redirect(url_for("admin.reviews"))

    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    deployed_applicants = Applicant.query.filter_by(pipeline_status="deployed").order_by(Applicant.full_name).all()
    return render_template("admin/reviews.html", reviews=all_reviews, applicants=deployed_applicants)


# ---------------------------------------------------------------------------
# Notifications — bulk SMS/email (scaffold; wire a real provider to go live)
# ---------------------------------------------------------------------------

@admin_bp.route("/notifications", methods=["GET", "POST"])
@login_required
@admin_required
@permission_required("notifications")
def notifications():
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        audience = request.form.get("audience", "all")
        if not message:
            flash("እባክዎ መልእክት ይጻፉ። / Please write a message.", "danger")
            return redirect(url_for("admin.notifications"))

        query = Applicant.query
        if audience.startswith("stage:"):
            query = query.filter_by(pipeline_status=audience.split(":", 1)[1])
        recipients = query.count()

        note = Notification(
            channel=request.form.get("channel", "sms"), message=message,
            audience_filter=audience, recipient_count=recipients,
            status="queued", sent_by=current_user.id,
        )
        db.session.add(note)
        db.session.flush()
        log_action("notification.queue", "Notification", note.id, f"{recipients} recipients")
        db.session.commit()
        flash(
            f"{recipients} ተቀባዮች ወደ ወረፋ ገብተዋል። ትክክለኛ መላክ ግን የSMS አቅራቢ ማዋቀር ይጠይቃል (README ይመልከቱ)። / "
            f"Queued for {recipients} recipients — actually sending requires connecting an SMS provider (see README).",
            "info",
        )
        return redirect(url_for("admin.notifications"))

    sent_log = Notification.query.order_by(Notification.created_at.desc()).limit(30).all()
    stage_counts = dict(
        db.session.query(Applicant.pipeline_status, func.count(Applicant.id))
        .group_by(Applicant.pipeline_status).all()
    )
    return render_template("admin/notifications.html", sent_log=sent_log, stage_counts=stage_counts,
                            stages=Applicant.PIPELINE_STAGES)


# ---------------------------------------------------------------------------
# Audit log — super admin only
# ---------------------------------------------------------------------------

@admin_bp.route("/audit")
@login_required
@admin_required
@super_admin_required
def audit():
    entries = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(150).all()
    return render_template("admin/audit.html", entries=entries)


# ---------------------------------------------------------------------------
# Team — manage who has admin access to this panel, and what they can do
# ---------------------------------------------------------------------------

@admin_bp.route("/team", methods=["GET", "POST"])
@login_required
@admin_required
@super_admin_required
def team():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        is_super = request.form.get("is_super_admin") == "on"
        granted = request.form.getlist("permissions")

        if not name or not username or not email or not password:
            flash("ስም፣ የተጠቃሚ ስም፣ ኢሜይል እና የይለፍ ቃል ያስፈልጋሉ። / Name, username, email, and password are required.", "danger")
            return redirect(url_for("admin.team"))
        if len(password) < 8:
            flash("የይለፍ ቃል ቢያንስ 8 ፊደላት ሊኖረው ይገባል። / Password must be at least 8 characters.", "danger")
            return redirect(url_for("admin.team"))

        # Guard against duplicates — never create a second account for the same username/email/phone.
        if User.query.filter_by(username=username).first():
            flash(f"'{username}' ቀድሞውኑ ተይዟል፣ ድግግሞሽ አልተፈጠረም። / '{username}' is already taken — no duplicate was created.", "warning")
            return redirect(url_for("admin.team"))
        if User.query.filter_by(email=email).first():
            flash(f"'{email}' ቀድሞውኑ ተመዝግቧል፣ ድግግሞሽ አልተፈጠረም። / '{email}' is already registered — no duplicate was created.", "warning")
            return redirect(url_for("admin.team"))
        if phone and User.query.filter_by(phone=phone).first():
            flash(f"'{phone}' ቀድሞውኑ ተመዝግቧል፣ ድግግሞሽ አልተፈጠረም። / '{phone}' is already registered — no duplicate was created.", "warning")
            return redirect(url_for("admin.team"))

        new_admin = User(
            name=name, username=username, email=email, phone=phone or None,
            role="admin", is_verified=True, is_super_admin=is_super,
            permissions=[] if is_super else [p for p in granted if p in User.PERMISSION_SCOPES],
        )
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.flush()
        log_action("team.add_admin", "User", new_admin.id, name)
        db.session.commit()
        flash(f"'{name}' እንደ አድሚን ተጨምሯል፣ አሁን በ '{username}' መግባት ይችላል። / '{name}' was added as an admin and can now sign in as '{username}'.", "success")
        return redirect(url_for("admin.team"))

    admins = User.query.filter_by(role="admin").order_by(User.created_at.asc()).all()
    return render_template("admin/team.html", admins=admins, scopes=User.PERMISSION_SCOPES)
