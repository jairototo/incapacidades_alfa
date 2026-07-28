"""Servicio de carga masiva de empleados: plantilla Excel, parseo+validación, confirmación."""
import datetime as dt
import io
from decimal import Decimal, InvalidOperation

from openpyxl import Workbook, load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.models.empleado import Empleado
from app.models.empresa import Empresa
from app.schemas.empleado_bulk import FilaError
from app.utils.enums import EstadoEmpleado, Genero, TipoDocumento

TEMPLATE_HEADERS = [
    "numero_documento", "tipo_documento", "nombres", "apellidos", "email",
    "telefono", "fecha_nacimiento", "genero", "cargo", "area",
    "fecha_ingreso", "salario_base", "nit_empresa",
]

TEMPLATE_INSTRUCCIONES = [
    ("numero_documento", "Número de documento de identidad. Obligatorio, único por empresa."),
    ("tipo_documento", "CC, CE, TI, PASAPORTE o PEP. Obligatorio."),
    ("nombres", "Nombres del empleado. Obligatorio."),
    ("apellidos", "Apellidos del empleado. Obligatorio."),
    ("email", "Correo del empleado. Opcional."),
    ("telefono", "Teléfono de contacto. Opcional."),
    ("fecha_nacimiento", "Formato YYYY-MM-DD. Opcional."),
    ("genero", "M, F u O. Opcional."),
    ("cargo", "Cargo del empleado. Opcional."),
    ("area", "Área de trabajo. Opcional."),
    ("fecha_ingreso", "Formato YYYY-MM-DD. Obligatorio."),
    ("salario_base", "Salario base numérico. Opcional."),
    ("nit_empresa", "NIT de la empresa a la que pertenece el empleado. Obligatorio, debe existir."),
]


def generar_plantilla_empleados() -> bytes:
    """Genera un .xlsx con encabezados, una fila de ejemplo y una hoja de instrucciones."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Empleados"
    ws.append(TEMPLATE_HEADERS)
    ws.append([
        "1234567890", "CC", "Juan", "Pérez", "juan.perez@correo.com",
        "3001234567", "1990-05-15", "M", "Analista", "Operaciones",
        "2024-01-15", "3000000", "900123456",
    ])

    ws_instrucciones = wb.create_sheet("Instrucciones")
    ws_instrucciones.append(["Columna", "Descripción"])
    for columna, descripcion in TEMPLATE_INSTRUCCIONES:
        ws_instrucciones.append([columna, descripcion])

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


def _text(v):
    """Convierte una celda Excel a texto limpio, o None si está vacía."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _is_empty(values) -> bool:
    """Retorna True si todos los valores de la fila son None, cadena vacía o solo espacios."""
    return all(v is None or (isinstance(v, str) and not v.strip()) or v == "" for v in values)


