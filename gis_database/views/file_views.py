import os
from io import BytesIO

from django.http import HttpResponse, Http404
import zipfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Sum
from django.db import transaction
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.models import User

from ..models import Project, File, FileActivity, ProjectMembership
from accounts.models import Profile
from ..forms import ProjectForm, CreateProjectForm

from ..utils import compute_hash


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


def unset_latest(user, project, file_name):
    """Helper to unset is_latest for previous files if the are the same hash"""
    File.objects.filter(
        owner=user,
        project=project,
        name=file_name,
        is_latest=True,
    ).update(is_latest=False)

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

