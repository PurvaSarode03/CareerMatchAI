import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ai_engine.suggestions import build_suggestions, resume_health
from ai_engine.text_extraction import ExtractionError

from .forms import ResumeUploadForm
from .models import Resume
from .services import process_resume, resume_to_dict


def _own(request, pk):
    return get_object_or_404(Resume, pk=pk, user=request.user)


@login_required
def resume_list(request):
    return render(request, "resumes/list.html", {"resumes": request.user.resumes.prefetch_related("skills")})


@login_required
def upload(request):
    form = ResumeUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        f = form.cleaned_data["file"]
        resume = Resume(user=request.user, original_filename=os.path.basename(f.name)[:255],
                        title=form.cleaned_data["title"] or os.path.splitext(os.path.basename(f.name))[0][:120], file=f)
        resume.save()
        try:
            process_resume(resume)
        except ExtractionError as exc:
            resume.delete()
            form.add_error("file", str(exc))
        except Exception:
            resume.delete()
            form.add_error("file", "Something went wrong while analysing this file. Please try another one.")
        else:
            messages.success(request, "Resume uploaded and analysed.")
            return redirect("resumes:detail", pk=resume.pk)
    return render(request, "resumes/upload.html", {"form": form})


@login_required
def detail(request, pk):
    resume = _own(request, pk)
    data = resume_to_dict(resume)
    skills_by_cat = {}
    for s in resume.skills.all():
        skills_by_cat.setdefault(s.get_category_display(), []).append(s.name)
    return render(request, "resumes/detail.html", {
        "resume": resume, "skills_by_cat": dict(sorted(skills_by_cat.items())),
        "health": resume_health(data), "suggestions": build_suggestions(data),
    })


@login_required
@require_POST
def reanalyze(request, pk):
    resume = _own(request, pk)
    try:
        process_resume(resume)
        messages.success(request, "Resume re-analysed with the latest skill list.")
    except ExtractionError as exc:
        messages.error(request, str(exc))
    return redirect("resumes:detail", pk=pk)


@login_required
@require_POST
def delete(request, pk):
    _own(request, pk).delete()
    messages.info(request, "Resume deleted.")
    return redirect("resumes:list")


@login_required
def download(request, pk):
    """Authenticated, owner-only file access — uploads are never publicly served."""
    resume = _own(request, pk)
    return FileResponse(resume.file.open("rb"), as_attachment=True, filename=resume.original_filename or "resume")
