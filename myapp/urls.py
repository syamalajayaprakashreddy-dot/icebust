from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("campaigns/new/", views.campaign_create, name="campaign_create"),
    path("campaigns/<int:pk>/send/", views.campaign_send, name="campaign_send"),

    path("templates/", views.template_list, name="template_list"),
    path("templates/new/", views.template_create, name="template_create"),
    path("templates/<int:pk>/edit/", views.template_edit, name="template_edit"),
    path("templates/<int:pk>/delete/", views.template_delete, name="template_delete"),

    path("recipients/", views.recipient_list, name="recipient_list"),
    path("recipients/import/", views.recipient_import, name="recipient_import"),
    path("recipients/delete/<int:pk>/", views.recipient_delete, name="recipient_delete"),
    path("recipients/undo/<int:pk>/", views.recipient_undo, name="recipient_undo"),

    # ✅ TRACKING (UUID ONLY)
    path("track/open/<uuid:tracking_id>/", views.track_open, name="track_open"),
    path("track/click/<uuid:tracking_id>/", views.track_click, name="track_click"),

    # ✅ WEBHOOK
    path("webhooks/brevo/", views.brevo_webhook, name="brevo_webhook"),

    # ✅ UNSUBSCRIBE
    path("unsubscribe/<int:recipient_id>/", views.unsubscribe, name="unsubscribe"),

    # ✅ STATS
    path("api/live-stats/", views.live_stats, name="live_stats"),
    path("live-stats/", views.live_stats),

    # ✅ SMTP TEST
    path("smtp-test/", views.smtp_test),
]
