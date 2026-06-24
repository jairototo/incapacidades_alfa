"""
Servicio de notificación para incapacidades en estado GLOSADA.

Responsabilidades:
1. Generar PDF con carta de glosa (usando reportlab).
2. Guardar PDF como Documento ligado a la incapacidad (tipo OTROS).
3. Enviar email a empresa.email_contacto con el PDF adjunto.

Diseño: best-effort — los errores se registran en el log pero NO
revientan la transición de estado que los invoca.
"""
from __future__ import annotations

import hashlib
import io
import smtplib
from datetime import datetime
from email import encoders
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from uuid import uuid4

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.documento import Documento
from app.models.incapacidad import Incapacidad
from app.utils.enums import TipoDocumentoAdjunto


# ---------------------------------------------------------------------------
# PDF Generation
# ---------------------------------------------------------------------------


def _generar_pdf_glosa(incapacidad: Incapacidad, motivo: str) -> bytes:
    """
    Genera el PDF de la carta de glosa usando reportlab.

    El PDF incluye:
    - Membrete "Seguros Alfa"
    - Número de caso / radicado
    - Nombre del beneficiario (empleado o afiliado)
    - Empresa (si aplica)
    - Período (fecha_inicio – fecha_fin)
    - Código CIE-10
    - Motivo de glosa
    - Fecha de emisión

    Returns:
        bytes — contenido del PDF (comienza con b'%PDF')
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6,
        textColor=colors.HexColor("#1a3a5c"),
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=4,
        textColor=colors.HexColor("#4a4a4a"),
    )
    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#666666"),
    )
    value_style = ParagraphStyle(
        "ValueStyle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.black,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )

    # Helpers
    def _nombre_beneficiario() -> str:
        if incapacidad.empleado:
            return f"{incapacidad.empleado.nombres} {incapacidad.empleado.apellidos}"
        if incapacidad.afiliado:
            return f"{incapacidad.afiliado.nombres} {incapacidad.afiliado.apellidos}"
        return "N/A"

    def _nombre_empresa() -> str:
        if incapacidad.empresa:
            return incapacidad.empresa.razon_social
        return "N/A"

    fecha_emision = datetime.utcnow().strftime("%d de %B de %Y")

    story = []

    # --- Membrete ---
    story.append(Paragraph("SEGUROS ALFA", title_style))
    story.append(Paragraph("Sistema de Gestión de Incapacidades", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 0.4 * cm))

    # --- Título del documento ---
    story.append(
        Paragraph(
            "COMUNICACIÓN DE GLOSA DE INCAPACIDAD",
            ParagraphStyle(
                "DocTitle",
                parent=styles["Heading2"],
                fontSize=13,
                alignment=1,  # CENTER
                textColor=colors.HexColor("#c0392b"),
                spaceAfter=10,
            ),
        )
    )

    # --- Tabla de datos del caso ---
    data = [
        [Paragraph("N° Radicado:", label_style), Paragraph(str(incapacidad.numero), value_style)],
        [Paragraph("Beneficiario:", label_style), Paragraph(_nombre_beneficiario(), value_style)],
        [Paragraph("Empresa:", label_style), Paragraph(_nombre_empresa(), value_style)],
        [
            Paragraph("Período:", label_style),
            Paragraph(
                f"{incapacidad.fecha_inicio.strftime('%d/%m/%Y')} – "
                f"{incapacidad.fecha_fin.strftime('%d/%m/%Y')} "
                f"({incapacidad.dias_totales} días)",
                value_style,
            ),
        ],
        [
            Paragraph("CIE-10:", label_style),
            Paragraph(str(incapacidad.diagnostico_cie10 or "N/A"), value_style),
        ],
        [Paragraph("Fecha de emisión:", label_style), Paragraph(fecha_emision, value_style)],
    ]

    table = Table(data, colWidths=[4 * cm, 12 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    # --- Motivo de glosa ---
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            "MOTIVO DE GLOSA",
            ParagraphStyle(
                "SectionTitle",
                parent=styles["Heading3"],
                fontSize=11,
                textColor=colors.HexColor("#1a3a5c"),
                spaceAfter=4,
            ),
        )
    )
    story.append(Paragraph(str(motivo), body_style))
    story.append(Spacer(1, 0.5 * cm))

    # --- Nota informativa ---
    story.append(
        Paragraph(
            "Esta comunicación es generada automáticamente por el Sistema de Gestión de "
            "Incapacidades de Seguros Alfa. Si tiene dudas sobre esta glosa, comuníquese "
            "con su ejecutivo de cuenta o escriba a noreply@incapacidades.com.",
            ParagraphStyle(
                "NoteStyle",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#888888"),
                leading=11,
            ),
        )
    )

    doc.build(story)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Persist PDF as Documento
# ---------------------------------------------------------------------------


async def _guardar_pdf_como_documento(
    db: AsyncSession,
    incapacidad: Incapacidad,
    pdf_bytes: bytes,
) -> Documento:
    """
    Guarda los bytes del PDF como un registro Documento (tipo OTROS)
    asociado a la incapacidad.  La ruta de storage es local al filesystem
    virtualizado — el PDF vive como artefacto interno del sistema, no es
    descargable públicamente.
    """
    nombre_archivo = f"glosa_{incapacidad.numero}.pdf"
    ruta_storage = f"glosas/{incapacidad.id}/{nombre_archivo}"

    md5 = hashlib.md5(pdf_bytes).hexdigest()
    sha256 = hashlib.sha256(pdf_bytes).hexdigest()

    documento = Documento(
        incapacidad_id=incapacidad.id,
        tipo_documento=TipoDocumentoAdjunto.OTROS,
        nombre_archivo=nombre_archivo,
        nombre_original=nombre_archivo,
        ruta_storage=ruta_storage,
        bucket="incapacidades",
        mime_type="application/pdf",
        tamanio_bytes=len(pdf_bytes),
        hash_md5=md5,
        hash_sha256=sha256,
        uploaded_by_id=None,
        validado=True,
    )

    db.add(documento)
    await db.flush()  # persiste dentro de la transacción abierta
    logger.info(
        f"[GLOSADA] PDF guardado como Documento {documento.id} para incapacidad {incapacidad.numero}"
    )
    return documento


# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------


async def _enviar_email_glosa(
    incapacidad: Incapacidad,
    motivo: str,
    pdf_bytes: bytes,
) -> None:
    """
    Envía el email de notificación de glosa.

    Recipient: incapacidad.empresa.email_contacto
    Fallback for SALUD (no empresa): incapacidad.afiliado.email
    Si no hay ningún email disponible, registra warning y retorna sin error.
    """
    destinatario = _resolver_destinatario(incapacidad)
    if not destinatario:
        logger.warning(
            f"[GLOSADA] Sin email de destinatario para incapacidad {incapacidad.numero} — "
            "notificación omitida"
        )
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            f"[GLOSADA][EMAIL MOCK] SMTP no configurado. "
            f"Email a {destinatario} (glosa {incapacidad.numero}) NO enviado."
        )
        return

    # Construir mensaje
    msg = MIMEMultipart()
    msg["Subject"] = f"Notificación de Glosa — Incapacidad {incapacidad.numero}"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = destinatario

    # Cuerpo HTML
    nombre_beneficiario = _nombre_beneficiario(incapacidad)
    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333">
      <h2 style="color:#c0392b;">Notificación de Glosa de Incapacidad</h2>
      <p>Estimado/a,</p>
      <p>Le informamos que la incapacidad con número de radicado
         <strong>{incapacidad.numero}</strong> correspondiente a
         <strong>{nombre_beneficiario}</strong> ha sido <strong>GLOSADA</strong>.</p>
      <table style="border-collapse:collapse;width:100%;max-width:500px">
        <tr><td style="padding:6px;background:#f0f4f8;"><strong>Radicado</strong></td>
            <td style="padding:6px;">{incapacidad.numero}</td></tr>
        <tr><td style="padding:6px;background:#f8f9fa;"><strong>Período</strong></td>
            <td style="padding:6px;">{incapacidad.fecha_inicio} – {incapacidad.fecha_fin}
            ({incapacidad.dias_totales} días)</td></tr>
        <tr><td style="padding:6px;background:#f0f4f8;"><strong>CIE-10</strong></td>
            <td style="padding:6px;">{incapacidad.diagnostico_cie10 or 'N/A'}</td></tr>
        <tr><td style="padding:6px;background:#f8f9fa;"><strong>Motivo de glosa</strong></td>
            <td style="padding:6px;">{motivo}</td></tr>
      </table>
      <p>Adjunto encontrará la carta formal de glosa en formato PDF.</p>
      <p style="color:#888;font-size:12px;">
        Este mensaje es generado automáticamente. No responda a este correo.
      </p>
    </body></html>
    """
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Adjuntar PDF
    pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=f"glosa_{incapacidad.numero}.pdf",
    )
    msg.attach(pdf_attachment)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.success(
            f"[GLOSADA] Email enviado a {destinatario} para incapacidad {incapacidad.numero}"
        )
    except smtplib.SMTPException as exc:
        logger.error(
            f"[GLOSADA] Error SMTP enviando email para {incapacidad.numero}: {exc}"
        )
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def notificar_glosada(
    db: AsyncSession,
    incapacidad: Incapacidad,
    motivo_glosa: str,
) -> None:
    """
    Orquesta la notificación completa de glosa:

    1. Genera PDF con carta de glosa.
    2. Guarda PDF como Documento en DB (tipo OTROS, nombre glosa_{numero}.pdf).
    3. Envía email con PDF adjunto al destinatario de la empresa/afiliado.

    Este método es best-effort: el llamador ya captura las excepciones y
    logea el error sin revertir la transición de estado.
    """
    logger.info(f"[GLOSADA] Iniciando notificación para incapacidad {incapacidad.numero}")

    pdf_bytes = _generar_pdf_glosa(incapacidad, motivo_glosa)
    await _guardar_pdf_como_documento(db, incapacidad, pdf_bytes)
    await _enviar_email_glosa(incapacidad, motivo_glosa, pdf_bytes)

    logger.info(f"[GLOSADA] Notificación completada para incapacidad {incapacidad.numero}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolver_destinatario(incapacidad: Incapacidad) -> Optional[str]:
    """
    Determina el email destinatario para la notificación de glosa.

    Prioridad:
    1. empresa.email_contacto (ARL siempre tiene empresa)
    2. afiliado.email (SALUD)
    3. None → no se envía email
    """
    if incapacidad.empresa and incapacidad.empresa.email_contacto:
        return incapacidad.empresa.email_contacto
    if incapacidad.afiliado and incapacidad.afiliado.email:
        return incapacidad.afiliado.email
    return None


def _nombre_beneficiario(incapacidad: Incapacidad) -> str:
    if incapacidad.empleado:
        return f"{incapacidad.empleado.nombres} {incapacidad.empleado.apellidos}"
    if incapacidad.afiliado:
        return f"{incapacidad.afiliado.nombres} {incapacidad.afiliado.apellidos}"
    return "N/A"
