"""
Generación del PDF "Autorización de pago por OCCIRED" para liquidación de
incapacidades.

Dos variantes de la misma plantilla:
- borrador=True  → generada al guardar el borrador de liquidación (POST
  /incapacidades/{id}/liquidacion), con marca de agua "BORRADOR".
- borrador=False → generada al completar la liquidación (POST
  /incapacidades/{id}/liquidacion/completar), sin marca de agua.

tipo_beneficiario y tipo_liquidacion quedan fijos en "Empleador" — pendiente
de definición de negocio (decisión explícita, 2026-07-24).
"""
from __future__ import annotations

import io
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage_core import storage_backend
from app.models.documento import Documento
from app.models.incapacidad import Incapacidad
from app.models.liquidacion import Liquidacion
from app.utils.enums import TipoDocumentoAdjunto

TITULO = "AUTORIZACIÓN DE PAGO POR OCCIRED"
TIPO_BENEFICIARIO_FIJO = "Empleador"
TIPO_LIQUIDACION_FIJO = "Empleador"
NOMBRE_DOCUMENTO_DISPLAY = "Autorizacion de pago por OCCIRED.pdf"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _safe(value: object) -> str:
    if value in (None, ""):
        return "N/A"
    return str(value)


def _fmt_date(value: Optional[date]) -> str:
    return value.strftime("%d/%m/%Y") if value else "N/A"


def _fmt_money(value: Optional[Decimal]) -> str:
    if value is None:
        return "Pendiente"
    return f"${value:,.2f}"


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------


def _draw_watermark(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 90)
    canvas.setFillColor(colors.HexColor("#c0392b"))
    canvas.setFillAlpha(0.15)
    canvas.translate(A4[0] / 2, A4[1] / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "BORRADOR")
    canvas.restoreState()


