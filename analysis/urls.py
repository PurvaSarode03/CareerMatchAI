from django.urls import path

from . import views

app_name = "analysis"
urlpatterns = [
    path("new/", views.new, name="new"),
    path("history/", views.history, name="history"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/delete/", views.delete, name="delete"),
]
