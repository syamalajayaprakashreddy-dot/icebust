from django.core.mail import send_mail
from django.conf import settings

def send_transactional_email(subject, message, to_email):
    send_mail(
        subject=subject,
        message=message,
        from_email="Icebust <support@icebust.shop>",
        recipient_list=[to_email],
        fail_silently=False,
        reply_to=["support@icebust.shop"],
    )
