from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def is_allowed_image(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_candidate_photo(file: FileStorage) -> str | None:
    if not file or not file.filename:
        return None
    if not is_allowed_image(file.filename):
        raise ValueError("Invalid image type. Allowed: png, jpg, jpeg, webp.")

    safe_name = secure_filename(file.filename)
    ext = safe_name.rsplit(".", 1)[1].lower()
    unique_name = f"candidate_{uuid.uuid4().hex}.{ext}"

    upload_root = Path(current_app.config["UPLOAD_FOLDER"])
    candidate_dir = upload_root / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)

    final_path = candidate_dir / unique_name
    file.save(final_path)
    return f"candidates/{unique_name}"


def delete_uploaded_file(relative_path: str | None) -> None:
    if not relative_path:
        return
    root = Path(current_app.config["UPLOAD_FOLDER"])
    file_path = root / relative_path
    if file_path.exists() and file_path.is_file():
        os.remove(file_path)

