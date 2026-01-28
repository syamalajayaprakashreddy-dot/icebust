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

    path("recipients/import/", views.recipient_import, name="recipient_import"),
    path("campaigns/<int:pk>/send/", views.campaign_send, name="campaign_send"),
    path("track/open/<int:log_id>/", views.track_open, name="track_open"),
    
]





