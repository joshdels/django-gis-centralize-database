from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Q

from ..models import Project, ProjectMembership

User = get_user_model()


@login_required
@require_POST
def add_member(request, project_id):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)

    username = request.POST.get("username")
    user = get_object_or_404(User, username=username)

    ProjectMembership.objects.get_or_create(
        user=user,
        project=project,
        defaults={"role": "editor", "invited_by": request.user},
    )

    members = ProjectMembership.objects.filter(project=project)

    context = {
        "members": members,
        "project": project,
        "can_manage": True,
    }

    # what is this??? 
    if request.headers.get("HX-Request"):
        return render(request, "components/project/members/html", context)


    return redirect("project-detail", pk=project.id)


@login_required
@require_POST
def remove_member(request, project_id, user_id):
    project = get_object_or_404(Project, pk=project_id)

    # Permission check (recommended: use your can_manage method)
    if not project.can_manage(request.user):
        messages.error(request, "You do not have permission to remove members.")
        return redirect("project-detail", pk=project.id)

    # Prevent removing the owner
    if project.owner.id == user_id:
        messages.error(request, "You cannot remove the project owner.")
        return redirect("project-detail", pk=project.id)

    membership = ProjectMembership.objects.filter(
        project=project, user_id=user_id
    ).first()

    if not membership:
        messages.error(request, "Member not found.")
    else:
        membership.delete()
        messages.success(request, "Member removed successfully.")

    return redirect("project-detail", pk=project.id)


User = get_user_model()


@login_required
def search_users(request, project_id):
    query = request.GET.get("q", "")

    users = []

    existing_member_ids = ProjectMembership.objects.filter(
        project_id=project_id
    ).values_list("user_id", flat=True)

    users = (
        User.objects.fiter(Q(username__icontains=query) | Q(email__icontains=query))
        .exclued(id__in=existing_member_ids)
        .exclude(id=request.user.id)[:10]
    )

    context = {"users": users, "project_id": project_id}

    return render(request, "components/project/user_search_result.html", context)
