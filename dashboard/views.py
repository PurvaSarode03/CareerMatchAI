from collections import Counter

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ai_engine.recommender import recommend_jobs
from ai_engine.suggestions import resume_health
from jobs.models import Job
from resumes.services import resume_to_dict


@login_required
def home(request):
    user = request.user
    analyses = list(user.analyses.order_by("created_at"))
    resume = user.resumes.first()

    df = pd.DataFrame([{"date": a.created_at, "score": a.score, "skill": a.skill_score, "semantic": a.semantic_score,
                        "title": a.job_title or "Custom JD"} for a in analyses])
    stats = {"resumes": user.resumes.count(), "analyses": len(analyses),
             "avg": round(df["score"].mean(), 1) if not df.empty else 0,
             "best": round(df["score"].max(), 1) if not df.empty else 0}

    missing = Counter(m["name"] for a in analyses for m in a.missing_skills)
    charts = {
        "trend": {"labels": [d.strftime("%d %b") for d in df["date"]] if not df.empty else [],
                  "scores": df["score"].round(1).tolist() if not df.empty else []},
        "gaps": {"labels": [k for k, _ in missing.most_common(8)], "values": [v for _, v in missing.most_common(8)]},
        "categories": {}, "bands": [0, 0, 0],
    }
    if not df.empty:
        charts["bands"] = [int((df.score >= 70).sum()), int(((df.score >= 45) & (df.score < 70)).sum()), int((df.score < 45).sum())]

    health, recs = None, []
    if resume:
        charts["categories"] = dict(Counter(s.get_category_display() for s in resume.skills.all()))
        health = resume_health(resume_to_dict(resume))
        try:
            recs = recommend_jobs(resume, Job.objects.filter(is_active=True), [s.name for s in resume.skills.all()], limit=3)
        except Exception:
            recs = []
    return render(request, "dashboard/home.html", {
        "stats": stats, "charts": charts, "resume": resume, "health": health, "recs": recs,
        "recent": list(reversed(analyses))[:5]})
