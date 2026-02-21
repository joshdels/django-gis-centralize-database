import json

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from django.urls import reverse_lazy
from django.core.paginator import Paginator

from ..models import Project, File, FileActivity
from accounts.models import Profile
from ..models import ProjectMembership


def get_user_storage_context(request):
    uploads = Project.objects.filter(owner=request.user, is_deleted=False).order_by(
        "-created_at"
    )
    paginator = Paginator(uploads, 3)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    total_bytes = sum(
        f.file.size for f in File.objects.filter(project__owner=request.user) if f.file
    )

    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None

    if profile and profile.storage_limit_mb > 0:
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
        }
    )
    return render(request, "pages/dashboard.html", context)


def analytics(request):
    projects = Project.objects.filter(is_deleted=False).prefetch_related(
        "membership__user"
    )

    context = get_user_storage_context(request)

    members_dict = {}

    for project in projects:
        members = project.membership.select_related("user").exclude(user=project.owner)
        for m in members:
            if m.user.id not in members_dict:

                m.all_projects = [
                    up.project
                    for up in ProjectMembership.objects.filter(
                        user=m.user
                    ).select_related("project")
                    if not up.project.is_deleted
                ]
                m.current_projects = [project]
                members_dict[m.user.id] = m
            else:
                members_dict[m.user.id].current_projects.append(project)

        members_list = list(members_dict.values())

    context.update(
        {
            "members": members_list,
        }
    )

    return render(request, "pages/analytics.html", context)
