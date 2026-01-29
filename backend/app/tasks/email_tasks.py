"""
Email tasks for Celery.
"""
from datetime import datetime
from typing import Dict, Any
from loguru import logger

from app.tasks import celery_app
from app.core.email import email_service


@celery_app.task(name="send_email")
def send_email_task(to: str, subject: str, html_body: str, template_name: str = None, context: Dict[str, Any] = None):
    """
    Send an email using HTML or template.
    
    Args:
        to: Email recipient
        subject: Email subject
        html_body: HTML body (if not using template)
        template_name: Template file name (optional)
        context: Template context variables (optional)
    """
    logger.info(f"Sending email to {to}: {subject}")
    
    try:
        if template_name and context:
            # Enviar usando template
            success = email_service.send_template_email(
                to=to,
                subject=subject,
                template_name=template_name,
                context=context
            )
        else:
            # Enviar HTML directo
            success = email_service.send_email(
                to=to,
                subject=subject,
                html_body=html_body
            )
        
        if success:
            return {"status": "sent", "to": to, "subject": subject}
        else:
            return {"status": "failed", "to": to, "subject": subject}
            
    except Exception as e:
        logger.error(f"Error en tarea send_email: {e}")
        return {"status": "error", "to": to, "error": str(e)}


@celery_app.task(name="send_bulk_emails")
def send_bulk_emails_task(emails: list):
    """
    Send multiple emails.
    
    Args:
        emails: List of email dictionaries with to, subject, html_body or template_name+context
    """
    logger.info(f"Sending {len(emails)} bulk emails")
    results = []
    for email in emails:
        result = send_email_task.delay(**email)
        results.append(result.id)
    return {"status": "queued", "task_ids": results}


@celery_app.task(name="send_incapacidad_radicada_email")
def send_incapacidad_radicada_email_task(
    correo_solicitante: str,
    solicitante_nombre: str,
    numero_radicacion: str,
    incapacidad_data: Dict[str, Any]
):
    """
    Envía correo de confirmación de radicación de incapacidad.
    
    Args:
        correo_solicitante: Email del solicitante
        solicitante_nombre: Nombre completo del solicitante
        numero_radicacion: Número de radicación generado
        incapacidad_data: Diccionario con datos de la incapacidad
    """
    logger.info(f"[EMAIL] Enviando notificación de radicación {numero_radicacion} a {correo_solicitante}")
    
    try:
        # Preparar contexto para el template
        context = {
            'solicitante_nombre': solicitante_nombre,
            'numero_radicacion': numero_radicacion,
            'empleado_nombre': incapacidad_data.get('beneficiario_nombre', 'N/A'),
            'numero_documento': incapacidad_data.get('numero_documento', 'N/A'),
            'tipo_incapacidad': incapacidad_data.get('tipo', 'N/A'),
            'empresa': incapacidad_data.get('empresa', None),
            'fecha_inicio': incapacidad_data.get('fecha_inicio', 'N/A'),
            'fecha_fin': incapacidad_data.get('fecha_fin', 'N/A'),
            'dias_totales': incapacidad_data.get('dias_totales', 0),
            'diagnostico': incapacidad_data.get('diagnostico', None),
            'ips': incapacidad_data.get('ips', None),
            'medico': incapacidad_data.get('medico', None),
            'registro_medico': incapacidad_data.get('registro_medico', None),
            'eps': incapacidad_data.get('eps', None),
            'fecha_radicacion': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'url_consulta': f"{incapacidad_data.get('base_url', 'http://localhost:3000')}/consultar?numero={numero_radicacion}",
            'year': datetime.utcnow().year
        }
        
        # Enviar email
        success = email_service.send_template_email(
            to=correo_solicitante,
            subject=f"✓ Incapacidad Radicada Exitosamente - {numero_radicacion}",
            template_name='incapacidad_radicada.html',
            context=context
        )
        
        if success:
            logger.success(f"[EMAIL] Notificación enviada exitosamente a {correo_solicitante}")
            return {
                "status": "sent",
                "to": correo_solicitante,
                "numero_radicacion": numero_radicacion
            }
        else:
            logger.error(f"[EMAIL] Fallo al enviar notificación a {correo_solicitante}")
            return {
                "status": "failed",
                "to": correo_solicitante,
                "numero_radicacion": numero_radicacion
            }
            
    except Exception as e:
        logger.error(f"[EMAIL] Error al enviar notificación de radicación: {e}")
        return {
            "status": "error",
            "to": correo_solicitante,
            "error": str(e)
        }
