import os

from django.db import models
from django.db.models import Q, UniqueConstraint, Sum
from django.core.exceptions import ValidationError
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
        unique_together = ("owner", "name")

    def __str__(self):
        return self.name

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def used_storage_bytes(self):
        return sum(f.file.size for f in self.files.all() if f.file)

    def has_storage_for(self, new_file_size):
        max_bytes = self.MAX_STORAGE_MB * 1024 * 1024
        return self.used_storage_bytes() + new_file_size <= max_bytes


class File(models.Model):

    name = models.CharField(max_length=255, blank=True, null=True)
    file_folder = models.CharField(max_length=255, blank=True, null=True)

    file = models.FileField(upload_to=file_upload_path)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )

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
                fields=["project", "hash"],
                name="no_duplicate_file_content_per_project",
            )
        ]

    def clean(self):
        if self.file:

            if self.file.size > self.MAX_FILE_SIZE:
                raise ValidationError(
                    f"File too large. Max size is {self.MAX_FILE_SIZE // (1024 * 1024)} MB."
                )
            if self.owner and not self.owner.profile.can_store(self.file.size):
                raise ValidationError("User storage quota exceeded")

    def delete(self, *args, **kwargs):
        if self.file:
            storage = self.file.storage
            try:
                path = self.file.path
            except NotImplementedError:
                path = None
        else:
            storage = None
            path = None

        super().delete(*args, **kwargs)

        if storage and path and storage.exists(path):
            storage.delete(path)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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
