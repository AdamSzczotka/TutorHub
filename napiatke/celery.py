import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'napiatke.settings')

app = Celery('napiatke')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-lesson-reminders': {
        'task': 'apps.lessons.tasks.send_lesson_reminders',
        'schedule': crontab(hour=18, minute=0),
    },
}
