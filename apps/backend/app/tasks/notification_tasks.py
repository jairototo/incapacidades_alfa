"""
Notification tasks for Celery.
"""
from loguru import logger

from apps.backend.app.tasks import celery_app


@celery_app.task(name="send_notification")
def send_notification_task(user_id: str, message: str, notification_type: str = "info"):
    """
    Send a notification to a user (placeholder).
    
    Args:
        user_id: User ID
        message: Notification message
        notification_type: Type of notification
    """
    logger.info(f"Sending {notification_type} notification to user {user_id}: {message}")
    # TODO: Implement notification logic
    return {"status": "sent", "user_id": user_id, "type": notification_type}


@celery_app.task(name="process_incapacidad_notification")
def process_incapacidad_notification_task(incapacidad_id: str, event: str):
    """
    Process incapacidad state change notification.
    
    Args:
        incapacidad_id: Incapacidad ID
        event: Event type (radicada, auditada, aprobada, etc.)
    """
    logger.info(f"Processing notification for incapacidad {incapacidad_id}: {event}")
    # TODO: Implement incapacidad notification logic
    return {"status": "processed", "incapacidad_id": incapacidad_id, "event": event}
