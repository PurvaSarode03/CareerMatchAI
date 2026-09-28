"""Recommend jobs for a resume using vectorised cosine similarity (NumPy) + skill overlap (Pandas ranking)."""
import numpy as np
import pandas as pd

from . import embeddings as emb
from .matcher import RELATED_CREDIT, SEMANTIC_WEIGHT, SKILL_WEIGHT
from .skills import load_related_map


def job_text(job) -> str:
    return f"{job.title}. {job.description}"


def ensure_embeddings(objs, text_fn, backend):
    """Compute + cache embeddings on model instances (Job/Resume) whose cache is missing or from another backend."""
    for o in objs:
        if not o.embedding or o.embedding_backend != backend:
            o.embedding = emb.embed_document(text_fn(o)).tolist()
            o.embedding_backend = backend
            o.save(update_fields=["embedding", "embedding_backend"])


def recommend_jobs(resume, jobs, resume_skill_names, limit=10, min_score=0):
    backend = emb.backend_name()
    jobs = list(jobs.prefetch_related("required_skills"))
    if not jobs:
        return []
    ensure_embeddings(jobs, job_text, backend)
    if not resume.embedding or resume.embedding_backend != backend:
        resume.embedding = emb.embed_document(resume.raw_text).tolist()
        resume.embedding_backend = backend
        resume.save(update_fields=["embedding", "embedding_backend"])

    R = np.asarray(resume.embedding, dtype=float)
    J = np.asarray([j.embedding for j in jobs], dtype=float)
    cos = (J @ R) / (np.linalg.norm(J, axis=1) * np.linalg.norm(R) + 1e-9)

    have, rel_map, rows = set(resume_skill_names), load_related_map(), []
    for job, c in zip(jobs, cos):
        req = [s.name for s in job.required_skills.all()]
        matched = [s for s in req if s in have]
        related = [s for s in req if s not in have and have & rel_map.get(s, set())]
        missing = [s for s in req if s not in have]
        skill = (len(matched) + RELATED_CREDIT * len(related)) / len(req) * 100 if req else 0.0
        sem = emb.calibrate(float(c), backend)
        score = SKILL_WEIGHT * skill + SEMANTIC_WEIGHT * sem if req else sem
        rows.append({"job": job, "score": round(score, 1), "skill_score": round(skill, 1), "semantic_score": round(sem, 1),
                     "matched": matched, "missing": missing, "n_required": len(req)})
    df = pd.DataFrame(rows).sort_values(["score", "skill_score"], ascending=False)
    df = df[df["score"] >= min_score].head(limit)
    return df.to_dict("records")
