import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'napiatke.settings.production')

app = Celery('napiatke')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# The beat schedule lives in settings (CELERY_BEAT_SCHEDULE). Assigning
# app.conf.beat_schedule here used to silently replace it, so monthly billing
# and overdue checks never ran.
