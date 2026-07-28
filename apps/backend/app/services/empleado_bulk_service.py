"""Servicio de carga masiva de empleados: plantilla Excel, parseo+validación, confirmación."""
import io

from openpyxl import Workbook

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
