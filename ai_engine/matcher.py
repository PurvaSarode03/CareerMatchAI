"""Resume <-> Job matching: skill matching + semantic similarity -> 0-100 score with explanation."""
from dataclasses import dataclass, field

import numpy as np

from . import embeddings as emb
from .skills import extract_skills, load_related_map

SKILL_WEIGHT, SEMANTIC_WEIGHT = 0.6, 0.4
RELATED_CREDIT = 0.5          # partial credit for a related (transferable) skill
CORE_CATEGORIES = {"language", "backend", "frontend", "database", "data", "cloud"}


@dataclass
class MatchResult:
    score: float
    skill_score: float
    semantic_score: float
    raw_similarity: float
    backend: str
    matched: list = field(default_factory=list)
    missing: list = field(default_factory=list)   # dicts: name, category, priority, related_have
    related: list = field(default_factory=list)   # dicts: missing, have
    extra: list = field(default_factory=list)     # resume skills not asked for
    explanation: dict = field(default_factory=dict)


def _weight(count: int) -> float:
    return min(1 + 0.25 * (count - 1), 1.5)   # skills repeated in the JD matter a bit more


def _semantic_related(missing_names, have_names, backend):
    """Embedding-based relatedness (only meaningful with real Sentence Transformers)."""
    if not missing_names or not have_names or not backend.startswith("sbert"):
        return {}
    m, h = emb.encode(missing_names), emb.encode(have_names)
    sims = m @ h.T
    out = {}
    for i, name in enumerate(missing_names):
        j = int(np.argmax(sims[i]))
        if sims[i, j] >= 0.6:
            out[name] = have_names[j]
    return out


def compute_match(resume_skill_names, resume_text, resume_vec, jd_text, jd_skills=None, jd_vec=None,
                  backend=None, related_map=None) -> MatchResult:
    backend = backend or emb.backend_name()
    related_map = related_map if related_map is not None else load_related_map()
    jd_skills = jd_skills if jd_skills is not None else extract_skills(jd_text)
    have = set(resume_skill_names)

    # ---- semantic similarity (cosine on document embeddings)
    if resume_vec is None:
        resume_vec = emb.embed_document(resume_text)
    if jd_vec is None:
        jd_vec = emb.embed_document(jd_text)
    raw = emb.cosine(resume_vec, jd_vec)
    semantic = emb.calibrate(raw, backend)

    # ---- skill match
    matched, missing, related = [], [], []
    total_w = matched_w = related_w = 0.0
    sem_rel = _semantic_related([h.name for h in jd_skills if h.name not in have], sorted(have), backend)
    for h in jd_skills:
        w = _weight(h.count)
        total_w += w
        if h.name in have:
            matched.append(h.name)
            matched_w += w
            continue
        have_related = sorted(have & related_map.get(h.name, set()))
        if not have_related and h.name in sem_rel:
            have_related = [sem_rel[h.name]]
        if have_related:
            related_w += w
            related.append({"missing": h.name, "have": have_related[:3]})
        priority = "high" if h.count >= 2 else ("medium" if h.category in CORE_CATEGORIES else "low")
        missing.append({"name": h.name, "category": h.category, "priority": priority, "mentions": h.count,
                        "related_have": have_related[:3]})

    if total_w:
        skill_score = (matched_w + RELATED_CREDIT * related_w) / total_w * 100
        final = SKILL_WEIGHT * skill_score + SEMANTIC_WEIGHT * semantic
    else:  # JD has no recognisable skills: rely on semantic similarity only
        skill_score, final = 0.0, semantic

    required = {h.name for h in jd_skills}
    extra = sorted(have - required)
    order = {"high": 0, "medium": 1, "low": 2}
    missing.sort(key=lambda d: (order[d["priority"]], d["name"]))
    final = float(np.clip(final, 0, 100))

    res = MatchResult(score=round(final, 1), skill_score=round(skill_score, 1), semantic_score=round(semantic, 1),
                      raw_similarity=round(raw, 4), backend=backend, matched=sorted(matched), missing=missing,
                      related=related, extra=extra)
    res.explanation = explain(res, len(jd_skills), bool(total_w))
    return res


def explain(res: MatchResult, n_required: int, has_skills: bool) -> dict:
    """Human-readable breakdown of how the final score was produced."""
    parts = []
    if has_skills:
        parts.append({"label": "Skill match", "weight": int(SKILL_WEIGHT * 100), "score": res.skill_score,
                      "points": round(SKILL_WEIGHT * res.skill_score, 1),
                      "detail": f"{len(res.matched)} of {n_required} required skills found"
                                + (f", {len(res.related)} more have a related skill (half credit)" if res.related else "")})
        parts.append({"label": "Semantic similarity", "weight": int(SEMANTIC_WEIGHT * 100), "score": res.semantic_score,
                      "points": round(SEMANTIC_WEIGHT * res.semantic_score, 1),
                      "detail": f"Cosine similarity {res.raw_similarity:.2f} between resume and job text ({res.backend})"})
    else:
        parts.append({"label": "Semantic similarity", "weight": 100, "score": res.semantic_score, "points": res.semantic_score,
                      "detail": "No known skills were found in the job text, so only text similarity was used"})
    if res.score >= 75:
        verdict = "Strong match — you cover most of what the role asks for."
    elif res.score >= 55:
        verdict = "Good match — a few gaps to close, most of the core fits."
    elif res.score >= 35:
        verdict = "Partial match — there are meaningful gaps for this role."
    else:
        verdict = "Low match — this role is far from your current profile."
    reasons = []
    if res.matched:
        reasons.append("Strengths: " + ", ".join(res.matched[:8]))
    high = [m["name"] for m in res.missing if m["priority"] == "high"]
    if high:
        reasons.append("Biggest gaps (emphasised in the job): " + ", ".join(high[:6]))
    elif res.missing:
        reasons.append("Missing: " + ", ".join(m["name"] for m in res.missing[:6]))
    return {"verdict": verdict, "components": parts, "reasons": reasons}
