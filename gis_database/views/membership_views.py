from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.models import User

from ..models import Project, ProjectMembership


@login_required
@require_POST
def add_member(request, project_id):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)

    username_or_email = request.POST.get("username")
    try:
        user = User.objects.get(username=username_or_email)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("project-detail", pk=project.id)

    membership, created = ProjectMembership.objects.get_or_create(
        user=user,
        project=project,
        defaults={"role": "viewer", "invited_by": request.user},
    )

    if not created:
        messages.info(request, f"{user.username} is already a member.")
    else:
        messages.success(request, f"{user.username} added as a member.")

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
