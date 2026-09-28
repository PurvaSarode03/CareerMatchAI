from ai_engine import embeddings as emb
from ai_engine.matcher import compute_match
from ai_engine.recommender import ensure_embeddings, job_text
from ai_engine.skills import extract_skills
from ai_engine.suggestions import build_suggestions
from resumes.services import resume_to_dict

from .models import Analysis


def run_analysis(user, resume, jd_text, job=None, title=""):
    backend = emb.backend_name()
    if not resume.embedding or resume.embedding_backend != backend:
        resume.embedding = emb.embed_document(resume.raw_text).tolist()
        resume.embedding_backend = backend
        resume.save(update_fields=["embedding", "embedding_backend"])

    jd_vec = None
    jd_skills = None
    if job is not None:
        ensure_embeddings([job], job_text, backend)
        jd_vec = job.embedding
        jd_skills = None  # extract from the text so weights (mention counts) are consistent
    result = compute_match(
        resume_skill_names=[s.name for s in resume.skills.all()], resume_text=resume.raw_text,
        resume_vec=resume.embedding, jd_text=jd_text, jd_skills=jd_skills, jd_vec=jd_vec, backend=backend)
    suggestions = build_suggestions(resume_to_dict(resume), result.missing, result.related, title)
    return Analysis.objects.create(
        user=user, resume=resume, job=job, job_title=(title or (job.title if job else ""))[:160],
        job_description=jd_text, score=result.score, skill_score=result.skill_score,
        semantic_score=result.semantic_score, raw_similarity=result.raw_similarity, embedding_backend=result.backend,
        matched_skills=result.matched, missing_skills=result.missing, related_skills=result.related,
        explanation={**result.explanation, "extra": result.extra}, suggestions=suggestions)
