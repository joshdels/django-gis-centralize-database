from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404

from accounts.models import Profile


def sidebar_context(request):
    profile = None

    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
    profile = get_object_or_404(Profile, user=request.user)

    return {
        "sidebar_menu": [
            {
                "label": "Management",
                "icon": "database",
                "url": reverse_lazy("gis_database:dashboard"),
            },
            {
                "label": "Analytics",
                "icon": "chart-pie",
                "url": reverse_lazy("gis_database:analytics"),
            },
            {
                "label": "Guides",
                "icon": "notebook-text",
                "url": reverse_lazy("gis_database:guides"),
            },
        ],
        "profile": profile,
    }
