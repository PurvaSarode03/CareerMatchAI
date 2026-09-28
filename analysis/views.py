from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from jobs.models import Job

from .forms import AnalysisForm
from .models import Analysis
from .services import run_analysis


@login_required
def new(request):
    if not request.user.resumes.exists():
        messages.info(request, "Upload a resume first.")
        return redirect("resumes:upload")
    initial = {}
    if request.GET.get("job"):
        initial["job"] = Job.objects.filter(pk=request.GET["job"], is_active=True).first()
    if request.GET.get("resume"):
        initial["resume"] = request.user.resumes.filter(pk=request.GET["resume"]).first()
    form = AnalysisForm(request.user, request.POST or None, request.FILES or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        a = run_analysis(request.user, d["resume"], d["jd_text"], job=d.get("job"), title=d.get("job_title", ""))
        return redirect("analysis:detail", pk=a.pk)
    return render(request, "analysis/new.html", {"form": form})


@login_required
def detail(request, pk):
    a = get_object_or_404(Analysis.objects.select_related("resume", "job"), pk=pk, user=request.user)
    return render(request, "analysis/detail.html", {"a": a})


@login_required
def history(request):
    qs = request.user.analyses.select_related("resume", "job")
    if q := request.GET.get("q"):
        qs = qs.filter(job_title__icontains=q)
    if request.GET.get("sort") == "score":
        qs = qs.order_by("-score")
    page = Paginator(qs, 10).get_page(request.GET.get("page"))
    return render(request, "analysis/history.html", {"page": page, "q": request.GET.get("q", ""), "sort": request.GET.get("sort", "")})


@login_required
@require_POST
def delete(request, pk):
    get_object_or_404(Analysis, pk=pk, user=request.user).delete()
    messages.info(request, "Analysis deleted.")
    return redirect("analysis:history")
