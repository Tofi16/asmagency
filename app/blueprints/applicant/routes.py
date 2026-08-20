import os
import uuid
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.blueprints.applicant import applicant_bp
from app.extensions import db
from app.models.document import Document
from app.models.application import Application
from app.utils.decorators import applicant_required


@applicant_bp.route("/dashboard")
@login_required
@applicant_required
def dashboard():
    applicant = current_user.applicant
    recent_apps = (
        applicant.applications.order_by(Application.submitted_at.desc()).limit(5).all()
    )
    pending_docs = applicant.documents.filter_by(status="pending").count()
    return render_template(
        "applicant/dashboard.html",
        applicant=applicant,
        recent_apps=recent_apps,
        pending_docs=pending_docs,
    )


@applicant_bp.route("/profile", methods=["GET", "POST"])
@login_required
@applicant_required
def profile():
    applicant = current_user.applicant
    if request.method == "POST":
        applicant.full_name = request.form.get("full_name", applicant.full_name).strip()
        applicant.region = request.form.get("region", "").strip() or None
        applicant.city = request.form.get("city", "").strip() or None
        applicant.education_level = request.form.get("education_level", "").strip() or None
        applicant.work_experience = request.form.get("work_experience", "").strip() or None
        applicant.preferred_country = request.form.get("preferred_country", "").strip() or None
        applicant.preferred_job_category = request.form.get("preferred_job_category", "").strip() or None
        db.session.commit()
        flash("መገለጫዎ ተስተካክሏል። / Your profile has been updated.", "success")
        return redirect(url_for("applicant.profile"))

    return render_template("applicant/profile.html", applicant=applicant)


@applicant_bp.route("/applications")
@login_required
@applicant_required
def applications():
    applicant = current_user.applicant
    apps = applicant.applications.order_by(Application.submitted_at.desc()).all()
    return render_template("applicant/applications.html", applications=apps)


@applicant_bp.route("/uploads", methods=["GET", "POST"])
@login_required
@applicant_required
def uploads():
    applicant = current_user.applicant

    if request.method == "POST":
        file = request.files.get("document")
        doc_type = request.form.get("doc_type", "other")

        if not file or file.filename == "":
            flash("እባክዎ ፋይል ይምረጡ። / Please choose a file.", "danger")
            return redirect(url_for("applicant.uploads"))

        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in Document.ALLOWED_EXTENSIONS:
            flash("የማይፈቀድ የፋይል አይነት (pdf, jpg, png ብቻ)። / File type not allowed (pdf, jpg, png only).", "danger")
            return redirect(url_for("applicant.uploads"))

        stored_name = f"{uuid.uuid4().hex}.{ext}"
        upload_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, stored_name)
        file.save(file_path)

        doc = Document(
            applicant_id=applicant.id,
            doc_type=doc_type,
            original_filename=secure_filename(file.filename),
            stored_filename=stored_name,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
        )
        db.session.add(doc)
        db.session.commit()
        flash("ሰነድ ተሰቅሏል፣ ለማረጋገጫ በመጠባበቅ ላይ። / Document uploaded, pending verification.", "success")
        return redirect(url_for("applicant.uploads"))

    docs = applicant.documents.order_by(Document.uploaded_at.desc()).all()
    return render_template(
        "applicant/uploads.html", documents=docs, doc_types=Document.DOC_TYPES,
        doc_labels_am=Document.DOC_TYPE_LABELS_AM, doc_labels_en=Document.DOC_TYPE_LABELS_EN,
    )
