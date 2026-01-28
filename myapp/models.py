from django.db import models

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

    def __str__(self):
        return self.email

    
class Campaign(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("sent", "Sent"),
    ]

    name = models.CharField(max_length=100, unique=True)  # 👈 THIS LINE
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

    def __str__(self):
        return self.name




class CampaignLog(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="logs")
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE,null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    opened = models.BooleanField(default=False)
    clicked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("campaign", "recipient")




