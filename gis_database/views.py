import os
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ValidationError

from .models import Project
from .forms import ProjectForm


def home(request):
    return render(request, "pages/home.html")


def test_files(request):
    return render(request, "test/test.html")


def test(request):
    return HttpResponse("<h1>Hello Test</h>")


@login_required
@ensure_csrf_cookie
def dashboard(request):
    uploads = Project.objects.filter(user=request.user).order_by("-created_at")

    total_bytes = 0
    for p in uploads:
        if p.file:
            try:
                print(f"{p.file.name} -> {p.file.size} bytes")  # debug
                total_bytes += p.file.size
            except Exception as e:
                print("Error reading file size:", e)

    total_mb = total_bytes / (1024 * 1024)
    remaining_mb = max(Project.MAX_STORAGE_MB - total_mb, 0)
    storage_percent_remaining = min(
        round((remaining_mb / Project.MAX_STORAGE_MB) * 100, 1), 100
    )

    print("Total MB:", total_mb, "Storage %:", storage_percent_remaining)

    return render(
        request,
        "pages/dashboard.html",
        {
            "uploads": uploads,
            "storage_percentage": storage_percent_remaining,
            "remaining_mb": round(remaining_mb, 1),
            "max_storage": Project.MAX_STORAGE_MB
        },
    )


@login_required
def upload_file(request):
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
