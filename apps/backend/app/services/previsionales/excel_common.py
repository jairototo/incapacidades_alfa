"""
Parsers tolerantes para Excel: fecha, decimal, entero, radicado, texto.
Validación de encabezados con normalización.
"""
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.core.exceptions import BadRequestException


class CeldaInvalidaError(ValueError):
    """Excepción lanzada cuando un valor de celda no puede ser parseado."""
    pass


def _text(v) -> Optional[str]:
    """Convierte una celda Excel a texto limpio, o None si está vacía."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _is_empty(v) -> bool:
    """Retorna True si el valor es None, cadena vacía o solo espacios."""
    return v is None or (isinstance(v, str) and not v.strip()) or v == ""


def es_vacio(v) -> bool:
    """Retorna True si el valor está vacío (None, cadena vacía o espacios)."""
    return _is_empty(v)


def texto(v) -> Optional[str]:
    """Convierte una celda Excel a texto limpio, o None si está vacía."""
    return _text(v)


def parse_fecha(v) -> Optional[date]:
    """
    Convierte un valor de celda Excel a date.
    Acepta:
    - datetime → extrae .date()
    - date → retorna igual
    - None o cadena vacía → None
    - String en formatos: d/m/yyyy, dd/mm/yyyy, yyyy-mm-dd, yyyy/mm/dd

    Lanza CeldaInvalidaError si no puede parsear el texto.
    """
    if _is_empty(v):
        return None

    if isinstance(v, datetime):
        return v.date()

    if isinstance(v, date):
        return v

    # Es string, intentar múltiples formatos
    s = str(v).strip()

    # Formatos a intentar (en orden de probabilidad)
    formatos = [
        r'^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$',  # d/m/yyyy o dd/mm/yyyy
        r'^(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})$',  # yyyy-mm-dd o yyyy/mm/dd
    ]

    for patron in formatos:
        match = re.match(patron, s)
        if match:
            groups = match.groups()

            # Primer patrón: d(d)/m(m)/yyyy
            if len(groups[2]) == 4 and len(groups[0]) <= 2 and len(groups[1]) <= 2:
                try:
                    dia = int(groups[0])
                    mes = int(groups[1])
                    ano = int(groups[2])
                    return date(ano, mes, dia)
                except (ValueError, TypeError):
                    pass

            # Segundo patrón: yyyy-mm-dd o yyyy/mm/dd
            if len(groups[0]) == 4:
                try:
                    ano = int(groups[0])
                    mes = int(groups[1])
                    dia = int(groups[2])
                    return date(ano, mes, dia)
                except (ValueError, TypeError):
                    pass

    raise CeldaInvalidaError(f"Fecha inválida: {s!r}. Use formatos d/m/yyyy, dd/mm/yyyy, yyyy-mm-dd o yyyy/mm/dd")


def parse_decimal(v) -> Optional[Decimal]:
    """
    Convierte un valor de celda Excel a Decimal.
    Acepta None/cadena vacía → None.
    Maneja números con coma como separador decimal.
    Lanza CeldaInvalidaError si no puede parsear.
    """
    if _is_empty(v):
        return None

    # Si es float o int, convertir directo
    if isinstance(v, (int, float)):
        try:
            return Decimal(str(v))
        except (InvalidOperation, ValueError, TypeError):
            raise CeldaInvalidaError(f"Decimal inválido: {v!r}")

    # Es string, limpiar y reemplazar coma por punto
    s = str(v).strip().replace(",", ".")

    try:
        return Decimal(s)
    except (InvalidOperation, ValueError, TypeError):
        raise CeldaInvalidaError(f"Decimal inválido: {s!r}")


def parse_entero(v) -> Optional[int]:
    """
    Convierte un valor de celda Excel a int.
    Acepta None/cadena vacía → None.
    Float que es entero (123.0) → 123.
    Lanza CeldaInvalidaError si no puede parsear.
    """
    if _is_empty(v):
        return None

    if isinstance(v, int):
        return v

    if isinstance(v, float):
        if v.is_integer():
            return int(v)
        raise CeldaInvalidaError(f"Entero inválido (decimal no-entero): {v!r}")

    # Es string, intentar parsear
    s = str(v).strip()
    try:
        return int(s)
    except (ValueError, TypeError):
        raise CeldaInvalidaError(f"Entero inválido: {s!r}")


def parse_radicado(v) -> Optional[str]:
    """
    Convierte un valor de celda Excel a string (radicado number).
    IMPORTANTE: floats deben convertir via int() primero, NUNCA str(float).
    Ejemplo: 103862022114100.0 → int(103862022114100.0) → str(...) → "103862022114100"
    (NO "103862022114100.0")

    Acepta None/cadena vacía → None.
    Lanza CeldaInvalidaError si no puede convertir.
    """
    if _is_empty(v):
        return None

    if isinstance(v, str):
        return v.strip()

    if isinstance(v, float):
        # Validar que sea un float que representa un entero
        if v.is_integer():
            return str(int(v))
        raise CeldaInvalidaError(f"Radicado inválido (float no-entero): {v!r}")

    if isinstance(v, int):
        return str(v)

    # Intentar conversión
    try:
        return str(int(v))
    except (ValueError, TypeError, OverflowError):
        raise CeldaInvalidaError(f"Radicado inválido: {v!r}")


def normalizar_encabezado(s: str) -> str:
    """
    Normaliza un string de encabezado:
    - Remueve acentos y tildes (ó → o, ñ → n, etc.)
    - Convierte a minúsculas
    - Colapsa espacios múltiples a uno

    Ejemplo: " OBSERVACIÓN  ALFA " → "observacion alfa"
    """
    if not isinstance(s, str):
        s = str(s)

    # Remover acentos y tildes usando NFD + filtro
    s_nfd = unicodedata.normalize("NFD", s)
    s_sin_tildes = "".join(
        c for c in s_nfd if unicodedata.category(c) != "Mn"
    )

    # Minúsculas
    s_lower = s_sin_tildes.lower()

    # Colapsar espacios múltiples
    s_collapsed = re.sub(r"\s+", " ", s_lower).strip()

    return s_collapsed


def validar_encabezados(ws, esperados: dict[str, str], fila: int) -> None:
    """
    Valida los encabezados de una hoja openpyxl.

    Parámetros:
    - ws: Worksheet de openpyxl
    - esperados: dict mapping column-letter → expected-header-text
      Ejemplo: {"A": "ID", "B": "Nombre", "C": "Fecha"}
    - fila: Número de fila (1-indexed) donde están los encabezados

    Lanza BadRequestException si algún encabezado no coincide (normalizados).
    """
    # Mapear letras de columna (A, B, C, ...) a índices (1, 2, 3, ...)
    col_map = {}
    for col_letter, expected_text in esperados.items():
        # Convertir letra a número de columna (A=1, B=2, ..., Z=26, AA=27, ...)
        col_num = 0
        for char in col_letter.upper():
            col_num = col_num * 26 + (ord(char) - ord("A") + 1)
        col_map[col_num] = (col_letter, expected_text)

    # Leer la fila de encabezados
    row_values = list(ws.iter_rows(min_row=fila, max_row=fila, values_only=True))[0]

    # Validar cada columna esperada
    for col_num, (col_letter, expected_text) in col_map.items():
        # Ajustar índice (openpyxl 1-indexed, list 0-indexed)
        cell_value = row_values[col_num - 1] if col_num <= len(row_values) else None

        # Obtener texto de la celda
        found_text = _text(cell_value) or ""

        # Normalizar ambos lados
        expected_normalized = normalizar_encabezado(expected_text)
        found_normalized = normalizar_encabezado(found_text)

        # Comparar
        if expected_normalized != found_normalized:
            raise BadRequestException(
                f"Encabezado en columna {col_letter} no coincide. "
                f"Esperado: {expected_text!r}. Encontrado: {found_text!r}."
            )
