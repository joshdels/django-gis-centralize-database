from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def user_upload_path(instance, filename):
    """Creates a designated folder per user of project file"""
    return f"uploads/user_{instance.user.id}/{filename}"


class Project(models.Model):
    """Represents a user project with filem, name, description, and owner"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploads",
        help_text="The user who created this project",
    )
    file = models.FileField(upload_to=user_upload_path)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.CharField(max_length=255, null=True, blank=True)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    # ----- Domain Constraints ------
    MAX_FILES = 3
    MAX_STORAGE_MB = 10
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __str__(self):
        return self.name

    # ---- DOMAIN RULES ----
    def clean(self):
        """Validate all constraints before saving"""

        # Max rows per user
        user_projects = Project.objects.filter(user=self.user, archived=False)
        if self.pk:
            user_projects = user_projects.exclude(pk=self.pk)
        if user_projects.count() >= self.MAX_FILES:
            raise ValidationError(
                {"file": f"You can only have {self.MAX_FILES} project per user."}
            )

        # Total file size per user
        total_used_bytes = sum(p.file.size for p in user_projects if p.file)
        current_file_size = self.file.size if self.file else 0
        total_used_mb = (total_used_bytes + current_file_size) / (1024 * 1024)
        if total_used_mb > self.MAX_STORAGE_MB:
            raise ValidationError(
                {"file": f"Total storage exceeded ({self.MAX_STORAGE_MB} MB max)."}
            )

        # Max single file size
        if self.file and self.file.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                {
                    "file": f"File exceeds the {self.MAX_FILE_SIZE // (1024*1024)} MB limit"
                }
            )

    def save(self, *args, **kwargs):
        """Enforce domain rules to automatically save"""
        if not self.user_id:
            raise ValidationError(
                {"user": "User must be set before saving this Project."}
            )

        if not self.owner:
            self.owner = self.user.username

        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        storage = self.file.storage if self.file else None
        name = self.file.name if self.file else None
        super().delete(*args, **kwargs)
        if storage and name:
            storage.delete(name)

    # def can_user_download(self, user):
    #     return user.is_staff or self.user_id == user.id
