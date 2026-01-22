from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction


def user_upload_path(instance, filename):
    """Uploads to a folder per user of the parent project."""
    try:
        # For ProjectFile
        user_id = instance.user.id
    except AttributeError:
        try:
            # For ProjectFileVersion
            user_id = instance.project_file.project.user.id
        except AttributeError:
            # fallback: unknown user
            user_id = "unknown"
    return f"uploads/user_{user_id}/{filename}"


class Project(models.Model):
    """
    Top-level container for user files.

    A Project groups files together and defines ownership,
    visibility, lifecycle state, and storage limits.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploads",
        help_text="The user who created this project",
    )

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    to_trash = models.BooleanField(default=False)

    # ----- Domain Constraints ------
    MAX_STORAGE_MB = 50

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name


class ProjectFile(models.Model):
    """
    Represents the *current / active* file for a project.

    Notes:
    - Only one ProjectFile exists per logical file.
    - Historical versions are stored in ProjectFileVersion.
    - `file` always points to the latest version.
    """

    project = models.ForeignKey(Project, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)

    # ----- Domain Constraints ------
    MAX_FILE_SIZE = 100 * 1024 * 1024

    def clean(self):
        user = self.project.user
        queryset = ProjectFile.objects.filter(project__user=user)

        if self.pk:
            queryset = queryset.exclude(pk=self.pk)

        total_used_bytes = sum(pf.file.size for pf in queryset)
        total_used_bytes += self.file.size

        if total_used_bytes / (1024 * 1024) > Project.MAX_STORAGE_MB:
            raise ValidationError(
                f"Total storage exceeded ({Project.MAX_STORAGE_MB} MB max)."
            )

        if self.file.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                f"File exceeds {self.MAX_FILE_SIZE // (1024*1024)} MB limit."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        storage = self.file.storage
        name = self.file.name
        super().delete(*args, **kwargs)
        storage.delete(name)

    def create_new_version(self, new_file):
        with transaction.atomic():
            last_version = self.versions.first()
            next_version = (last_version.version_number if last_version else 0) + 1

            version = ProjectFileVersion.objects.create(
                project_file=self,
                file=new_file,
                version_number=next_version,
            )

            self.file = version.file
            self.save(update_fields=["file"])

            return version


class ProjectFileVersion(models.Model):
    """
    Immutable snapshot of a file at a point in time.

    Used for:
    - Syncing to remote storage
    - Conflict resolution
    - History / rollback
    - Offline-first workflows
    """

    project_file = models.ForeignKey(
        ProjectFile,
        related_name="versions",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to=user_upload_path)
    version_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    # ---- SYNC FIELDS ----
    synced = models.BooleanField(default=False)
    checksum = models.CharField(max_length=64, blank=True, null=True)
    remote_path = models.CharField(max_length=512, blank=True, null=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-version_number"]
        unique_together = ("project_file", "version_number")
        indexes = [
            models.Index(fields=["synced"]),
        ]

    def __str__(self):
        return f"{self.project_file.project.name} v{self.version_number}"
