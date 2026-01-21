from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def user_upload_path(instance, filename):
    """Uploads to a folder per user of the parent project."""
    try:
        user_id = instance.user.id
    except AttributeError:
        user_id = instance.project.user.id
    return f"uploads/user_{user_id}/{filename}"


class Project(models.Model):
    """Represents a user project with filem, name, description, and owner"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploads",
        help_text="The user who created this project",
    )
    file = models.FileField(upload_to=user_upload_path, blank=True, null=True)
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
    MAX_STORAGE_MB = 50
    MAX_FILE_SIZE = 100 * 1024 * 1024

    def __str__(self):
        return self.name

    # ---- DOMAIN RULES ----
    def clean(self):
        """Validate all constraints before saving"""

        # Max rows per user
        user_projects = Project.objects.filter(user=self.user, archived=False)
        if self.pk:
            user_projects = user_projects.exclude(pk=self.pk)

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
            
    def create_new_version(self, new_file):
        """This appends to the ProjectVersion Model Everytime I update the project"""
        last_version = self.version.first()
        new_version_number = (last_version.version_number if last_version else 0) + 1

        new_version = ProjectVersion.objects.create(
            project=self,
            file=new_file,
            version_number=new_version_number,
        )

        self.file = new_version.file
        self.updated_at = timezone.now()
        self.save(update_fields=["file", "updated_at"])

        return new_version
        


class ProjectVersion(models.Model):
    project = models.ForeignKey(
        Project, related_name="versions", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to=user_upload_path)
    version_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        unique_together = ("project", "version_number")

    def __str__(self):
        return f"{self.project.name} v{self.version_number}"
