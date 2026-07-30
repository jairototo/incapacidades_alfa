"""Tests para parsers de Excel tolerantes (Previsionales)."""
import pytest
from datetime import date, datetime
from decimal import Decimal

from app.services.previsionales.excel_common import (
    CeldaInvalidaError,
    parse_fecha,
    parse_decimal,
    parse_entero,
    parse_radicado,
    texto,
    es_vacio,
    normalizar_encabezado,
)


# ============================================================================
# Tests para parse_fecha (tolerante a múltiples formatos)
# ============================================================================

class TestParseFecha:
    """Pruebas para parse_fecha con d/m/yyyy, dd/mm/yyyy, yyyy-mm-dd, yyyy/mm/dd."""

    def test_fecha_dia_sin_cero(self):
        """Debe parsear 9/05/2026 como date(2026, 5, 9)."""
        assert parse_fecha("9/05/2026") == date(2026, 5, 9)

    def test_fecha_dia_con_cero(self):
        """Debe parsear 18/06/2026 como date(2026, 6, 18)."""
        assert parse_fecha("18/06/2026") == date(2026, 6, 18)

    def test_fecha_datetime_passthrough(self):
        """Debe convertir datetime a date."""
        result = parse_fecha(datetime(2025, 10, 2))
        assert result == date(2025, 10, 2)

    def test_fecha_date_passthrough(self):
        """Debe pasar directamente date."""
        d = date(2025, 10, 2)
        assert parse_fecha(d) == d

    def test_fecha_formato_yyyy_mm_dd(self):
        """Debe parsear yyyy-mm-dd."""
        assert parse_fecha("2026-05-09") == date(2026, 5, 9)

    def test_fecha_formato_yyyy_slash_mm_slash_dd(self):
        """Debe parsear yyyy/mm/dd."""
        assert parse_fecha("2026/05/09") == date(2026, 5, 9)

    def test_fecha_dd_mm_yyyy(self):
        """Debe parsear dd/mm/yyyy con dos dígitos en día."""
        assert parse_fecha("09/05/2026") == date(2026, 5, 9)

    def test_fecha_invalida_lanza(self):
        """Debe lanzar CeldaInvalidaError para texto no parseable."""
        with pytest.raises(CeldaInvalidaError):
            parse_fecha("no es fecha")

    def test_fecha_vacia_retorna_none(self):
        """Debe retornar None para None o cadena vacía."""
        assert parse_fecha(None) is None
        assert parse_fecha("") is None
        assert parse_fecha("   ") is None


# ============================================================================
# Tests para parse_decimal
# ============================================================================

class TestParseDecimal:
    """Pruebas para parse_decimal."""

    def test_decimal_de_string(self):
        """Debe parsear string con número decimal."""
        assert parse_decimal("123.45") == Decimal("123.45")

    def test_decimal_de_float(self):
        """Debe parsear float."""
        assert parse_decimal(123.45) == Decimal("123.45")

    def test_decimal_de_int(self):
        """Debe parsear int."""
        assert parse_decimal(123) == Decimal("123")

    def test_decimal_con_coma(self):
        """Debe parsear números con coma como separador decimal."""
        assert parse_decimal("123,45") == Decimal("123.45")

    def test_decimal_vacio_retorna_none(self):
        """Debe retornar None para None o cadena vacía."""
        assert parse_decimal(None) is None
        assert parse_decimal("") is None

    def test_decimal_invaldo_lanza(self):
        """Debe lanzar para string no numérico."""
        with pytest.raises(CeldaInvalidaError):
            parse_decimal("no es numero")


# ============================================================================
# Tests para parse_entero
# ============================================================================

