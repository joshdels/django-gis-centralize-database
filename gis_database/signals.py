from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps


@receiver(post_save, sender="gis_database.Project")
def add_owner_as_admin(sender, instance, created, **kwargs):
    if created and instance.owner:
        ProjectMembership = apps.get_model("gis_database", "ProjectMembership")

        ProjectMembership.objects.create(
            user=instance.owner,
            project=instance,
            role="admin",
            invited_by=instance.owner
        )
