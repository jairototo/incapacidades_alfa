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

# Celery Beat periodic schedule
from celery.schedules import crontab  # noqa: E402

celery_app.conf.beat_schedule = {
    # Procesar incapacidades RADICADAS que no hayan pasado a auditoría
    "procesar-radicadas-pendientes": {
        "task": "procesar_incapacidades_radicadas_pendientes",
        "schedule": crontab(minute=0, hour="*/1"),  # cada hora
    },
    # Alerta diaria: incapacidades en PENDIENTE > PENDIENTE_ALERT_DAYS días
    "check-pendientes-alert": {
        "task": "tasks.check_pendientes_alert",
        "schedule": crontab(hour=8, minute=0),  # diario a las 8am Bogotá
    },
}

# Import tasks (ensure they are registered)
from app.tasks import (  # noqa
    report_tasks,
    incapacidad_tasks,
)


__all__ = ["celery_app"]
