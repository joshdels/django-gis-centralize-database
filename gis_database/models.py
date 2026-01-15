from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os


def user_upload_path(instance, filename):
    """Creates a designated folder per user of project file"""
    return f"uploads/user_{instance.user.id}/{filename}"


class Project(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploads",
    )
    file = models.FileField(upload_to=user_upload_path)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


@receiver(post_delete, sender=Project)
def delete_file_on_instance_delete(sender, instance, **kwargs):
    """Delete file/s from storage when Project instance is deleted"""
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
