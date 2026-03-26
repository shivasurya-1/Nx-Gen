import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

# Read config from settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto discover tasks from all apps
app.autodiscover_tasks()