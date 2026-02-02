print("LOADED MYAPP VIEWS")

from datetime import timedelta
import csv
import json
import base64

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.timezone import now
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse
from django.conf import settings
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import io


from .models import Campaign, CampaignLog, EmailTemplate, Recipient
from .forms import CampaignForm, EmailTemplateForm


from .models import AuditLog

def log_action(request, action, object_type, object_id=None, message=""):
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        object_type=object_type,
        object_id=object_id,
        message=message,
    )


# =======================
# HOME / DASHBOARD
# =======================

def home(request):
    return render(request, "myapp/home.html")


from django.db.models import Count

def dashboard(request):
    total_campaigns = Campaign.objects.count()

    emails_sent = CampaignLog.objects.count()
    opened = CampaignLog.objects.filter(opened=True).count()
    clicked = CampaignLog.objects.filter(clicked=True).count()

    open_rate = round((opened / emails_sent) * 100, 1) if emails_sent else 0
    click_rate = round((clicked / emails_sent) * 100, 1) if emails_sent else 0

    recent_campaigns = Campaign.objects.annotate(
        sent_count=Count("logs")
    ).order_by("-created_at")[:10]

    context = {
        "total_campaigns": total_campaigns,
        "emails_sent": emails_sent,
        "open_rate": open_rate,
        "click_rate": click_rate,
        "recent_campaigns": recent_campaigns,
    }

    return render(request, "myapp/dashboard.html", context)



# =======================
# CREATE CAMPAIGN (ONLY ONE)
# =======================

def campaign_create(request):
    if request.method == "POST":
        form = CampaignForm(request.POST)

        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.status = "draft"
            campaign.save()
            form.save_m2m()

            log_action(
    request,
    action="create",
    object_type="Campaign",
    object_id=campaign.id,
    message=f"Campaign '{campaign.name}' created"
)


            messages.success(request, "Campaign created successfully.")
            return redirect("dashboard")   # ✅ SAME BEHAVIOR

    else:
        form = CampaignForm()

    return render(request, "myapp/campaign_create.html", {"form": form})



# =======================
# SEND CAMPAIGN
# =======================

from django.utils import timezone

def campaign_send(request, pk):
    if request.method != "POST":
        return redirect("dashboard")

    campaign = get_object_or_404(Campaign, pk=pk)

    if campaign.status == "sent":
        return redirect("dashboard")

    recipients = campaign.recipients.filter(is_subscribed=True)

    sent_count = 0

    for r in recipients:
        log, created = CampaignLog.objects.get_or_create(
    campaign=campaign,
    recipient=r,
    defaults={"sent_at": timezone.now()}
    )

# optional: skip re-sending if already sent
        if not created:
            continue


        open_pixel_url = request.build_absolute_uri(
        reverse("track_open", args=[log.tracking_id])
        )

        click_url = f"{settings.SITE_URL}{reverse('track_click', args=[log.tracking_id])}"





        html_body = campaign.template.body_html
        html_body = html_body.replace("{{CLICK_URL}}", click_url)

# tracking pixel TEMPORARILY disabled
# html_body += f"""
# <img src="{open_pixel_url}" width="1" height="1" style="display:none;" />
# """

        send_mail(
    subject=campaign.template.subject,
    message="This email contains HTML content. Please view in an email client.",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[r.email],
    html_message=html_body,
    fail_silently=False,
)



        sent_count += 1

    campaign.status = "sent"
    campaign.save(update_fields=["status"])

    log_action(
    request,
    action="send",
    object_type="Campaign",
    object_id=campaign.id,
    message=f"Campaign '{campaign.name}' sent to {sent_count} recipients"
)


    return redirect("dashboard")



# =======================
# EMAIL TEMPLATES
# =======================

def template_list(request):
    return render(request, "myapp/template_list.html", {
        "templates": EmailTemplate.objects.order_by("-created_at")
    })


def template_create(request):
    form = EmailTemplateForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(
    request,
    action="create",
    object_type="EmailTemplate",
    message="Email template created"
)

        messages.success(request, "Email template created successfully.")
        return redirect("dashboard")   # ✅ SAME

    return render(request, "myapp/template_form.html", {"form": form})



