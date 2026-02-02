from django import forms
from .models import Campaign, Recipient, EmailTemplate


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ["name", "subject", "body_html"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body_html": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 12
            }),
        }


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        exclude = ["status", "created_at"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "template": forms.Select(attrs={"class": "form-control"}),
            "recipients": forms.SelectMultiple(attrs={
                "class": "form-control select2",
                "data-placeholder": "Click to select recipients"
            }),
            "redirect_url": forms.URLInput(attrs={
                "class": "form-control redirect-input",
                "placeholder": "https://example.com"
            }),
        }

