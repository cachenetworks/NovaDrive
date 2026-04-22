from __future__ import annotations

from pathlib import PurePath

from werkzeug.utils import secure_filename


class ValidationError(ValueError):
    pass


def normalize_filename(filename: str) -> str:
    cleaned = secure_filename(filename.strip())
    if not cleaned:
        raise ValidationError("A valid filename is required.")
    return cleaned


def validate_upload_size(content_length: int | None, max_size: int) -> None:
    if content_length is not None and content_length > max_size:
        raise ValidationError("The file exceeds the configured maximum upload size.")


def validate_folder_name(name: str) -> str:
    candidate = name.strip()
    if not candidate:
        raise ValidationError("Folder name cannot be empty.")
    if len(candidate) > 120:
        raise ValidationError("Folder name is too long.")
    if PurePath(candidate).name != candidate:
        raise ValidationError("Folder name cannot contain path separators.")
    return candidate
