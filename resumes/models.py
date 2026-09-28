import os
import uuid

from django.conf import settings
from django.db import models

from jobs.models import Skill


def resume_upload_path(instance, filename):
    """Random file names: no user-controlled paths, no collisions, no guessing."""
    ext = os.path.splitext(filename)[1].lower()
    return f"resumes/{instance.user_id}/{uuid.uuid4().hex}{ext}"


class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes")
    title = models.CharField(max_length=120)
    original_filename = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=resume_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Extracted content
    raw_text = models.TextField(blank=True)
    full_name = models.CharField(max_length=120, blank=True)
    email = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    summary = models.TextField(blank=True)
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name="resumes")
    unmapped_skills = models.JSONField(default=list, blank=True)
    stats = models.JSONField(default=dict, blank=True)  # word count, sections, quality score…
    embedding = models.JSONField(null=True, blank=True, editable=False)
    embedding_backend = models.CharField(max_length=40, blank=True, editable=False)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} ({self.user})"

    def delete(self, *args, **kwargs):
        storage, path = self.file.storage, self.file.name
        super().delete(*args, **kwargs)
        if path:
            storage.delete(path)