def template_edit(request, pk):
    template = get_object_or_404(EmailTemplate, pk=pk)
    form = EmailTemplateForm(request.POST or None, instance=template)

    if request.method == "POST" and form.is_valid():
        form.save()
        log_action(
    request,
    action="update",
    object_type="EmailTemplate",
    object_id=template.id,
    message=f"Email template '{template.name}' updated"
)

        messages.success(request, "Email template updated successfully.")
        return redirect("dashboard")   # ✅ SAME

    return render(request, "myapp/template_form.html", {
        "form": form,
        "template": template
    })




from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(is_admin)
def template_delete(request, pk):
    template = get_object_or_404(EmailTemplate, pk=pk)

    if request.method == "POST":
        template.delete()
        messages.success(request, "Email template deleted successfully.")
        return redirect("template_list")

    return redirect("template_list")



# =======================
# RECIPIENTS
# =======================

def recipient_list(request):
    recipients = Recipient.objects.filter(is_deleted=False).order_by("-id")
    return render(request, "myapp/recipient_list.html", {
        "recipients": recipients
    })


from django.views.decorators.http import require_POST


from django.contrib.auth.decorators import user_passes_test

@require_POST
@user_passes_test(is_admin)
def recipient_delete(request, pk):

    recipient = get_object_or_404(Recipient, pk=pk, is_deleted=False)

    recipient.is_deleted = True
    recipient.deleted_at = timezone.now()
    recipient.save(update_fields=["is_deleted", "deleted_at"])
    log_action(
    request,
    action="delete",
    object_type="Recipient",
    object_id=pk,
    message="Recipient soft-deleted"
)


    messages.warning(
        request,
        f"Recipient deleted. "
        f"<a href='{reverse('recipient_undo', args=[pk])}' "
        f"class='text-white text-decoration-underline'>Undo</a>"
    )

    return redirect("dashboard")


def recipient_undo(request, pk):
    recipient = get_object_or_404(Recipient, pk=pk)

    if recipient.is_deleted:
        recipient.is_deleted = False
        recipient.deleted_at = None
        recipient.save(update_fields=["is_deleted", "deleted_at"])
        log_action(
    request,
    action="undo",
    object_type="Recipient",
    object_id=pk,
    message="Recipient restored via undo"
)

        messages.success(request, "Recipient restored successfully.")

    return redirect("dashboard")



"""def recipient_import(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file or not file.name.endswith(".csv"):
            messages.error(request, "Upload a valid CSV.")
            return redirect("recipient_import")

        reader = csv.DictReader(file.read().decode("utf-8").splitlines())
        for row in reader:
            if row.get("email"):
                Recipient.objects.get_or_create(email=row["email"])

        messages.success(request, "Recipients imported.")
        return redirect("recipient_import")

    return render(request, "myapp/recipient_import.html")"""

"""def recipient_import(request):
    if request.method == "POST":
        csv_file = request.FILES.get("file")

        if not csv_file:
            messages.error(request, "No file received.")
            return redirect("dashboard")

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect("dashboard")

        file_data = io.TextIOWrapper(csv_file.file, encoding="utf-8-sig")
        reader = csv.DictReader(file_data)

        created = 0
        for row in reader:
            email = row.get("email")
            if not email:
                continue

            email = email.strip().lower()
            _, was_created = Recipient.objects.get_or_create(email=email)

            if was_created:
                created += 1

        messages.success(
            request,
            f"{created} new recipients imported successfully."
        )
        return redirect("dashboard")   # ✅ SAME
    log_action(
    request,
    action="import",
    object_type="Recipient",
    message=f"{created} recipients imported"
)

    return redirect("dashboard")"""

