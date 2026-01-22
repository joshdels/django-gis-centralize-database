import os
import zipfile
from io import BytesIO
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Project, ProjectFile
from .forms import ProjectForm, ProjectFileUpdateForm


# -------------------------------
# Utilities
# -------------------------------
def get_user_storage_context(user):
    """
    Calculate total storage usage for a user and return context for templates.
    """
    uploads = Project.objects.filter(user=user).order_by("-created_at")

    total_bytes = 0
    for project in uploads:
        for pf in project.files.all():
            if pf.file:
                total_bytes += pf.file.size
            for v in pf.versions.all():
                if v.file:
                    total_bytes += v.file.size

    total_mb = total_bytes / (1024 * 1024)
    remaining_mb = max(Project.MAX_STORAGE_MB - total_mb, 0)
    used_percent = min(round((total_mb / Project.MAX_STORAGE_MB) * 100, 1), 100)

    return {
        "uploads": uploads,
        "storage_percentage": used_percent,
        "remaining_mb": round(remaining_mb, 1),
        "max_storage": Project.MAX_STORAGE_MB,
    }


# -------------------------------
# Public Views
# -------------------------------
def home(request):
    return render(request, "pages/home.html")


def test_files(request):
    return render(request, "test/test.html")


def test(request):
    return HttpResponse("<h1>Hello Test</h1>")


# -------------------------------
# Authenticated Views
# -------------------------------
@login_required
@ensure_csrf_cookie
def dashboard(request):
    context = get_user_storage_context(request.user)
    return render(request, "pages/dashboard.html", context)


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    return render(request, "pages/project-details.html", {"project": project})


@login_required
def upload_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user 
            obj.save()
            # handle file if uploaded
            if "file" in request.FILES:
                ProjectFile.objects.create(project=obj, file=request.FILES["file"])
            return redirect("file:dashboard")
    else:
        form = ProjectForm(user=request.user) 

    return render(request, "pages/upload.html", {"form": form})



@login_required
def download_project(request, pk):
    """
    Download an entire project as a ZIP file, including only the latest version of each file.
    """
    project = get_object_or_404(Project, pk=pk, user=request.user)
    files = project.files.all()  # all ProjectFile objects

    if not files.exists():
        raise Http404("No files in this project.")

    # Create an in-memory zip
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for pf in files:
            if pf.file:
                filename = os.path.basename(pf.file.name)
                zip_file.writestr(filename, pf.file.read())

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{project.name}.zip"'
    return response


@login_required
def update_file(request, pk):
    project_file = get_object_or_404(ProjectFile, pk=pk)

    if project_file.project.user != request.user:
        raise Http404("You do not have permission to update this file.")

    if request.method == "POST":
        form = ProjectVersionForm(request.POST, request.FILES)
        if form.is_valid():
            new_file = form.cleaned_data["file"]

            # --- Save old version first ---
            from django.db import transaction

            with transaction.atomic():
                # Determine next version number
                last_version = project_file.versions.first()
                next_version = (last_version.version_number if last_version else 0) + 1

                # Create new ProjectFileVersion for the old file
                ProjectFileVersion.objects.create(
                    project_file=project_file,
                    file=project_file.file,  # snapshot of current file
                    version_number=next_version,
                )

                # Update ProjectFile with new file
                project_file.file = new_file
                project_file.save(update_fields=["file", "updated_at"])

            return redirect("file:project-detail", pk=project_file.project.pk)
    else:
        form = ProjectVersionForm()

    return render(
        request,
        "pages/update_file.html",
        {"form": form, "project_file": project_file},
    )


@login_required
def delete_file(request, pk):
    """
    Delete a project and all associated files and versions.
    """
    project = get_object_or_404(Project, pk=pk, user=request.user)
    if request.method == "POST":
        project.delete()
        return redirect("file:dashboard")
    return render(request, "components/project_delete.html", {"project": project})


@login_required
def project_file_versions(request, file_id):
    """
    List all versions for a specific ProjectFile.
    """
    project_file = get_object_or_404(
        ProjectFile, pk=file_id, project__user=request.user
    )
    versions = project_file.versions.all()
    return render(
        request,
        "pages/file_versions.html",
        {"project_file": project_file, "versions": versions},
    )