class TestParseEntero:
    """Pruebas para parse_entero."""

    def test_entero_de_string(self):
        """Debe parsear string con número entero."""
        assert parse_entero("123") == 123

    def test_entero_de_int(self):
        """Debe pasar directamente int."""
        assert parse_entero(123) == 123

    def test_entero_de_float_integer(self):
        """Debe parsear float que es entero (123.0 → 123)."""
        assert parse_entero(123.0) == 123

    def test_entero_vacio_retorna_none(self):
        """Debe retornar None para None o cadena vacía."""
        assert parse_entero(None) is None
        assert parse_entero("") is None

    def test_entero_invalido_lanza(self):
        """Debe lanzar para string no numérico."""
        with pytest.raises(CeldaInvalidaError):
            parse_entero("no es numero")


# ============================================================================
# Tests para parse_radicado (float a string sin decimales)
# ============================================================================

class TestParseRadicado:
    """Pruebas para parse_radicado (floats deben convertir via int, nunca str(float))."""

    def test_radicado_float_16_digitos(self):
        """Debe convertir float 16 dígitos a string sin punto decimal."""
        assert parse_radicado(4107413227182500.0) == "4107413227182500"

    def test_radicado_float_15_digitos(self):
        """Debe convertir float 15 dígitos a string sin punto decimal."""
        assert parse_radicado(103862022114100.0) == "103862022114100"

    def test_radicado_string(self):
        """Debe pasar directamente string."""
        assert parse_radicado("4107413227182500") == "4107413227182500"

    def test_radicado_int(self):
        """Debe convertir int a string."""
        assert parse_radicado(4107413227182500) == "4107413227182500"

    def test_radicado_vacio_retorna_none(self):
        """Debe retornar None para None o cadena vacía."""
        assert parse_radicado(None) is None
        assert parse_radicado("") is None


# ============================================================================
# Tests para texto
# ============================================================================

class TestTexto:
    """Pruebas para texto."""

    def test_texto_de_string(self):
        """Debe limpiar y retornar string."""
        assert texto("  hola mundo  ") == "hola mundo"

    def test_texto_de_numero(self):
        """Debe convertir número a string."""
        assert texto(123) == "123"

    def test_texto_vacio_retorna_none(self):
        """Debe retornar None para None o cadena vacía."""
        assert texto(None) is None
        assert texto("") is None
        assert texto("   ") is None


# ============================================================================
# Tests para es_vacio
# ============================================================================

class TestEsVacio:
    """Pruebas para es_vacio."""

    def test_es_vacio_none(self):
        """None debe ser vacio."""
        assert es_vacio(None) is True

    def test_es_vacio_string_vacio(self):
        """String vacío debe ser vacio."""
        assert es_vacio("") is True

    def test_es_vacio_string_espacios(self):
        """String con solo espacios debe ser vacio."""
        assert es_vacio("   ") is True

    def test_es_vacio_numero_cero(self):
        """0 no es vacio."""
        assert es_vacio(0) is False

    def test_es_vacio_string_con_contenido(self):
        """String con contenido no es vacio."""
        assert es_vacio("hola") is False


# ============================================================================
# Tests para normalizar_encabezado
# ============================================================================

class TestNormalizarEncabezado:
    """Pruebas para normalizar_encabezado."""

    def test_encabezado_tolerante(self):
        """Debe normalizar espacios, tildes y mayúsculas."""
        assert (
            normalizar_encabezado(" OBSERVACIÓN  ALFA ")
            == normalizar_encabezado("observacion alfa")
        )

    def test_encabezado_remove_accents(self):
        """Debe remover acentos y tildes."""
        assert normalizar_encabezado("INFORMACIÓN") == "informacion"

    def test_encabezado_lowercase(self):
        """Debe convertir a minúsculas."""
        assert normalizar_encabezado("HOLA MUNDO") == "hola mundo"

    def test_encabezado_collapse_whitespace(self):
        """Debe colapsar espacios múltiples."""
        assert normalizar_encabezado("  hola   mundo  ") == "hola mundo"

    def test_encabezado_special_chars(self):
        """Debe manejar caracteres especiales españoles."""
        assert normalizar_encabezado("Ñiño Año") == "nino ano"
