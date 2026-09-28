import csv
import io

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from .models import Job, Skill


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(help_text="Columns: name,category,aliases (aliases separated by |)")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "job_count")
    list_filter = ("category", "is_active")
    search_fields = ("name", "aliases")
    filter_horizontal = ("related",)
    change_list_template = "admin/jobs/skill_changelist.html"

    @admin.display(description="Jobs")
    def job_count(self, obj):
        return obj.jobs.count()

    def get_urls(self):
        return [path("import-csv/", self.admin_site.admin_view(self.import_csv), name="jobs_skill_import")] + super().get_urls()

    def import_csv(self, request):
        form = CsvImportForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            data = form.cleaned_data["csv_file"].read().decode("utf-8-sig")
            created = 0
            for row in csv.DictReader(io.StringIO(data)):
                name = (row.get("name") or "").strip()
                if not name:
                    continue
                _, was_new = Skill.objects.update_or_create(name=name, defaults={
                    "category": (row.get("category") or "other").strip(),
                    "aliases": ", ".join(a.strip() for a in (row.get("aliases") or "").split("|") if a.strip()),
                })
                created += was_new
            messages.success(request, f"Import finished. {created} new skills added.")
            return redirect("..")
        return render(request, "admin/jobs/csv_form.html", {"form": form, "opts": self.model._meta, "title": "Import skills from CSV"})


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "job_type", "experience_level", "is_active", "created_at")
    list_filter = ("is_active", "job_type", "experience_level")
    search_fields = ("title", "company", "description")
    filter_horizontal = ("required_skills",)
    actions = ["activate", "deactivate", "auto_detect_skills"]

    @admin.action(description="Mark selected jobs active")
    def activate(self, request, qs):
        qs.update(is_active=True)

    @admin.action(description="Mark selected jobs inactive")
    def deactivate(self, request, qs):
        qs.update(is_active=False)

    @admin.action(description="Auto-detect required skills from description (NLP)")
    def auto_detect_skills(self, request, qs):
        from ai_engine.skills import extract_skills
        n = 0
        for job in qs:
            found = extract_skills(job.description)
            job.required_skills.add(*Skill.objects.filter(name__in=[s.name for s in found]))
            job.embedding = None
            job.save()
            n += 1
        self.message_user(request, f"Updated skills for {n} job(s).", messages.SUCCESS)

    def save_model(self, request, obj, form, change):
        obj.embedding = None  # force re-embedding after edits
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Fill skills automatically if the admin left them empty.
        job = form.instance
        if not job.required_skills.exists():
            from ai_engine.skills import extract_skills
            job.required_skills.add(*Skill.objects.filter(name__in=[s.name for s in extract_skills(job.description)]))
