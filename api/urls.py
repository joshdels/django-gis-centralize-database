from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, LoginView, LogoutView

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
    path("login/", LoginView.as_view(), name="api-login"),
    path("logout/", LogoutView.as_view(), name="api-logout"),
]
