"""Servicio de radicación masiva: plantilla Excel, parseo+validación, mapeo ZIP."""
import datetime as dt
import io
import re
import zipfile
from uuid import UUID

from openpyxl import Workbook, load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.models.empleado import Empleado
from app.services.incapacidad_validation_rules import validate_row

TEMPLATE_HEADERS = [
    "numero_documento", "tipo_documento", "empleado_nombres", "empleado_apellidos",
    "tipo_enfermedad", "fecha_inicio", "fecha_fin", "dias_totales", "diagnostico_cie10",
    "descripcion_diagnostico", "nombre_medico", "registro_medico", "ips",
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
                "NO", # prorroga
                "",   # observaciones
            ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _parse_date(v) -> "dt.date | None":
    """Convierte un valor de celda Excel a date, o None si está vacío."""
    if v in (None, ""):
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = str(v).strip()
    try:
        return dt.date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        raise ValueError(f"Fecha inválida: {s!r}. Use formato YYYY-MM-DD.")


def _parse_int(v):
    """Convierte un valor de celda Excel a int, o None si está vacío."""
    if v in (None, ""):
        return None
    try:
        return int(float(str(v)))   # handles "5", "5.0", 5, 5.0
    except (ValueError, TypeError):
        raise ValueError(f"Valor no numérico: {v!r}")


def _text(v):
    """Convierte una celda Excel a texto limpio, o None si está vacía.

    openpyxl entrega los números como int/float; los campos de texto de la
    plantilla (registro_medico, nombre_medico, ips, ...) deben llegar como
    str para no romper la validación Pydantic en la radicación. Los enteros
    que llegan como float (p.ej. ``5.0``) se rinden como ``"5"``.
    """
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _is_empty(values) -> bool:
    """Retorna True si todos los valores de la fila son None, cadena vacía o solo espacios."""
    return all(v is None or (isinstance(v, str) and not v.strip()) or v == "" for v in values)


async def parsear_y_validar(db: AsyncSession, empresa_id: UUID, file_bytes: bytes) -> list[dict]:
    """Parsea el Excel, valida cada fila y retorna resultados por fila.

    - Filas completamente vacías (o solo espacios) son omitidas.
    - Cada empleado se resuelve por numero_documento DENTRO de la empresa autenticada.
    - Se retornan TODOS los errores por fila (no solo el primero).
    - Celdas con valores inválidos generan un error de fila (no un 500).
    - Archivos corruptos o no-Excel generan un 400.
    """
    try:
        wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception:
        raise BadRequestException("El archivo no es un Excel válido (.xlsx).")

    ws = wb.active
    if ws is None:
        raise BadRequestException("El archivo Excel no contiene hojas activas.")

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
        numero_documento = _text(data.get("numero_documento")) or ""
        empleado = by_doc.get(numero_documento)
        raw_datos = {k: _text(v) for k, v in data.items()}

        try:
            parsed = {
                "tipo": "ARL",
                "empleado_numero_documento": numero_documento,
                "tipo_enfermedad": _text(data.get("tipo_enfermedad")),
                "fecha_inicio": _parse_date(data.get("fecha_inicio")),
                "fecha_fin": _parse_date(data.get("fecha_fin")),
                "dias_totales": _parse_int(data.get("dias_totales")),
                "diagnostico_cie10": _text(data.get("diagnostico_cie10")),
                "descripcion_diagnostico": _text(data.get("descripcion_diagnostico")),
                "nombre_medico": _text(data.get("nombre_medico")),
                "registro_medico": _text(data.get("registro_medico")),
                "ips": _text(data.get("ips")),
                "prorroga": str(data.get("prorroga") or "").strip().upper() in ("SI", "SÍ", "TRUE", "1", "YES"),
                "observaciones": _text(data.get("observaciones")),
            }
        except ValueError as exc:
            resultados.append({
                "fila": idx,
                "empleado_id": str(empleado.id) if empleado else None,
                "datos": raw_datos,
                "errores": [{"codigo": "INVALID_CELL_VALUE", "categoria": "PARSE_ERROR",
                             "severidad": "ERROR", "descripcion": str(exc), "campo_afectado": None}],
                "valida": False,
            })
            continue

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
                # Campos de presentación que el frontend usa para mostrar la fila
                # y para emparejar documentos del ZIP por número de documento.
                "numero_documento": parsed["empleado_numero_documento"],
                "empleado_nombres": raw_datos.get("empleado_nombres"),
                "empleado_apellidos": raw_datos.get("empleado_apellidos"),
                "fecha_inicio": parsed["fecha_inicio"].isoformat() if parsed["fecha_inicio"] else None,
                "fecha_fin": parsed["fecha_fin"].isoformat() if parsed["fecha_fin"] else None,
            },
            "errores": errores,
            "valida": not any(e.get("severidad") == "ERROR" for e in errores),
        })

    return resultados


# ---------------------------------------------------------------------------
# ZIP filename mapping — pure function, no DB access
# ---------------------------------------------------------------------------

TIPOS_VALIDOS = {"INCAPACIDAD", "HISTORIA_CLINICA", "SOPORTE", "SOPORTE_ADICIONAL"}
_NAME_RE = re.compile(r"^(?P<doc>[A-Za-z0-9]+)_(?P<tipo>[A-Z_]+)\.(?P<ext>[A-Za-z0-9]+)$")
MAX_ZIP_BYTES = 20 * 1024 * 1024


def mapear_zip(file_bytes: bytes, documentos_esperados: set[str]) -> list[dict]:
    """Parsea un ZIP y mapea cada archivo a un (numero_documento, tipo) según convención de nombre.

    Convención: ``{numero_documento}_{TIPO}.{ext}``  (e.g. ``1023555444_INCAPACIDAD.pdf``)

    - Archivos que no cumplen la convención → ``match=False``
    - Archivos con tipo no reconocido o documento fuera de ``documentos_esperados`` → ``match=False``
    - ZIP > 20 MB → ``ValueError``
    - ZIP corrupto → ``ValueError``
    - No realiza operaciones de BD (puro, testeable sin fixtures).
    """
    if len(file_bytes) > MAX_ZIP_BYTES:
        raise ValueError("El ZIP excede el tamaño máximo de 20 MB")
    try:
        zf = zipfile.ZipFile(io.BytesIO(file_bytes))
    except zipfile.BadZipFile:
        raise ValueError("El archivo no es un ZIP válido")
    asignaciones: list[dict] = []
    with zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue  # skip directory entries
            base = name.split("/")[-1]
            m = _NAME_RE.match(base)
            if not m:
                asignaciones.append({
                    "archivo": base,
                    "match": False,
                    "motivo": "Nombre no cumple convención",
                })
                continue
            doc, tipo = m.group("doc"), m.group("tipo")
            ok = tipo in TIPOS_VALIDOS and doc in documentos_esperados
            asignaciones.append({
                "archivo": base,
                "numero_documento": doc,
                "tipo": tipo,
                "match": ok,
                "motivo": None if ok else "Documento o tipo no reconocido",
            })
    return asignaciones
