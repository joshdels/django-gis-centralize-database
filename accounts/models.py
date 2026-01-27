from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from gis_database.models import File


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()


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
        default=10, help_text="Maximum allowed storage for this user in MB"
    )

    def __str__(self):
        return f"{self.user.username}"

    def used_storage_bytes(self):
        return sum(f.file.size for f in File.objects.filter(owner=self.user) if f.file)

    def remaining_storage_bytes(self):
        return max(
            (self.storage_limit_mb * 1024 * 1024) - self.used_storage_bytes(),
            0,
        )

    def can_store(self, file_size):
        return file_size <= self.remaining_storage_bytes()
