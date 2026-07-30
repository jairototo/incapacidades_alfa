"""
Lector del excel de la AFP: desprotege (si aplica) y expone la hoja
FORMALIZACION como Worksheet de openpyxl.

Detecta cifrado por magic bytes OLE2/CFB (`\\xd0\\xcf\\x11\\xe0\\xa1\\xb1\\x1a\\xe1`),
NUNCA por extension de archivo -- un .xlsx renombrado sigue detectandose
correctamente, y un .xlsx plano nunca se trata como cifrado solo por su
extension. `bulk_radicacion_service.py:118-119` traga cualquier excepcion de
`load_workbook` bajo un unico mensaje generico; aqui se distinguen tres
mensajes de error segun la causa real:

- "el archivo requiere contraseña"  -> es OLE2 y no se dio password
- "contraseña incorrecta"           -> es OLE2, se dio password, no desencripta
- "no es un Excel válido"           -> ni OLE2 ni un zip OOXML valido

La contraseña NUNCA se loguea ni se incluye en mensajes de excepcion.
"""
import io
from zipfile import BadZipFile

import msoffcrypto
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from app.core.exceptions import BadRequestException

_MAGIC_OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_HOJA_FORMALIZACION = "FORMALIZACION"


def _es_ole2(file_bytes: bytes) -> bool:
    """True si los primeros 8 bytes son la firma OLE2/CFB (contenedor cifrado)."""
    return file_bytes[:8] == _MAGIC_OLE2


def descifrar_si_aplica(file_bytes: bytes, password: str | None) -> bytes:
    """
    Desprotege `file_bytes` si es un contenedor OLE2/CFB; si no lo es, lo
    retorna tal cual (passthrough) -- un .xlsx plano nunca pasa por
    msoffcrypto.

    Args:
        file_bytes: Bytes crudos del archivo subido, cifrado o no.
        password: Contraseña a usar si el archivo esta cifrado. Puede ser
            None -- en ese caso, si el archivo SI esta cifrado, se lanza
            BadRequestException en vez de intentar desencriptar sin clave.

    Returns:
        Bytes del libro sin cifrar (idénticos a `file_bytes` si no estaba
        cifrado).

    Raises:
        BadRequestException: "el archivo requiere contraseña" si esta
            cifrado y `password` es None/vacio; "contraseña incorrecta" si
            `password` no logra desencriptar el archivo.
    """
    if not _es_ole2(file_bytes):
        return file_bytes

    if not password:
        raise BadRequestException("el archivo requiere contraseña")

    try:
        office_file = msoffcrypto.OfficeFile(io.BytesIO(file_bytes))
        office_file.load_key(password=password)
        buffer = io.BytesIO()
        office_file.decrypt(buffer)
    except Exception:
        # Deliberadamente generico: msoffcrypto lanza distintos tipos de
        # excepcion segun el algoritmo de cifrado (InvalidKeyError,
        # DecryptionError, etc.) y ninguno debe filtrarse con la contraseña
        # incluida en su mensaje.
        raise BadRequestException("contraseña incorrecta")

    return buffer.getvalue()


def cargar_hoja_desde_bytes_planos(bytes_planos: bytes) -> Worksheet:
    """
    Abre un libro YA sin cifrar y retorna su hoja FORMALIZACION.

    Separado de `cargar_hoja_formalizacion` para que el llamador (el
    servicio de carga) pueda reusar los mismos `bytes_planos` que ya
    desencripto una vez (p.ej. para archivarlos en storage) sin tener que
    desencriptar el archivo cifrado por segunda vez.

    Raises:
        BadRequestException: "no es un Excel válido" si `bytes_planos` no
            es un .xlsx valido; "Hoja FORMALIZACION no encontrada" si el
            libro no trae esa hoja.
    """
    try:
        wb = openpyxl.load_workbook(io.BytesIO(bytes_planos), data_only=True)
    except BadZipFile:
        raise BadRequestException("no es un Excel válido")
    except Exception:
        raise BadRequestException("no es un Excel válido")

    if _HOJA_FORMALIZACION not in wb.sheetnames:
        raise BadRequestException("Hoja FORMALIZACION no encontrada")

    return wb[_HOJA_FORMALIZACION]


def cargar_hoja_formalizacion(file_bytes: bytes, password: str | None) -> Worksheet:
    """
    Desprotege (si aplica) y carga la hoja FORMALIZACION del libro AFP.

    Args:
        file_bytes: Bytes crudos del archivo subido.
        password: Contraseña del archivo, si esta cifrado.

    Returns:
        Worksheet de openpyxl para la hoja "FORMALIZACION".

    Raises:
        BadRequestException: ver `descifrar_si_aplica` y
            `cargar_hoja_desde_bytes_planos`.
    """
    bytes_planos = descifrar_si_aplica(file_bytes, password)
    return cargar_hoja_desde_bytes_planos(bytes_planos)
