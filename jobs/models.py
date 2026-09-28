from django.db import models


class Skill(models.Model):
    CATEGORIES = [
        ("language", "Programming Language"), ("backend", "Backend"), ("frontend", "Frontend"),
        ("database", "Database"), ("cloud", "Cloud & DevOps"), ("data", "Data & ML"),
        ("tools", "Tools"), ("soft", "Soft Skill"), ("other", "Other"),
    ]
    name = models.CharField(max_length=80, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORIES, default="other")
    aliases = models.CharField(max_length=255, blank=True, help_text="Comma-separated alternate spellings, e.g. 'js, ecmascript'")
    related = models.ManyToManyField("self", blank=True, help_text="Skills that partially transfer (e.g. MySQL <-> PostgreSQL)")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def alias_list(self):
        return [a.strip() for a in self.aliases.split(",") if a.strip()]


class Job(models.Model):
    JOB_TYPES = [("full_time", "Full-time"), ("part_time", "Part-time"), ("internship", "Internship"),
                 ("contract", "Contract"), ("remote", "Remote")]
    LEVELS = [("entry", "Entry / Fresher"), ("mid", "Mid-level"), ("senior", "Senior")]

    title = models.CharField(max_length=160)
    company = models.CharField(max_length=120)
    location = models.CharField(max_length=120, blank=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default="full_time")
    experience_level = models.CharField(max_length=10, choices=LEVELS, default="entry")
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill, blank=True, related_name="jobs")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    embedding = models.JSONField(null=True, blank=True, editable=False)
    embedding_backend = models.CharField(max_length=40, blank=True, editable=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_active", "-created_at"])]

    def __str__(self):
        return f"{self.title} @ {self.company}"
