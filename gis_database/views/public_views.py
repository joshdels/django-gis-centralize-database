from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy


sidebar_menu = [
    {"label": "Storage", "icon": "database", "url": "/dashboard/"},
    {"label": "Analytics", "icon": "chart-pie", "url": reverse_lazy("analytics")},
    {"label": "Guides", "icon": "notebook-text", "url": reverse_lazy("guides")},
]


def home(request):
    return render(request, "pages/home.html")


def guides(request):
    return render(request, "pages/guides.html", {"sidebar_menu": sidebar_menu})


def guides_qgis(request):
    return render(request, "components/guides/qgis.html")


def test_files(request):
    return render(request, "pages/test.html")


def test(request):
    return HttpResponse("<h1>Hello Test</h1>")
