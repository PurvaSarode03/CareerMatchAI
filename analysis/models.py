from django.conf import settings
from django.db import models

from jobs.models import Job
from resumes.models import Resume


class Analysis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analyses")
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="analyses")
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name="analyses")
    job_title = models.CharField(max_length=160, blank=True)
    job_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    score = models.FloatField()               # final 0-100
    skill_score = models.FloatField()         # 0-100
    semantic_score = models.FloatField()      # 0-100
    raw_similarity = models.FloatField(default=0)  # raw cosine
    embedding_backend = models.CharField(max_length=40, blank=True)

    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)   # [{name, category, priority}]
    related_skills = models.JSONField(default=list)   # [{missing, have}]
    explanation = models.JSONField(default=dict)
    suggestions = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]
        verbose_name_plural = "analyses"

    def __str__(self):
        return f"{self.job_title or 'Custom JD'} — {self.score:.0f}%"

    @property
    def band(self):
        return "success" if self.score >= 70 else "warning" if self.score >= 45 else "danger"
