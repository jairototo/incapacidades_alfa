"""
Utilidades para envío de correos electrónicos.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, Dict, Any
from jinja2 import Template
from loguru import logger

from apps.backend.app.core.config import settings


class EmailService:
    """Servicio para envío de correos electrónicos."""
    
    TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"
    
    @classmethod
    def render_template(cls, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renderiza un template de email con Jinja2.
        
        Args:
            template_name: Nombre del archivo template (ej: 'incapacidad_radicada.html')
            context: Diccionario con variables para el template
            
        Returns:
            HTML renderizado como string
        """
        template_path = cls.TEMPLATES_DIR / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template no encontrado: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        template = Template(template_content)
        return template.render(**context)
    
    @classmethod
    def send_email(
        cls,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Envía un correo electrónico HTML.
        
        Args:
            to: Email del destinatario
            subject: Asunto del correo
            html_body: Contenido HTML del correo
            text_body: Contenido en texto plano (fallback)
            from_email: Email del remitente (opcional, usa settings.EMAIL_FROM por defecto)
            
        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        # Validar configuración SMTP
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning(
                "SMTP no configurado. Email no enviado. "
                "Configure SMTP_USER y SMTP_PASSWORD en las variables de entorno."
            )
            # En desarrollo, solo loggeamos el contenido
            logger.info(f"[EMAIL MOCK] To: {to}")
            logger.info(f"[EMAIL MOCK] Subject: {subject}")
            logger.debug(f"[EMAIL MOCK] Body: {html_body[:200]}...")
            return True  # Retornar True en desarrollo para no bloquear el flujo
        
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email or settings.EMAIL_FROM
            msg['To'] = to
            
            # Agregar versión texto plano si existe
            if text_body:
                part1 = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(part1)
            
            # Agregar versión HTML
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part2)
            
            # Conectar y enviar
            logger.info(f"Conectando a SMTP: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.success(f"Email enviado exitosamente a {to}: {subject}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP al enviar email a {to}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado al enviar email a {to}: {e}")
            return False
    
    @classmethod
    def send_template_email(
        cls,
        to: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None
    ) -> bool:
        """
        Envía un correo usando un template.
        
        Args:
            to: Email del destinatario
            subject: Asunto
            template_name: Nombre del template (ej: 'incapacidad_radicada.html')
            context: Variables para el template
            from_email: Email del remitente (opcional)
            
        Returns:
            True si se envió exitosamente
        """
        try:
            html_body = cls.render_template(template_name, context)
            return cls.send_email(
                to=to,
                subject=subject,
                html_body=html_body,
                from_email=from_email
            )
        except Exception as e:
            logger.error(f"Error al enviar email con template {template_name} a {to}: {e}")
            return False


# Instancia global
email_service = EmailService()
