import os
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ValidationError

from .models import Project
from .forms import ProjectForm


# Utility
def get_user_storage_context(user):
    """Calculates storage stats for a specific user."""
    uploads = Project.objects.filter(user=user).order_by("-created_at")

    total_bytes = sum(p.file.size for p in uploads if p.file)
    total_mb = total_bytes / (1024 * 1024)

    remaining_mb = max(Project.MAX_STORAGE_MB - total_mb, 0)
    storage_percent = min(round((remaining_mb / Project.MAX_STORAGE_MB) * 100, 1), 100)

    return {
        "uploads": uploads,
        "storage_percentage": storage_percent,
        "remaining_mb": round(remaining_mb, 1),
        "max_storage": round(Project.MAX_STORAGE_MB, 1),
    }


# Public Views
def home(request):
    return render(request, "pages/home.html")


def test_files(request):
    return render(request, "test/test.html")


def test(request):
    return HttpResponse("<h1>Hello Test</h>")


@login_required
@ensure_csrf_cookie
def dashboard(request):
    context = get_user_storage_context(request.user)
    return render(request, "pages/dashboard.html", context)


@login_required
def upload_file(request):
    context = get_user_storage_context(request.user)

    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            try:
                obj.save()
                return redirect("file:dashboard")
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = ProjectForm()

    return render(request, "pages/upload.html", {"form": form})


@login_required
def layer_detail(request, pk):
    layer = get_object_or_404(Project, pk=pk)
    return render(request, "pages/detail.html", {"layer": layer})
