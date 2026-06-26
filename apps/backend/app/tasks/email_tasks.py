"""
Email tasks for Celery.
"""
from datetime import datetime
from html import escape
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
    # No esta imprimiendo ni el nombre del empleado
    logger.debug(f"[EMAIL] Datos incapacidad: {incapacidad_data}")
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
            'url_consulta': f"{incapacidad_data.get('base_url', 'http://localhost:5173')}/consultar?numero={numero_radicacion}",
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


@celery_app.task(name="send_devolucion_pre_incapacidad_email")
def send_devolucion_pre_incapacidad_email_task(
    correo_solicitante: str,
    solicitante_nombre: str,
    numero_radicacion: str,
    empleado_nombre: str,
    empleado_documento: str,
    empresa_nombre: str,
    fecha_inicio: str,
    dias_totales: int,
    motivo: str,
    usuario_nombre: str,
):
    """Envía carta de devolución formal al solicitante."""
    logger.info(f"[EMAIL] Enviando devolución radicación {numero_radicacion} a {correo_solicitante}")
    try:
        context = {
            "solicitante_nombre": solicitante_nombre,
            "numero_radicacion": numero_radicacion,
            "empleado_nombre": empleado_nombre,
            "empleado_documento": empleado_documento,
            "empresa_nombre": empresa_nombre,
            "fecha_inicio": fecha_inicio,
            "dias_totales": dias_totales,
            "motivo": motivo,
            "usuario_nombre": usuario_nombre,
            "fecha_devolucion": datetime.utcnow().strftime("%d de %B de %Y"),
            "year": datetime.utcnow().year,
        }
        success = email_service.send_template_email(
            to=correo_solicitante,
            subject=f"Devolución Radicación N° {numero_radicacion} — Información Requerida",
            template_name="devolucion_pre_incapacidad.html",
            context=context,
        )
        return {"status": "sent" if success else "failed", "to": correo_solicitante}
    except Exception as e:
        logger.error(f"[EMAIL] Error al enviar devolución: {e}")
        return {"status": "error", "error": str(e)}


def _build_bulk_email_html(empresa_nombre: str, fecha: str, items: list[dict]) -> str:
    """Build a branded HTML email body for bulk filing confirmation.

    items: list of {numero, numero_documento, dias_totales}
    """
    rows_html = ""
    for item in items:
        rows_html += (
            f'<tr style="border-bottom:1px solid #CEDFDC;">'
            f'<td style="padding:10px 14px;color:#004953;">{escape(str(item["numero_documento"]))}</td>'
            f'<td style="padding:10px 14px;font-family:monospace;color:#004953;">{escape(str(item["numero"]))}</td>'
            f'<td style="padding:10px 14px;text-align:right;color:#004953;">{item["dias_totales"]}</td>'
            f'</tr>'
        )
    year = datetime.utcnow().year
    count = len(items)
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F0FAF8;font-family:Roboto,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F0FAF8;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,73,83,0.08);border-top:4px solid #009966;">
        <tr>
          <td style="background:#004953;padding:24px 32px;">
            <h1 style="margin:0;font-size:20px;color:#FFFFFF;font-weight:700;">Seguros Alfa</h1>
            <p style="margin:6px 0 0;font-size:14px;color:rgba(255,255,255,0.75);">Confirmación de Radicación de Incapacidades</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <p style="margin:0 0 8px;font-size:15px;color:#004953;">Empresa: <strong>{escape(empresa_nombre)}</strong></p>
            <p style="margin:0 0 24px;font-size:14px;color:#52706F;">
              Se radicaron exitosamente <strong>{count}</strong> incapacidad(es) el {escape(fecha)}.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border:1px solid #CEDFDC;">
              <thead>
                <tr style="background:#EBF7F5;">
                  <th style="padding:10px 14px;text-align:left;font-size:12px;color:#52706F;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Nº Documento</th>
                  <th style="padding:10px 14px;text-align:left;font-size:12px;color:#52706F;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Número de Radicado</th>
                  <th style="padding:10px 14px;text-align:right;font-size:12px;color:#52706F;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Días</th>
                </tr>
              </thead>
              <tbody>
                {rows_html}
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background:#F0FAF8;padding:20px 32px;border-top:1px solid #CEDFDC;">
            <p style="margin:0;font-size:12px;color:#52706F;text-align:center;">
              © {year} Seguros Alfa — Este correo es generado automáticamente.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


@celery_app.task(name="send_resumen_radicacion_masiva")
def send_resumen_radicacion_masiva_task(
    to: str,
    empresa_nombre: str,
    fecha: str,
    items: list[dict],
) -> dict:
    """Send a formatted bulk filing summary email.

    items: list of {numero, numero_documento, dias_totales}
    """
    logger.info(f"[EMAIL] Enviando resumen masivo ({len(items)} items) a {to}")
    try:
        html_body = _build_bulk_email_html(empresa_nombre, fecha, items)
        success = email_service.send_email(
            to=to,
            subject="Confirmación de radicación masiva de incapacidades",
            html_body=html_body,
        )
        return {"status": "sent" if success else "failed", "to": to}
    except Exception as exc:
        logger.error(f"[EMAIL] Error al enviar resumen masivo: {exc}")
        return {"status": "error", "to": to, "error": str(exc)}
