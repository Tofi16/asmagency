import os
import uuid

from flask import current_app, url_for
from werkzeug.utils import secure_filename


def cloudinary_enabled():
    return bool(
        current_app.config.get("CLOUDINARY_URL")
        or all(
            current_app.config.get(key)
            for key in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
        )
    )


def save_upload(file, folder="asm-agency/documents"):
    """Store an upload in Cloudinary when configured, otherwise on local disk."""
    original_name = secure_filename(file.filename or "upload")
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    stored_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    if cloudinary_enabled():
        import cloudinary.uploader

        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            public_id=stored_name.rsplit(".", 1)[0],
            resource_type="auto",
        )
        return stored_name, result["secure_url"], result.get("bytes")

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_name)
    file.save(file_path)
    return stored_name, file_path, os.path.getsize(file_path)


def document_url(document):
    if not document:
        return ""
    if document.file_path and document.file_path.startswith(("http://", "https://")):
        return document.file_path
    return url_for("static", filename=f"uploads/{document.stored_filename}")