from django.contrib import admin
from .models import EmailTemplate, Campaign, CampaignLog, Recipient

admin.site.register(EmailTemplate)
admin.site.register(Campaign)
admin.site.register(CampaignLog)
admin.site.register(Recipient)