async def parsear_y_validar_empleados(
    db: AsyncSession, file_bytes: bytes
) -> tuple[list[tuple[int, dict]], list[FilaError]]:
    """Parsea el Excel de empleados y valida fila por fila. No escribe en BD.

    Retorna (filas_validas, errores):
    - filas_validas: lista de (numero_de_fila_excel, dict_listo_para_Empleado)
    - errores: lista de FilaError para las filas inválidas

    Filas completamente vacías son omitidas (no cuentan como error ni como válida).
    """
    try:
        wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception:
        raise BadRequestException("El archivo no es un Excel válido (.xlsx).")

    ws = wb.active
    if ws is None:
        raise BadRequestException("El archivo Excel no contiene hojas activas.")

    empresas_by_nit = {
        e.nit: e for e in (await db.execute(select(Empresa))).scalars().all()
    }
    documentos_existentes = {
        (doc, str(empresa_id))
        for doc, empresa_id in (
            await db.execute(select(Empleado.numero_documento, Empleado.empresa_id))
        ).all()
    }

    filas_validas: list[tuple[int, dict]] = []
    errores: list[FilaError] = []
    documentos_en_archivo: dict[str, int] = {}

    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        cells = list(row) + [None] * (len(TEMPLATE_HEADERS) - len(row))
        if _is_empty(cells):
            continue

        data = dict(zip(TEMPLATE_HEADERS, cells))
        fila_errores: list[FilaError] = []

        numero_documento = _text(data.get("numero_documento"))
        if not numero_documento:
            fila_errores.append(FilaError(fila=idx, columna="numero_documento", mensaje="Campo obligatorio"))

        tipo_documento = _text(data.get("tipo_documento"))
        if not tipo_documento:
            fila_errores.append(FilaError(fila=idx, columna="tipo_documento", mensaje="Campo obligatorio"))
        elif tipo_documento not in {t.value for t in TipoDocumento}:
            fila_errores.append(FilaError(fila=idx, columna="tipo_documento", mensaje=f"Valor inválido: {tipo_documento}"))

        nombres = _text(data.get("nombres"))
        if not nombres:
            fila_errores.append(FilaError(fila=idx, columna="nombres", mensaje="Campo obligatorio"))

        apellidos = _text(data.get("apellidos"))
        if not apellidos:
            fila_errores.append(FilaError(fila=idx, columna="apellidos", mensaje="Campo obligatorio"))

        nit_empresa = _text(data.get("nit_empresa"))
        empresa = None
        if not nit_empresa:
            fila_errores.append(FilaError(fila=idx, columna="nit_empresa", mensaje="Campo obligatorio"))
        else:
            empresa = empresas_by_nit.get(nit_empresa)
            if empresa is None:
                fila_errores.append(FilaError(fila=idx, columna="nit_empresa", mensaje=f"No existe una empresa con NIT {nit_empresa}"))

        fecha_ingreso_raw = data.get("fecha_ingreso")
        fecha_ingreso = None
        if fecha_ingreso_raw in (None, ""):
            fila_errores.append(FilaError(fila=idx, columna="fecha_ingreso", mensaje="Campo obligatorio"))
        else:
            try:
                fecha_ingreso = _parse_date(fecha_ingreso_raw)
            except ValueError as e:
                fila_errores.append(FilaError(fila=idx, columna="fecha_ingreso", mensaje=str(e)))

        fecha_nacimiento_raw = data.get("fecha_nacimiento")
        fecha_nacimiento = None
        if fecha_nacimiento_raw not in (None, ""):
            try:
                fecha_nacimiento = _parse_date(fecha_nacimiento_raw)
            except ValueError as e:
                fila_errores.append(FilaError(fila=idx, columna="fecha_nacimiento", mensaje=str(e)))

        genero = _text(data.get("genero"))
        if genero and genero not in {g.value for g in Genero}:
            fila_errores.append(FilaError(fila=idx, columna="genero", mensaje=f"Valor inválido: {genero}"))

        salario_base = None
        salario_raw = data.get("salario_base")
        if salario_raw not in (None, ""):
            try:
                salario_base = Decimal(str(salario_raw))
            except InvalidOperation:
                fila_errores.append(FilaError(fila=idx, columna="salario_base", mensaje=f"Valor no numérico: {salario_raw!r}"))

        if numero_documento:
            if numero_documento in documentos_en_archivo:
                fila_errores.append(FilaError(
                    fila=idx, columna="numero_documento",
                    mensaje=f"Documento duplicado en el archivo (también en fila {documentos_en_archivo[numero_documento]})",
                ))
            else:
                documentos_en_archivo[numero_documento] = idx

            if empresa and (numero_documento, str(empresa.id)) in documentos_existentes:
                fila_errores.append(FilaError(
                    fila=idx, columna="numero_documento",
                    mensaje=f"Ya existe un empleado con documento {numero_documento} en esta empresa",
                ))

        if fila_errores:
            errores.extend(fila_errores)
            continue

        filas_validas.append((idx, {
            "empresa_id": empresa.id,
            "numero_documento": numero_documento,
            "tipo_documento": tipo_documento,
            "nombres": nombres,
            "apellidos": apellidos,
            "email": _text(data.get("email")),
            "telefono": _text(data.get("telefono")),
            "fecha_nacimiento": fecha_nacimiento,
            "genero": genero,
            "cargo": _text(data.get("cargo")),
            "area": _text(data.get("area")),
            "fecha_ingreso": fecha_ingreso,
            "salario_base": salario_base,
            "estado": EstadoEmpleado.ACTIVO,
        }))

    return filas_validas, errores
