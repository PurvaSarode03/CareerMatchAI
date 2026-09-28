from django.urls import path

from . import views

app_name = "resumes"
urlpatterns = [
    path("", views.resume_list, name="list"),
    path("upload/", views.upload, name="upload"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/reanalyze/", views.reanalyze, name="reanalyze"),
    path("<int:pk>/delete/", views.delete, name="delete"),
    path("<int:pk>/download/", views.download, name="download"),
]
