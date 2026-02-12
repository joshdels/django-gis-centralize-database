from django.urls import path
from . import views

app_name = "file"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("upload/", views.upload_project, name="upload-project"),
    path("create/", views.create_project, name="create-project"),
    path("project/<int:pk>/sync", views.project_sync, name="project-sync"),
    path("project/<int:pk>/detail", views.project_detail, name="project-detail"),
    path("project/<int:pk>/delete", views.delete_project, name="project-delete"),
    path("project/<int:pk>/download", views.download_project, name="download-file"),
    path("project/<int:pk>/update", views.update_file, name="update-file"),
    
    path("test", views.test, name="test"),
    path("test-file", views.test_files, name="test-file"),
    path("guides", views.guides, name="guides"),
    path("guides/qgis", views.guides_qgis, name="qgis")
]
