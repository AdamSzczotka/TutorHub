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
    'check-attendance-alerts': {
        'task': 'apps.attendance.tasks.check_attendance_alerts',
        'schedule': crontab(hour=8, minute=0),  # Every day at 8:00 AM
    },
    'generate-monthly-reports': {
        'task': 'apps.attendance.tasks.generate_monthly_reports_task',
        'schedule': crontab(day_of_month=1, hour=6, minute=0),  # First day of month at 6:00 AM
        'args': (None,),  # Will use previous month
    },
    'send-weekly-summaries': {
        'task': 'apps.notifications.tasks.send_weekly_summaries_task',
        'schedule': crontab(day_of_week=0, hour=18, minute=0),  # Sunday at 6 PM
    },
}
