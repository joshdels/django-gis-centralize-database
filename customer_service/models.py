from django.conf import settings
from django.db import models


class CustomerMessage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_messages",
    )

    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_messages",
    )

    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()

    CATEGORY_CHOICES = [
        ("FEEDBACK", "Feedback"),
        ("TESTIMONIAL", "Testimonial"),
        ("BUG", "Bug Report"),
        ("FEATURE", "Feature Request"),
        ("SUPPORT", "Support"),
    ]
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="FEEDBACK",
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
    )

    SENDER_CHOICES = [
        ("USER", "User"),
        ("STAFF", "Staff"),
    ]
    sender = models.CharField(
        max_length=10,
        choices=SENDER_CHOICES,
        default="USER",
    )

    # Status of the ticket
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("REPLIED", "Replied"),
        ("ONGOING", "On Going"),
        ("CLOSED", "Closed"),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="NEW",
    )

    is_public = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer Message"
        verbose_name_plural = "Customer Messages"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.category} | {self.subject or self.message[:30]}"
