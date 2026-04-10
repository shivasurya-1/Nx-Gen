from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


def send_instructor_credentials_email_sync(email, name, username, password):
    subject = "Your Instructor Account is Created 🎉"

    message = f"""
Hi {name},

Your instructor account has been successfully created.

Login Details:
Username: {username}
Password: {password}

⚠️ Please change your password after first login.

You can now access the platform.

Regards,  
Team Nxgen
"""

    return send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )


@shared_task
def send_instructor_credentials_email_task(email, name, username, password):
    return send_instructor_credentials_email_sync(email, name, username, password)