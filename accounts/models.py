from django.db import models
from django.contrib.auth.models import User


def user_upload_path(instance, filename):
    return f"uploads/user_{instance.user.id}/{filename}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Custom Profile
    image = models.ImageField(upload_to=user_upload_path, null=True, blank=True)
    institution = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)

    storage_limit_mb = models.PositiveIntegerField(
        default=50, help_text="Maximum allowed storage for this user in MB"
    )

    used_storage_mb = models.FloatField(
        default=0.0, help_text="Storage used by the user in MB"
    )

    def __str__(self):
        return f"{self.user.username}"

    @property
    def remaining_storage_mb(self):
        return max(self.storage_limit_mb - self.used_storage_mb, 0)

    def has_space_for(self, size_mb):
        return self.remaining_storage_mb >= size_mb
