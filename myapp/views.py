print("LOADED MYAPP VIEWS")
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail

from .models import Campaign, CampaignLog, EmailTemplate
from .forms import CampaignForm, EmailTemplateForm


# =======================
# DASHBOARD
# =======================
def dashboard(request):
    total_campaigns = Campaign.objects.count()

    emails_sent = CampaignLog.objects.filter(
        campaign__status="sent"
    ).count()

    opened = CampaignLog.objects.filter(
        opened=True,
        campaign__status="sent"
    ).count()

    clicked = CampaignLog.objects.filter(
        clicked=True,
        campaign__status="sent"
    ).count()

    open_rate = round((opened / emails_sent) * 100, 1) if emails_sent else 0
    click_rate = round((clicked / emails_sent) * 100, 1) if emails_sent else 0

    recent_campaigns = (
        Campaign.objects
        .annotate(sent_count=Count("logs"))
        .order_by("-created_at")[:10]
    )

    context = {
        "total_campaigns": total_campaigns,
        "emails_sent": emails_sent,
        "open_rate": open_rate,
        "click_rate": click_rate,
        "recent_campaigns": recent_campaigns,
    }

    return render(request, "myapp/dashboard.html", context)


# =======================
# CREATE CAMPAIGN
# =======================
def campaign_create(request):
    if request.method == "POST":
        form = CampaignForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = CampaignForm()

    return render(request, "myapp/campaign_create.html", {"form": form})


# =======================
# SEND CAMPAIGN (POST ONLY)
# =======================
def campaign_send(request, pk):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("dashboard")

    campaign = get_object_or_404(Campaign, pk=pk)

    if campaign.status == "sent":
        messages.info(request, "Campaign already sent.")
        return redirect("dashboard")

    if not campaign.template:
        messages.error(request, "Campaign has no template.")
        return redirect("dashboard")

    recipients = campaign.recipients.filter(is_subscribed=True)

    if not recipients.exists():
        messages.error(request, "No recipients assigned.")
        return redirect("dashboard")

    sent_count = 0  # ✅ define ONCE

    for r in recipients:
        log, created = CampaignLog.objects.get_or_create(
            campaign=campaign,
            recipient=r,
            defaults={"sent_at": timezone.now()},
        )

        if created:
            tracking_url = f"{settings.SITE_URL}{reverse('track_open', args=[log.id])}"

            html_body = campaign.template.body_html + f"""
                <img src="{tracking_url}" width="1" height="1" style="display:none;" />
            """

            

            send_mail(
    subject=campaign.template.subject,
    message="",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[r.email],
    html_message=html_body,
    fail_silently=False,
)


            sent_count += 1  # ✅ MUST be inside if created

    campaign.status = "sent"
    campaign.save()

    messages.success(request, f"Sent to {sent_count} recipients.")
    return redirect("dashboard")


# =======================
# EMAIL TEMPLATES
# =======================

def template_list(request):
    templates = EmailTemplate.objects.order_by("-created_at")
    return render(request, "myapp/template_list.html", {"templates": templates})


def template_create(request):
    if request.method == "POST":
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("template_list")
    else:
        form = EmailTemplateForm()

    return render(request, "myapp/template_form.html", {
        "form": form,
        "title": "Create Template"
    })


def template_edit(request, pk):
    template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == "POST":
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            return redirect("template_list")
    else:
        form = EmailTemplateForm(instance=template)

    return render(request, "myapp/template_form.html", {
        "form": form,
        "title": "Edit Template"
    })


def template_delete(request, pk):
    template = get_object_or_404(EmailTemplate, pk=pk)
    if request.method == "POST":
        template.delete()
        return redirect("template_list")

    return render(request, "myapp/template_delete.html", {"template": template})

def recipient_import(request):
    return render(request, "myapp/recipient_import.html")

from django.http import HttpResponse
from django.views.decorators.http import require_GET
import base64

@require_GET
def track_open(request, log_id):
    log = get_object_or_404(CampaignLog, id=log_id)

    if not log.opened:
        log.opened = True
        log.save(update_fields=["opened"])

    # 1x1 transparent tracking pixel (GIF)
    pixel = base64.b64decode(
        "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
    )

    return HttpResponse(pixel, content_type="image/gif")
