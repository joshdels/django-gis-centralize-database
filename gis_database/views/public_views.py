from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy


def home(request):
    return render(request, "pages/home.html")


def guides(request):
    return render(request, "pages/guides.html")


def guides_qgis(request):
    return render(request, "components/guides/qgis.html")


def test_files(request):
    return render(request, "pages/test.html")


def test(request):
    return HttpResponse("<h1>Hello Test</h1>")
