import os
import zipfile
from io import BytesIO

from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Sum
from django.db import transaction

from .models import Project, File, FileActivity
from accounts.models import Profile
from .forms import ProjectForm
from .utils import compute_hash


# -------------------------------
# Utilities
# -------------------------------
def get_user_storage_context(user):
    uploads = Project.objects.filter(owner=user, is_deleted=False).order_by(
        "-created_at"
    )

    total_bytes = sum(
        f.file.size for f in File.objects.filter(project__owner=user) if f.file
    )

    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = None

    if profile:
        remaining_mb = round(profile.remaining_storage_bytes() / (1024 * 1024), 1)
        max_storage = profile.storage_limit_mb
    else:
        remaining_mb = 0
        max_storage = 0

    used_percent = min(
        round((total_bytes / (profile.storage_limit_mb * 1024 * 1024)) * 100, 1),
        100,
    )

    return {
        "uploads": uploads,
        "storage_percentage": used_percent,
        "remaining_mb": remaining_mb,
        "max_storage": max_storage,
    }


def unset_latest(user, project, file_name):
    """Helper to unset is_latest for previous files if the are the same hash"""
    File.objects.filter(
        owner=user,
        project=project,
        name=file_name,
        is_latest=True,
    ).update(is_latest=False)


# -------------------------------
# Public Views
# -------------------------------
def home(request):
    return render(request, "pages/home.html")


def test_files(request):
    return render(request, "components/map/map-project.html")


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
def project_sync(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    return render(request, "components/project/project-sync.html", {"project": project})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    return render(
        request, "components/project/project-detail.html", {"project": project}
    )


@login_required
def upload_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, owner=request.user)

        if form.is_valid():
            uploaded_file = request.FILES["uploaded_file"]

            if uploaded_file.size > File.MAX_FILE_SIZE:
                form.add_error("uploaded_file", "File exceeds maximum size (100MB)")
                return render(request, "pages/uploaded.html", {"form": form})

            with transaction.atomic():
                if not request.user.profile.can_store(uploaded_file.size):
                    form.add_error(
                        "uploaded_file", "Storage limit exceeded during upload."
                    )
                    return render(request, "pages/upload.html", {"form": form})

                form.save()
                return redirect("file:dashboard")
    else:
        form = ProjectForm(owner=request.user)

    return render(request, "pages/upload.html", {"form": form})


@login_required
def download_project(request, pk):
    """
    Download all latest ProjectFiles of a project as a ZIP.
    """
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    files = project.files.filter(is_latest=True, project__is_deleted=False)

    if not files.exists():
        raise Http404("No files in this project.")

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for pf in files:
            if pf.file:
                filename = os.path.basename(pf.file.name)
                with pf.file.open("rb") as f:
                    zip_file.writestr(filename, f.read())

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{project.name}.zip"'
    return response


@login_required
def update_file(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)

    project_file = project.files.filter(is_latest=True).order_by("-version").first()

    if not project_file:
        raise Http404("No latest file to update")

    if request.method == "POST":
        uploaded_file = request.FILES.get("uploaded_file")
        if not uploaded_file:
            raise Http404("No file uploaded")

        profile = request.user.profile
        if not profile.can_store(uploaded_file.size):
            return HttpResponse("Storage quota exceeded", status=400)

        new_hash = compute_hash(uploaded_file)

        if new_hash == project_file.hash:
            return HttpResponse("No changes detected", status=400)

        with transaction.atomic():
            unset_latest(request.user, project, project_file.name)

            new_file = File.objects.create(
                project=project,
                owner=request.user,
                name=project_file.name,
                file_folder=project_file.file_folder,
                file=uploaded_file,
                hash=new_hash,
                version=project_file.version + 1,
                is_latest=True,
            )

            FileActivity.objects.create(
                file=new_file,
                owner=request.user,
                action="upload_new_version",
            )

        return redirect("file:project-sync", pk=project.id) 

    return render(
        request,
        "pages/update_file.html",
        {
            "project_file": project_file,
            "project": project,
        },
    )


@login_required
def delete_file(request, pk):
    """
    Delete a single file of file (hard delete)
    """
    project_file = get_object_or_404(File, pk=pk, project__owner=request.user)
    if request.method == "POST":
        project_file.delete()
        return redirect("file:project-detail", pk=project_file.project.pk)

    # Temporary fix. will make the delete.html
    return render(request, "components/file/file_delete.html", {"file": project_file})


@login_required
def delete_project(request, pk):
    """
    Delete a project and all associated files and versions.
    """
    project_file = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == "POST":
        project_file.delete()
        return redirect("file:dashboard")
    return render(
        request, "components/project/project_delete.html", {"project": project_file}
    )


@login_required
def delete_project_soft(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == "POST":
        project.soft_delete()
    return redirect("file:dashboard")
