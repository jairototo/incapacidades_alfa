"""
Tests for previsionales segmentation and AFP column parsing.

Cases taken from real data to ensure accuracy in disability claim processing.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.services.previsionales.segmentacion import (
    ConteoSegmentosError,
    parear_segmentos,
    segmentar,
    split_multivalor,
)


def test_un_solo_mes():
    assert [
        (s.fecha_inicio, s.fecha_fin, s.dias)
        for s in segmentar(date(2026, 7, 11), date(2026, 7, 25))
    ] == [(date(2026, 7, 11), date(2026, 7, 25), 15)]


def test_cruza_fin_de_mes():
    assert [
        (s.fecha_inicio, s.fecha_fin, s.dias)
        for s in segmentar(date(2026, 6, 18), date(2026, 7, 17))
    ] == [(date(2026, 6, 18), date(2026, 6, 30), 13), (date(2026, 7, 1), date(2026, 7, 17), 17)]


def test_cruza_fin_de_ano():
    segs = segmentar(date(2025, 12, 20), date(2026, 1, 10))
    assert [s.dias for s in segs] == [12, 10]
    assert segs[0].fecha_inicio.year == 2025 and segs[1].fecha_inicio.year == 2026


def test_split_acepta_string_con_separador():
    assert split_multivalor("2200110 - 2200110 ") == [Decimal("2200110"), Decimal("2200110")]


def test_split_acepta_numero_suelto():
    # caso real: un solo segmento llega como float
    assert split_multivalor(1750905.0) == [Decimal("1750905")]


def test_split_vacio():
    assert split_multivalor(None) == [] and split_multivalor("") == []


def test_conteo_desalineado_lanza():
    # caso real afiliado 23333262
    segs = segmentar(date(2026, 7, 11), date(2026, 7, 25))  # 1 segmento
    with pytest.raises(ConteoSegmentosError):
        parear_segmentos(
            segs,
            ibc=split_multivalor("1750905 - 1750905 - 1750905 - 1750905 - 1750905 "),
            salario=[Decimal(0)] * 5,
            dias_cotizados=[30] * 5,
        )


def test_split_float_precision_no_binary_contamination():
    """
    Regression test: Decimal(str(valor)) must be used, not Decimal(valor).

    When valor is a float like 1234.56, Decimal(float) produces binary
    representation: Decimal('1234.55999999999994543031789362430572509765625').
    Using Decimal(str(valor)) ensures we get the intended value.

    This is critical for AFP calculations where decimal places matter.
    """
    # Test with a float that has decimal places (would exhibit binary precision issues)
    result = split_multivalor(1234.56)
    assert result == [Decimal("1234.56")], (
        f"Expected [Decimal('1234.56')], got {result}. "
        "Float-to-Decimal conversion must use str() to avoid binary contamination."
    )

    # Also test that string input with decimals works
    result_str = split_multivalor("1234.56")
    assert result_str == [Decimal("1234.56")]

    # Verify the two paths produce identical results
    assert split_multivalor(1234.56) == split_multivalor("1234.56")
