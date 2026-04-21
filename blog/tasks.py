from celery import shared_task
from django.utils import timezone
from .models import Blog

@shared_task(name="blog.tasks.update_scheduled_blogs")
def update_scheduled_blogs():
    """
    Periodic task to update blogs that have reached their scheduled publish time.
    """
    now = timezone.now()
    updated_count = Blog.objects.filter(
        status='scheduled',
        publish_at__lte=now,
        is_deleted=False
    ).update(status='published')
    
    return f"Updated {updated_count} blogs to published status."
