from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, redirect, get_object_or_404
from .models import Project
from .forms import ProjectForm
from django.shortcuts import redirect
import os


MAX_UPLOADS = 3
MAX_STORAGE_MB = 5


def user_storage_used(user):
    total = 0
    for upload in Project.objects.filter(user=user):
        if upload.file and os.path.exists(upload.file.path):
            total += os.path.getsize(upload.file.path)
    return total / (1024 * 1024)


def home(request):
    return render(request, "pages/home.html")


@login_required
@ensure_csrf_cookie
def dashboard(request):
    uploads = Project.objects.filter(user=request.user).order_by("-created_at")

    return render(
        request,
        "pages/dashboard.html",
        {
            "uploads": uploads,
        },
    )


@login_required
def upload_file(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES)
        file_size_mb = request.FILES["file"].size / (1024 * 1024)

        # Max uploads check
        if Project.objects.filter(user=request.user).count() >= MAX_UPLOADS:
            return render(
                request,
                "pages/upload.html",
                {"form": form, "error": f"Upload limit reached ({MAX_UPLOADS} files)."},
            )

        # Max storage check
        if user_storage_used(request.user) + file_size_mb > MAX_STORAGE_MB:
            return render(
                request,
                "pages/upload.html",
                {
                    "form": form,
                    "error": f"Storage limit reached ({MAX_STORAGE_MB} MB).",
                },
            )

        # Save file
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return redirect("file:dashboard")
    else:
        form = ProjectForm()
    return render(request, "pages/upload.html", {"form": form})


@login_required
def layer_detail(request, pk):
    layer = get_object_or_404(Project, pk=pk)
    return render(request, "pages/detail.html", {"layer": layer})
