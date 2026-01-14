"""
Email tasks for Celery.
"""
from loguru import logger

from app.tasks import celery_app


@celery_app.task(name="send_email")
def send_email_task(to: str, subject: str, body: str):
    """
    Send an email (placeholder).
    
    Args:
        to: Email recipient
        subject: Email subject
        body: Email body
    """
    logger.info(f"Sending email to {to}: {subject}")
    # TODO: Implement email sending logic
    return {"status": "sent", "to": to, "subject": subject}


@celery_app.task(name="send_bulk_emails")
def send_bulk_emails_task(emails: list):
    """
    Send multiple emails.
    
    Args:
        emails: List of email dictionaries with to, subject, body
    """
    logger.info(f"Sending {len(emails)} bulk emails")
    results = []
    for email in emails:
        result = send_email_task.delay(**email)
        results.append(result.id)
    return {"status": "queued", "task_ids": results}
