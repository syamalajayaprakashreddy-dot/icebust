import uuid

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User



class EmailTemplate(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body_html = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Recipient(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    is_subscribed = models.BooleanField(default=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.email

    
class Campaign(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("sent", "Sent"),
    ]

    name = models.CharField(max_length=100, unique=True)
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    recipients = models.ManyToManyField(Recipient, blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    redirect_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name




class CampaignLog(models.Model):

    tracking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    campaign = models.ForeignKey(
        Campaign,
        related_name="logs",
        on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        Recipient,
        on_delete=models.CASCADE
    )

    sent_at = models.DateTimeField(default=timezone.now)
    opened = models.BooleanField(default=False)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("campaign", "recipient")

    def __str__(self):
        return f"{self.campaign} → {self.recipient}"






from django.contrib.auth.models import User

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("send", "Send"),
        ("import", "Import"),
        ("undo", "Undo"),
    ]

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} | {self.object_type} | {self.created_at}"

    




