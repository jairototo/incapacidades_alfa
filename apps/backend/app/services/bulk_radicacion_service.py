"""Servicio de radicación masiva: plantilla Excel, parseo+validación, mapeo ZIP."""
import io
from uuid import UUID

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.empleado import Empleado

TEMPLATE_HEADERS = [
    "numero_documento", "tipo_documento", "empleado_nombres", "empleado_apellidos",
    "tipo_enfermedad", "fecha_inicio", "fecha_fin", "dias_totales", "diagnostico_cie10",
    "descripcion_diagnostico", "nombre_medico", "registro_medico", "ips", "valor_dia",
    "prorroga", "observaciones",
]


async def generar_plantilla(db: AsyncSession, empresa_id: UUID, empleado_ids: list[UUID]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Incapacidades"
    ws.append(TEMPLATE_HEADERS)
    if empleado_ids:
        empleados = (
            await db.execute(
                select(Empleado).where(
                    Empleado.id.in_(empleado_ids),
                    Empleado.empresa_id == empresa_id,
                )
            )
        ).scalars().all()
        for e in empleados:
            ws.append([
                e.numero_documento,
                str(e.tipo_documento),
                e.nombres,
                e.apellidos,
                "",   # tipo_enfermedad
                "",   # fecha_inicio
                "",   # fecha_fin
                "",   # dias_totales
                "",   # diagnostico_cie10
                "",   # descripcion_diagnostico
                "",   # nombre_medico
                "",   # registro_medico
                "",   # ips
                "",   # valor_dia
                "NO", # prorroga
                "",   # observaciones
            ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
