from django.db import transaction

from ai_engine.parser import parse_resume
from ai_engine.text_extraction import extract_text
from jobs.models import Skill


def process_resume(resume):
    """Extract text, run NLP parsing, and store structured fields on the Resume."""
    resume.file.open("rb")
    try:
        text = extract_text(resume.file, resume.original_filename or resume.file.name)
    finally:
        resume.file.close()
    parsed = parse_resume(text)
    with transaction.atomic():
        resume.raw_text = text
        resume.full_name = parsed.full_name
        resume.email = parsed.email
        resume.phone = parsed.phone
        resume.summary = parsed.summary
        resume.education = parsed.education
        resume.experience = parsed.experience
        resume.projects = parsed.projects
        resume.certifications = parsed.certifications
        resume.unmapped_skills = parsed.unmapped_skills
        resume.stats = {**parsed.stats, "linkedin": parsed.linkedin, "github": parsed.github}
        resume.embedding, resume.embedding_backend = None, ""   # recomputed lazily
        resume.save()
        resume.skills.set(Skill.objects.filter(name__in=[s["name"] for s in parsed.skills]))
    return resume


def resume_to_dict(resume):
    return {
        "full_name": resume.full_name, "email": resume.email, "phone": resume.phone, "summary": resume.summary,
        "education": resume.education, "experience": resume.experience, "projects": resume.projects,
        "certifications": resume.certifications, "stats": resume.stats,
        "skills": [{"name": s.name, "category": s.category} for s in resume.skills.all()],
    }
