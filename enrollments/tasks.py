from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


# 🔥 GENERIC EMAIL TASK
@shared_task(bind=True, max_retries=3)
def send_email_task(self, subject, message, recipients):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipients,
            fail_silently=False,
        )
        return "Email sent successfully"

    except Exception as e:
        # Retry after 10 seconds if failed
        raise self.retry(exc=e, countdown=10)


# 🔥 ADMIN NOTIFICATION (ENROLLMENT)
def send_admin_enrollment_email_sync(name, email, course, phone):
    return send_mail(
        subject="New Enrollment Request",
        message=f"""
New student enrolled:

Name: {name}
Email: {email}
Course: {course}
Phone: {phone}
            """,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False,
    )


@shared_task(bind=True, max_retries=3)
def send_admin_enrollment_email(self, name, email, course, phone):
    try:
        send_admin_enrollment_email_sync(name, email, course, phone)
        return "Admin notified"

    except Exception as e:
        raise self.retry(exc=e, countdown=10)


# 🔥 PAYMENT SUCCESS EMAIL (ADMIN)
@shared_task(bind=True, max_retries=3)
def send_payment_success_email(self, name, email, course):
    try:
        send_mail(
            subject="Payment Successful 💰",
            message=f"""
Payment completed:

Name: {name}
Email: {email}
Course: {course}
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        return "Payment email sent"

    except Exception as e:
        raise self.retry(exc=e, countdown=10)


# 🔥 STUDENT APPROVAL EMAIL
def send_student_approval_email_sync(name, username, password, course, email):
    return send_mail(
        subject="Enrollment Approved 🎉",
        message=f"""
Hi {name},

Your enrollment is approved.

Login Details:
Username: {username}
Password: {password}

Important: You must change your password on first login.

Course: {course}
            """,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task(bind=True, max_retries=3)
def send_student_approval_email(self, name, username, password, course, email):
    try:
        send_student_approval_email_sync(name, username, password, course, email)
        return "Student notified"

    except Exception as e:
        raise self.retry(exc=e, countdown=10)


# 🔥 STUDENT REJECTION EMAIL
def send_student_rejection_email_sync(name, course, email):
    return send_mail(
        subject="Enrollment Rejected",
        message=f"""
Hi {name},

Your enrollment for {course} was rejected.

Please contact support.
            """,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task(bind=True, max_retries=3)
def send_student_rejection_email(self, name, course, email):
    try:
        send_student_rejection_email_sync(name, course, email)
        return "Rejection email sent"

    except Exception as e:
        raise self.retry(exc=e, countdown=10)