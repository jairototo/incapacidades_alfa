"""Servicio de radicación masiva: plantilla Excel, parseo+validación, mapeo ZIP."""
import datetime as dt
import io
from uuid import UUID

from openpyxl import Workbook, load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.empleado import Empleado
from app.services.incapacidad_validation_rules import validate_row

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


def _parse_date(v):
    """Convierte un valor de celda Excel a date, o None si está vacío."""
    if v in (None, ""):
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v).strip()[:10])


def _is_empty(values) -> bool:
    """Retorna True si todos los valores de la fila son None o cadena vacía."""
    return all(v in (None, "") for v in values)


async def parsear_y_validar(db: AsyncSession, empresa_id: UUID, file_bytes: bytes) -> list[dict]:
    """Parsea el Excel, valida cada fila y retorna resultados por fila.

    - Filas completamente vacías son omitidas.
    - Cada empleado se resuelve por numero_documento DENTRO de la empresa autenticada.
    - Se retornan TODOS los errores por fila (no solo el primero).
    """
    wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb.active

    # Cargar empleados de la empresa en un dict por numero_documento
    empleados = (
        await db.execute(
            select(Empleado).where(Empleado.empresa_id == empresa_id)
        )
    ).scalars().all()
    by_doc = {e.numero_documento.strip(): e for e in empleados}

    resultados = []
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        cells = list(row) + [None] * (len(TEMPLATE_HEADERS) - len(row))
        if _is_empty(cells):
            continue

        data = dict(zip(TEMPLATE_HEADERS, cells))
        empleado = by_doc.get(str(data.get("numero_documento") or "").strip())

        parsed = {
            "tipo": "ARL",
            "empleado_numero_documento": str(data.get("numero_documento") or "").strip(),
            "tipo_enfermedad": data.get("tipo_enfermedad"),
            "fecha_inicio": _parse_date(data.get("fecha_inicio")),
            "fecha_fin": _parse_date(data.get("fecha_fin")),
            "dias_totales": int(data["dias_totales"]) if data.get("dias_totales") not in (None, "") else None,
            "diagnostico_cie10": data.get("diagnostico_cie10"),
            "descripcion_diagnostico": data.get("descripcion_diagnostico"),
            "nombre_medico": data.get("nombre_medico"),
            "registro_medico": data.get("registro_medico"),
            "ips": data.get("ips"),
            "valor_dia": data.get("valor_dia"),
            "prorroga": str(data.get("prorroga") or "").strip().upper() in ("SI", "SÍ", "TRUE", "1", "YES"),
            "observaciones": data.get("observaciones"),
        }

        errores = validate_row(parsed)

        if empleado is None:
            errores.append({
                "codigo": "EMPLEADO_NO_ENCONTRADO",
                "categoria": "INTEGRATION_CHECK",
                "severidad": "ERROR",
                "descripcion": "Empleado no pertenece a su empresa o no existe",
                "campo_afectado": "numero_documento",
            })

        resultados.append({
            "fila": idx,
            "empleado_id": str(empleado.id) if empleado else None,
            "datos": {
                **parsed,
                "fecha_inicio": parsed["fecha_inicio"].isoformat() if parsed["fecha_inicio"] else None,
                "fecha_fin": parsed["fecha_fin"].isoformat() if parsed["fecha_fin"] else None,
            },
            "errores": errores,
            "valida": len(errores) == 0,
        })

    return resultados