def _no_watermark(canvas, doc) -> None:
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generar_pdf_autorizacion_pago(
    incapacidad: Incapacidad,
    liquidacion: Liquidacion,
    nombre_ips: Optional[str],
    borrador: bool,
) -> bytes:
    """
    Genera el PDF "Autorización de pago por OCCIRED".

    Returns:
        bytes — contenido del PDF (comienza con b'%PDF')
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Heading1"], fontSize=14, alignment=1,
        textColor=colors.HexColor("#1a3a5c"), spaceAfter=10,
    )
    row_style = ParagraphStyle(
        "RowStyle", parent=styles["Normal"], fontSize=9, leading=12,
    )
    body_style = ParagraphStyle(
        "BodyStyle", parent=styles["Normal"], fontSize=9.5, leading=13, spaceAfter=8,
    )
    right_style = ParagraphStyle(
        "RightStyle", parent=styles["Normal"], fontSize=9.5, alignment=2,
    )
    total_style = ParagraphStyle(
        "TotalStyle", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold",
    )

    empresa = getattr(incapacidad, "empresa", None)
    empleado = getattr(incapacidad, "empleado", None)
    siniestro = getattr(incapacidad, "siniestro", None)

    nombre_empresa = _safe(empresa.razon_social if empresa else None)
    nit_empresa = _safe(empresa.nit if empresa else None)
    nro_contrato = _safe(getattr(empresa, "nro_contrato", None) if empresa else None)
    nombre_empleado = _safe(empleado.nombre_completo if empleado else None)
    identificacion_empleado = _safe(empleado.numero_documento if empleado else None)
    sbc_empleado = _fmt_money(empleado.salario_base) if empleado and empleado.salario_base is not None else "N/A"
    nro_siniestro = _safe(
        siniestro.numero_siniestro if siniestro else getattr(incapacidad, "numero_siniestro", None)
    )
    fecha_siniestro = _fmt_date(siniestro.fecha_siniestro) if siniestro else "N/A"
    sucursal = _safe(siniestro.sucursal if siniestro else None)
    fecha_autorizacion_pago = datetime.now().strftime("%d/%m/%Y")
    dias_incapacidad = liquidacion.dias_autorizados

    story = []
    story.append(Paragraph("SEGUROS ALFA", title_style))
    story.append(Paragraph(TITULO, title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a3a5c")))
    story.append(Spacer(1, 0.4 * cm))

    filas = [
        [Paragraph(
            f"Nro de Siniestro: {nro_siniestro}    Fecha siniestro: {fecha_siniestro}    "
            f"Fecha Autorización de pago: {fecha_autorizacion_pago}",
            row_style,
        )],
        [Paragraph(
            f"COMPAÑÍA_02 - RAMO:07 - SUCURSAL: {sucursal}    SUCURSAL GIRADORA: <b>DIRECCIÓN GENERAL</b>",
            row_style,
        )],
        [Paragraph(
            f"Nombre Empresa: {nombre_empresa}    Nit: {nit_empresa}    Nro de Contrato: {nro_contrato}",
            row_style,
        )],
        [Paragraph(
            f"Empleado: {nombre_empleado}    C.C.: {identificacion_empleado}    S.B.C.: {sbc_empleado}",
            row_style,
        )],
        [Paragraph(
            f"Beneficiario: {nombre_empresa}    NIT: {nit_empresa}    Días de incapacidad: {dias_incapacidad}",
            row_style,
        )],
        [Paragraph(
            f"Tipo de Liquidación: {TIPO_LIQUIDACION_FIJO}    Tipo de Beneficiario: {TIPO_BENEFICIARIO_FIJO}",
            row_style,
        )],
    ]
    tabla_encabezado = Table(filas, colWidths=[16 * cm])
    tabla_encabezado.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tabla_encabezado)
    story.append(Spacer(1, 0.5 * cm))

    fecha_inicio = _fmt_date(liquidacion.fecha_inicio_autorizada)
    fecha_fin = _fmt_date(liquidacion.fecha_fin_autorizada)
    nombre_ips_txt = _safe(nombre_ips)
    story.append(Paragraph(
        f"Pago incapacidad por {dias_incapacidad} días, desde {fecha_inicio} hasta {fecha_fin}, "
        f"expedida por {nombre_ips_txt}. Se autoriza pago por abono en cuenta bancaria, "
        "por los siguientes conceptos:",
        body_style,
    ))
    story.append(Spacer(1, 0.3 * cm))

    concepto_rows = [
        ["DÍAS", "CONCEPTO", "VALOR", "CONCEPTO", "VALOR"],
        [str(dias_incapacidad), "Días incapacidad temporal o prórroga",
         _fmt_money(liquidacion.valor_incapacidad_temporal), "", ""],
        [str(dias_incapacidad), "Días aporte patronal pensión",
         _fmt_money(liquidacion.valor_aporte_patronal_pension),
         "Aporte trabajador pensión", _fmt_money(liquidacion.valor_aporte_trabajador_pension)],
        [str(dias_incapacidad), "Días aporte patronal salud",
         _fmt_money(liquidacion.valor_aporte_patronal_salud),
         "Aporte trabajador salud", _fmt_money(liquidacion.valor_aporte_trabajador_salud)],
        ["", "", "", "Aporte trabajador adicional pensión",
         _fmt_money(liquidacion.valor_aporte_adicional_trabajador_pension)],
        ["", Paragraph("<b>TOTAL A PAGAR</b>", total_style), "", "", _fmt_money(liquidacion.valor_total)],
    ]
    tabla_conceptos = Table(concepto_rows, colWidths=[1.8 * cm, 4.4 * cm, 2.8 * cm, 4.2 * cm, 2.8 * cm])
    tabla_conceptos.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("SPAN", (1, 5), (3, 5)),
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#f0f4f8")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(tabla_conceptos)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph("FECHA LÍMITE DE PAGO: DÍA____ MES____ AÑO____", right_style))

    doc.build(story, onFirstPage=_draw_watermark if borrador else _no_watermark,
               onLaterPages=_draw_watermark if borrador else _no_watermark)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Persistence: guardar_pdf_autorizacion_pago
# ---------------------------------------------------------------------------


async def guardar_pdf_autorizacion_pago(
    db: AsyncSession,
    incapacidad: Incapacidad,
    pdf_bytes: bytes,
) -> Documento:
    """
    Guarda (o reemplaza) el PDF de autorización de pago como Documento de la
    incapacidad. Un único Documento por incapacidad — su contenido pasa de
    borrador (con marca de agua) a final (sin marca de agua) en el mismo
    registro, para que el usuario siempre vea un solo archivo con ese nombre
    en el espacio de documentos.
    """
    result = await db.execute(
        select(Documento).where(
            Documento.incapacidad_id == incapacidad.id,
            Documento.nombre_original == NOMBRE_DOCUMENTO_DISPLAY,
        )
    )
    existente = result.scalar_one_or_none()

    if existente is not None:
        try:
            storage_backend.delete_file(existente.ruta_storage)
        except Exception:
            pass  # archivo físico ya ausente — no bloquear el reemplazo

    ruta_storage, hash_md5, hash_sha256, tamanio_bytes = storage_backend.upload_file(
        file_data=io.BytesIO(pdf_bytes),
        file_name=NOMBRE_DOCUMENTO_DISPLAY,
        content_type="application/pdf",
        folder=f"liquidacion/{incapacidad.id}",
    )

    if existente is not None:
        existente.ruta_storage = ruta_storage
        existente.hash_md5 = hash_md5
        existente.hash_sha256 = hash_sha256
        existente.tamanio_bytes = tamanio_bytes
        await db.flush()
        return existente

    documento = Documento(
        incapacidad_id=incapacidad.id,
        tipo_documento=TipoDocumentoAdjunto.SOPORTE_PAGO,
        nombre_archivo=f"autorizacion_pago_occired_{incapacidad.numero}.pdf",
        nombre_original=NOMBRE_DOCUMENTO_DISPLAY,
        ruta_storage=ruta_storage,
        bucket="incapacidades",
        mime_type="application/pdf",
        tamanio_bytes=tamanio_bytes,
        hash_md5=hash_md5,
        hash_sha256=hash_sha256,
        uploaded_by_id=None,
        validado=True,
    )
    db.add(documento)
    await db.flush()
    return documento
