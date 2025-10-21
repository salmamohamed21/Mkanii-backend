import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mkani.settings')
app = Celery('mkani')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# جدولة المهام (تعمل في اليوم الأول من كل شهر الساعة 3 صباحًا)
app.conf.beat_schedule = {
    'generate-monthly-invoices': {
        'task': 'mkani.apps.core.tasks.generate_monthly_invoices',
        'schedule': crontab(hour=3, minute=0, day_of_month='1'),
    },
}
