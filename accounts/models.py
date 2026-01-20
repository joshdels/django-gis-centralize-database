from django.db import models
from django.contrib.auth.models import User


def user_upload_path(instance, filename):
    return f"uploads/user_{instance.user.id}/{filename}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # Custom Profile
    image = models.ImageField(upload_to=user_upload_path, null=True, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username}"
