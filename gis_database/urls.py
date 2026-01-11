from django.urls import path
from . import views

app_name = "file"

urlpatterns = [
    path("", views.home, name="home"),
    path("upload/", views.upload_file, name="upload"),
    path("layer/<int:pk>/", views.layer_detail, name="detail"),
]
