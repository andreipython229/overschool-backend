import os

from celery import Celery


redis_url = "redis://localhost"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "overschool.settings")

app = Celery("overschool", broker=redis_url, backend=redis_url)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
