from django import forms
from .models import EmailTemplate
from .models import Campaign

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ["name", "subject", "body_html"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body_html": forms.Textarea(attrs={"class": "form-control", "rows": 12}),
        }


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ["name", "template", "scheduled_time", "status"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "template": forms.Select(attrs={"class": "form-select"}),
            "scheduled_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
