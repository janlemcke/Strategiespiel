# django_celery/celery.py


import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.beat_schedule = {
            'update-resources-every-minute': {
                'task': 'building.tasks.update_resources',
                'schedule': crontab(minute='*'),
            },
        }

app.autodiscover_tasks()