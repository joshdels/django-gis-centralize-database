import os

from django.db.models import Q, UniqueConstraint
from django.db import models
from django.conf import settings
from django.utils import timezone


def file_upload_path(instance, filename):
    base_name, ext = os.path.splitext(filename)
    user_id = instance.owner.id if instance.owner else "anon"
    project_name = instance.project.name if instance.project else "default_project"
    file_folder = instance.file_folder or base_name.replace(" ", "_")
    return f"uploads/{user_id}/{project_name}/{file_folder}/{base_name}_v{instance.version}{ext}"


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=500, null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    is_deleted = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    # ----- Domain Constraints ------
    MAX_STORAGE_MB = 50

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])


class File(models.Model):

    name = models.CharField(max_length=255)
    file_folder = models.CharField(max_length=255, blank=True, null=True)

    file = models.FileField(upload_to=file_upload_path)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    project = models.ForeignKey(Project, related_name="files", on_delete=models.CASCADE)
    hash = models.CharField(max_length=64, db_index=True)
    version = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    is_latest = models.BooleanField(default=False, db_index=True)
    # ----- Domain Constraints ------
    MAX_FILE_SIZE = 100 * 1024 * 1024

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            UniqueConstraint(
                fields=["project", "name"],
                condition=Q(is_latest=True),
                name="one_latest_file_per_logical_file",
            )
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class FileActivity(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    action = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["action", "created_at"])]
