"""
Celery application configuration.
"""
from celery import Celery

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "incapacidades",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Bogota",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])

# Import tasks
from app.tasks import (  # noqa
    email_tasks,
    notification_tasks,
    report_tasks,
    incapacidad_tasks  # ← NUEVO
)


__all__ = ["celery_app"]
