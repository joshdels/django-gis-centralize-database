from django.urls import reverse_lazy

def sidebar_context(request):
    return {
        "sidebar_menu": [
            {"label": "Management", "icon": "database", "url": "/dashboard/"},
            {"label": "Analytics", "icon": "chart-pie", "url": reverse_lazy("analytics")},
            {"label": "Guides", "icon": "notebook-text", "url": reverse_lazy("guides")},
        ]
    }
