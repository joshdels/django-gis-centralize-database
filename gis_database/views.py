import os
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ValidationError

from .models import Project, ProjectVersion
from .forms import ProjectForm, ProjectVersionForm


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
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, "pages/project-details.html", {"project": project})


@login_required
def upload_project(request):
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
def download_file(request, pk):
    """Force download of a user's project file."""
    project = get_object_or_404(Project, pk=pk)

    if project.user != request.user:
        raise Http404("You do not have permission to download this file.")

    if not project.file:
        raise Http404("File not found.")

    try:
        response = FileResponse(
            project.file.open("rb"),
            as_attachment=True,
            filename=os.path.basename(project.file.name),
        )
        return response
    except FileNotFoundError:
        raise Http404("File not found.")


@login_required
def update_file(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # Ownership check
    if project.user != request.user:
        raise Http404("You do not have permission to update this project.")

    if request.method == "POST":
        form = ProjectVersionForm(request.POST, request.FILES)
        if form.is_valid():
            new_file = form.cleaned_data["file"]

            # --- STORAGE VALIDATION ---
            user_projects = Project.objects.filter(user=request.user, archived=False)
            total_bytes = 0
            for p in user_projects:
                # Exclude current project's file since it will be replaced
                if p.pk != project.pk and p.file:
                    total_bytes += p.file.size
                for v in p.versions.all():
                    if v.file:
                        total_bytes += v.file.size

            total_bytes += new_file.size
            total_mb = total_bytes / (1024 * 1024)

            if total_mb > Project.MAX_STORAGE_MB:
                form.add_error(
                    "file", f"Total storage exceeded ({Project.MAX_STORAGE_MB} MB max)."
                )
            else:
                # --- CREATE NEW VERSION ---
                last_version = project.versions.first()  # latest version
                new_version_number = (
                    last_version.version_number if last_version else 0
                ) + 1

                new_version = ProjectVersion.objects.create(
                    project=project,
                    file=new_file,
                    version_number=new_version_number,
                )

                # --- UPDATE MAIN PROJECT FILE + updated_at ---
                from django.utils import timezone

                project.file = new_version.file
                project.updated_at = timezone.now()  # force updated_at update
                project.save(update_fields=["file", "updated_at"])

                return redirect("file:project-detail", pk=project.pk)
    else:
        form = ProjectVersionForm()

    return render(request, "pages/update_file.html", {"form": form, "project": project})

@login_required
def delete_file(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        project.delete()
        return redirect('file:dashboard')
    return render(request, "components/project_delete.html", {'project': project})
    
    