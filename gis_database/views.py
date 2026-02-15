import os
import zipfile
from io import BytesIO

from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Sum
from django.db import transaction
from django.urls import reverse_lazy
from django.core.paginator import Paginator

from .models import Project, File, FileActivity
from accounts.models import Profile
from .forms import ProjectForm, CreateProjectForm

from .utils import compute_hash

sidebar_menu = [
    {"label": "Storage", "icon": "database", "url": "/dashboard/"},
    {"label": "Analytics", "icon": "chart-pie", "url": reverse_lazy("analytics")},
    {"label": "Guides", "icon": "notebook-text", "url": reverse_lazy("guides")},
]


# -------------------------------
# Utilities
# -------------------------------
def get_user_storage_context(request):
    uploads = Project.objects.filter(owner=request.user, is_deleted=False).order_by(
        "-created_at"
    )
    paginator = Paginator(uploads, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    total_bytes = sum(
        f.file.size for f in File.objects.filter(project__owner=request.user) if f.file
    )

    try:
        profile = request.user.profile
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
        "page_obj": page_obj,
        "uploads": page_obj,
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


def guides(request):
    return render(request, "pages/guides.html", {"sidebar_menu": sidebar_menu})

def analytics(request):
    return render(request, "pages/analytics.html", {"sidebar_menu": sidebar_menu})


def guides_qgis(request):
    return render(request, "components/guides/qgis.html")


def test_files(request):
    return render(request, "pages/test.html")


def test(request):
    return HttpResponse("<h1>Hello Test</h1>")


# -------------------------------
# Authenticated Views
# -------------------------------


@login_required
@ensure_csrf_cookie
def dashboard(request):

    projects = Project.objects.filter(owner=request.user, is_deleted=False)

    chart_labels = [p.name for p in projects]
    chart_data = [round(p.used_storage_bytes() / (1024 * 1024), 2) for p in projects]

    context = get_user_storage_context(request)
    file_activities = FileActivity.objects.filter(owner=request.user)
    context.update(
        {
            "file_activities": file_activities,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
            "sidebar_menu": sidebar_menu,
        }
    )
    return render(request, "pages/dashboard.html", context)


@login_required
def project_sync(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    return render(
        request, "components/project/_detail-layout.html", {"project": project}
    )


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    return render(request, "components/analytic/detail.html", {"project": project})


@login_required
def upload_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, owner=request.user)

        if form.is_valid():
            uploaded_file = request.FILES["uploaded_file"]

            # size per file validation
            if uploaded_file.size > File.MAX_FILE_SIZE:
                form.add_error("uploaded_file", "File exceeds maximum size (100MB)")
                return render(request, "pages/upload.html", {"form": form})

            # storage quota of the user
            if not request.user.profile.can_store(uploaded_file.size):
                form.add_error("uploaded_file", "Storage limit exceeded during upload.")
                return render(request, "pages/upload.html", {"form": form})

            new_hash = compute_hash(uploaded_file)

            with transaction.atomic():
                project = form.save(commit=False)
                project.owner = request.user
                project.save()

                file_folder = os.path.splitext(uploaded_file.name)[0].replace(" ", "_")

                file_obj = File.objects.create(
                    project=project,
                    owner=request.user,
                    name=uploaded_file.name,
                    file_folder=file_folder,
                    file=uploaded_file,
                    hash=new_hash,
                    version=1,
                    is_latest=True,
                )

                FileActivity.objects.create(
                    file=file_obj,
                    owner=request.user,
                    action="uploaded new file",
                )

                return redirect("dashboard")
    else:
        form = ProjectForm(owner=request.user)

    return render(request, "pages/upload.html", {"form": form})


@transaction.atomic
def create_project(request):
    form = CreateProjectForm(request.POST or None)

    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        return redirect("dashboard")

    return render(request, "components/project/create-layout.html", {"form": form})


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
                stored_name = os.path.basename(pf.file.name)
                base_name, ext = os.path.splitext(stored_name)

                if "_v" in base_name:
                    base_name = base_name.rsplit("_v", 1)[0]

                download_name = f"{base_name}{ext}"

                with pf.file.open("rb") as f:
                    zip_file.writestr(download_name, f.read())

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{project.name}.zip"'
    return response


@login_required
def update_file(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    latest_file = project.files.filter(is_latest=True).order_by("-version").first()

    if request.method == "POST":
        form = ProjectForm(request.POST, request.FILES, owner=request.user)

        if form.is_valid():
            uploaded_file = form.cleaned_data["uploaded_file"]
            profile = request.user.profile

            if not profile.can_store(uploaded_file.size):
                # Future modal: storage quota exceeded
                return HttpResponse("Storage quota exceeded", status=400)

            new_hash = compute_hash(uploaded_file)

            with transaction.atomic():
                # Case 1: File with same hash exists -> mark as latest
                existing_file_with_hash = project.files.filter(hash=new_hash).first()
                if existing_file_with_hash:
                    unset_latest(request.user, project, existing_file_with_hash.name)
                    existing_file_with_hash.is_latest = True
                    existing_file_with_hash.save(update_fields=["is_latest"])
                    return redirect("project-detail", pk=project.id)

                # Case 2: Same name, different hash -> version increment
                latest_file_same_name = (
                    project.files.filter(name=uploaded_file.name)
                    .order_by("-version")
                    .first()
                )
                if latest_file_same_name:
                    unset_latest(request.user, project, latest_file_same_name.name)
                    version = latest_file_same_name.version + 1
                    file_folder = latest_file_same_name.file_folder
                    action = "added new file"
                else:
                    # Completely new file
                    version = 1
                    file_folder = os.path.splitext(uploaded_file.name)[0].replace(
                        " ", "_"
                    )
                    action = "create new file version"

                # Create new File
                new_file = File.objects.create(
                    project=project,
                    owner=request.user,
                    name=uploaded_file.name,
                    file_folder=file_folder,
                    file=uploaded_file,
                    hash=new_hash,
                    version=version,
                    is_latest=True,
                )

                # Log activity
                FileActivity.objects.create(
                    file=new_file,
                    owner=request.user,
                    action=action,
                )

            return redirect("project-sync", pk=project.id)

    else:
        form = ProjectForm(owner=request.user)

    return render(
        request,
        "pages/update_file.html",
        {
            "form": form,
            "project_file": latest_file,
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
        FileActivity.objects.create(
            file=project_file, owner=request.user, action="deleted file"
        )

        project_file.delete()
        return redirect("project-detail", pk=project_file.project.pk)

    return render(request, "components/file/file_delete.html", {"file": project_file})


@login_required
def delete_project(request, pk):
    """
    Delete a project and all associated files and versions.
    """
    project_file = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == "POST":
        project_file.delete()
        return redirect("dashboard")
    return render(
        request, "components/project/project_delete.html", {"project": project_file}
    )


@login_required
def delete_project_soft(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == "POST":
        project.soft_delete()
    return redirect("dashboard")
