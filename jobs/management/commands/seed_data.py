from django.core.management.base import BaseCommand

from ai_engine.seed_data import JOBS, RELATED_GROUPS, SKILLS
from jobs.models import Job, Skill


class Command(BaseCommand):
    help = "Seed the skills vocabulary, related-skill graph and sample jobs."

    def add_arguments(self, parser):
        parser.add_argument("--no-jobs", action="store_true", help="Seed only skills")

    def handle(self, *args, **opts):
        from ai_engine.skills import extract_skills

        for name, cat, aliases in SKILLS:
            Skill.objects.update_or_create(name=name, defaults={"category": cat, "aliases": ", ".join(aliases)})
        by_name = {s.name: s for s in Skill.objects.all()}
        for group in RELATED_GROUPS:
            objs = [by_name[n] for n in group if n in by_name]
            for s in objs:
                s.related.add(*[o for o in objs if o.pk != s.pk])
        self.stdout.write(self.style.SUCCESS(f"Skills: {Skill.objects.count()}"))

        if not opts["no_jobs"]:
            for title, company, loc, jtype, level, desc in JOBS:
                job, _ = Job.objects.get_or_create(title=title, company=company, defaults={
                    "location": loc, "job_type": jtype, "experience_level": level, "description": desc})
                job.required_skills.set(Skill.objects.filter(name__in=[h.name for h in extract_skills(desc)]))
            self.stdout.write(self.style.SUCCESS(f"Jobs: {Job.objects.count()}"))
