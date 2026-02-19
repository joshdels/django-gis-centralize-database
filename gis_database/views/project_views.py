import os
import zipfile
from io import BytesIO

from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction

from ..models import Project, ProjectMembership, FileActivity
from ..forms import CreateProjectForm


@transaction.atomic
def create_project(request):
    form = CreateProjectForm(request.POST or None)

    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()

        ProjectMembership.objects.get_or_create(
            project=project,
            role="admin",
            invited_by=request.user,
        )

        FileActivity.objects.create(
            project=project,
            project_name_snapshot=project.name,
            action="new project created",
            owner=request.user,
        )

        return redirect("dashboard")

    return render(request, "components/project/create-layout.html", {"form": form})


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


def delete_project(request, pk):
    """
    Delete a project and all associated files and versions.
    """
    project = get_object_or_404(Project, pk=pk, owner=request.user)

    if request.method == "POST":
        FileActivity.objects.create(
            project=project,
            project_name_snapshot=project.name,
            action="project deleted",
            owner=request.user,
        )

        project.delete()

        return redirect("dashboard")
    return render(
        request, "components/project/project_delete.html", {"project": project}
    )


def delete_project_soft(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == "POST":
        project.soft_delete()

        FileActivity.objects.create(
            project=project,
            project_name_snapshot=project.name,
            action="project deleted",
            owner=request.user,
        )
    return redirect("dashboard")


def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    latest_file = project.files.filter(is_latest=True).order_by("-uploaded_at")
    all_files = project.files.all().order_by("-version")

    member = project.membership.select_related("user").all()
    role = project.get_user_role(request.user)
    can_manage = project.can_manage(request.user)

    context = {
        "project": project,
        "latest_files": latest_file,
        "all_files": all_files,
        "role": role,
        "members": member,
        "can_manage": can_manage,
    }

    return render(request, "components/project/_detail-layout.html", context)


def project_analytics(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    role = project.get_user_role(request.user)
    member = project.membership.select_related("user").all()

    can_manage = project.can_manage(request.user)

    context = {
        "project": project,
        "role": role,
        "members": member,
        "can_manage": can_manage,
    }

    return render(request, "components/analytics/_analysis-layout.html", context)
