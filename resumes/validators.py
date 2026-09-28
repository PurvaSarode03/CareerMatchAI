"""Secure upload validation: extension, size and file signature (magic bytes)."""
from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED = {".pdf": b"%PDF", ".docx": b"PK\x03\x04"}


def validate_resume_file(f):
    name = f.name.lower()
    ext = next((e for e in ALLOWED if name.endswith(e)), None)
    if not ext:
        raise ValidationError("Only PDF and DOCX files are allowed.")
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if f.size > max_bytes:
        raise ValidationError(f"File too large. Maximum size is {settings.MAX_UPLOAD_MB} MB.")
    head = f.read(4)
    f.seek(0)
    if not head.startswith(ALLOWED[ext]):
        raise ValidationError("File content does not match its extension.")