def recipient_import(request):
    if request.method == "POST":
        csv_file = request.FILES.get("file")

        if not csv_file:
            messages.error(request, "No file received.")
            return redirect("dashboard")

        if not csv_file.name.endswith(".csv"):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect("dashboard")

        file_data = io.TextIOWrapper(csv_file.file, encoding="utf-8-sig")
        reader = csv.DictReader(file_data)

        created = 0
        for row in reader:
            email = row.get("email")
            if not email:
                continue

            email = email.strip().lower()
            _, was_created = Recipient.objects.get_or_create(email=email)

            if was_created:
                created += 1

        log_action(
            request,
            action="import",
            object_type="Recipient",
            message=f"{created} recipients imported"
        )

        messages.success(
            request,
            f"{created} new recipients imported successfully."
        )

        return redirect("dashboard")

    # 👇 GET request → show upload page
    return render(request, "myapp/recipient_import.html")




# =======================
# TRACKING
# =======================

@require_GET
def track_open(request, tracking_id):
    log = get_object_or_404(CampaignLog, tracking_id=tracking_id)

    if not log.opened:
        log.opened = True
        log.save(update_fields=["opened"])

    return HttpResponse(
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
        b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
        content_type="image/gif"
    )



def track_click(request, tracking_id):
    log = get_object_or_404(CampaignLog, tracking_id=tracking_id)

    if not log.clicked:
        log.clicked = True
        log.clicked_at = timezone.now()
        log.save(update_fields=["clicked", "clicked_at"])

    url = log.campaign.redirect_url or "https://example.com"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return redirect(url)



# =======================
# LIVE STATS
# =======================

def live_stats(request):
    labels, opens, clicks = [], [], []

    for i in range(6, -1, -1):
        day = now().date() - timedelta(days=i)
        labels.append(day.strftime("%a"))
        opens.append(CampaignLog.objects.filter(opened=True, sent_at__date=day).count())
        clicks.append(CampaignLog.objects.filter(clicked=True, sent_at__date=day).count())

    return JsonResponse({
        "labels": labels,
        "opens": opens,
        "clicks": clicks,
    })


# =======================
# UNSUBSCRIBE
# =======================

def unsubscribe(request, recipient_id):
    r = get_object_or_404(Recipient, id=recipient_id)
    r.is_subscribed = False
    r.unsubscribed_at = timezone.now()
    r.save(update_fields=["is_subscribed", "unsubscribed_at"])
    return HttpResponse("You have been unsubscribed.")


# =======================
# SMTP TEST
# =======================

def smtp_test(request):
    send_mail(
        "SMTP TEST",
        "SMTP works.",
        settings.DEFAULT_FROM_EMAIL,
        ["test@example.com"],
        fail_silently=False,
    )
    return HttpResponse("SMTP test sent.")


# myapp/views.py (TOP IMPORTS)
import hmac
import hashlib
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def brevo_webhook(request):
    if request.method != "POST":
        return JsonResponse({"status": "invalid method"}, status=405)

    signature = request.headers.get("X-Brevo-Signature")
    if not signature:
        return JsonResponse({"status": "missing signature"}, status=401)

    computed = hmac.new(
        settings.BREVO_WEBHOOK_SECRET.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, computed):
        return JsonResponse({"status": "invalid signature"}, status=401)

    payload = json.loads(request.body.decode("utf-8"))

    event = payload.get("event")
    if not event:
        return JsonResponse({"status": "missing event"}, status=400)

    import uuid
    try:
        tracking_id = uuid.UUID(payload.get("tracking_id"))
    except Exception:
        return JsonResponse({"status": "invalid tracking_id"}, status=400)

    try:
        log = CampaignLog.objects.get(tracking_id=tracking_id)
    except CampaignLog.DoesNotExist:
        return JsonResponse({"status": "unknown tracking_id"}, status=404)

    if event == "opened":
        if log.opened:
            return JsonResponse({"status": "already opened"})
        log.opened = True
        log.save(update_fields=["opened"])

    if event == "click":
        if log.clicked:
            return JsonResponse({"status": "already clicked"})
        log.clicked = True
        log.clicked_at = timezone.now()
        log.save(update_fields=["clicked", "clicked_at"])

    return JsonResponse({"status": "ok"})




from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import CampaignLog

def email_open(request, log_id):
    log = get_object_or_404(CampaignLog, id=log_id)

    if not log.opened:
        log.opened = True
        log.save(update_fields=["opened"])

    # 1x1 transparent GIF pixel
    return HttpResponse(
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
        b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
        content_type="image/gif"
    )
