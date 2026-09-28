from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from ai_engine.recommender import recommend_jobs

from .models import Job, Skill


@login_required
def job_list(request):
    qs = Job.objects.filter(is_active=True).prefetch_related("required_skills")
    q, loc, jtype, level, skill = (request.GET.get(k, "").strip() for k in ("q", "location", "type", "level", "skill"))
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(company__icontains=q) | Q(description__icontains=q)
                       | Q(required_skills__name__icontains=q)).distinct()
    if loc:
        qs = qs.filter(location__icontains=loc)
    if jtype:
        qs = qs.filter(job_type=jtype)
    if level:
        qs = qs.filter(experience_level=level)
    if skill.isdigit():
        qs = qs.filter(required_skills__pk=skill)
    page = Paginator(qs, 9).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "jobs/list.html", {
        "page": page, "job_types": Job.JOB_TYPES, "levels": Job.LEVELS, "skills": Skill.objects.filter(jobs__isnull=False).distinct(),
        "f": {"q": q, "location": loc, "type": jtype, "level": level, "skill": skill}, "qs": params.urlencode()})


@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job.objects.prefetch_related("required_skills"), pk=pk, is_active=True)
    mine = {s.name for r in request.user.resumes.all()[:1] for s in r.skills.all()}
    return render(request, "jobs/detail.html", {"job": job, "mine": mine})


@login_required
def recommendations(request):
    resumes = request.user.resumes.all()
    resume = resumes.filter(pk=request.GET.get("resume")).first() if request.GET.get("resume") else resumes.first()
    recs = []
    if resume:
        recs = recommend_jobs(resume, Job.objects.filter(is_active=True), [s.name for s in resume.skills.all()], limit=12)
    return render(request, "jobs/recommendations.html", {"resumes": resumes, "resume": resume, "recs": recs})
