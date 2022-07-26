import os

from celery import Celery

broker_url = "amqp://localhost"
redis_url = "redis://localhost"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "overschool.settings")

app = Celery("overschool", broker=broker_url, backend=redis_url)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
