from django.urls import path

from . import views

app_name = "jobs"
urlpatterns = [
    path("", views.job_list, name="list"),
    path("recommended/", views.recommendations, name="recommended"),
    path("<int:pk>/", views.job_detail, name="detail"),
]
