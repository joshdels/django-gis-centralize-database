from django.urls import path
from . import views

app_name = "file"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("upload/", views.upload_file, name="upload"),
    path("project/<int:pk>/", views.project_detail, name="project-detail"),
    path("project/<int:pk>/download", views.download_file, name="download-file"),
    path("project/<int:pk>/update", views.update_file, name="update-file"),
    path("test", views.test, name="test"),
    path("test-file", views.test_files, name="test-file"),
]
