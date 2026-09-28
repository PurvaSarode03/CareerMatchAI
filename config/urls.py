from django.conf import settings
from django.conf.urls.static import static  # noqa: F401  (media served only in DEBUG)
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Resume Analyzer Admin"
admin.site.site_title = "Resume Analyzer"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("resumes/", include("resumes.urls")),
    path("jobs/", include("jobs.urls")),
    path("analysis/", include("analysis.urls")),
    path("", include("dashboard.urls")),
]
# NOTE: uploaded resumes are private; they are NOT exposed via MEDIA_URL.
# They are served only through an authenticated view (resumes:download).
