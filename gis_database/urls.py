from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("guides/", views.guides, name="guides"),
    path("analytics/", views.analytics, name="analytics"),
    
    path("upload/", views.upload_project, name="upload-project"),
    path("create/", views.create_project, name="create-project"),
    path("project/<int:pk>/details", views.project_detail, name="project-details"),
    path("project/<int:pk>/analytics", views.project_analytics, name="project-analytics"),
    path("project/<int:pk>/delete", views.delete_project, name="project-delete"),
    path("project/<int:pk>/download", views.download_project, name="download-file"),
    path("project/<int:pk>/update", views.update_file, name="update-file"),
    
    path("project/<int:project_id>/add-member/", views.add_member, name="add_member"),
    path('project/<int:project_id>/search-users/', views.search_users, name="search_users"),
    path("project/<int:project_id>/remove-member/<int:user_id>/", views.remove_member, name="remove-member"),
    
    path("test", views.test, name="test"),
    path("test-file/", views.test_files, name="test-file"),
    path("guides/qgis", views.guides_qgis, name="qgis")
]
