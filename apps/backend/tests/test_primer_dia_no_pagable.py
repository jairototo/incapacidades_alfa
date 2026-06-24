"""Tests for PRIMER_DIA_NO_PAGABLE business rule.

Task 3.2: When fecha_inicio == fecha_siniestro (same day), the first day is NOT payable,
so the rule fires and auditar_incapacidad() blocks LIQUIDACION (full), forcing LIQUIDACION_PARCIAL.
"""
from datetime import date
import uuid

from app.services.incapacidad_validation_rules import validate_business_rules


def test_primer_dia_no_pagable_fires_when_dates_match():
    row = {
        "tipo": "ARL",
        "siniestro_id": uuid.uuid4(),
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": date(2026, 6, 1),  # same as fecha_inicio
    }
    issues = validate_business_rules(row)
    assert any(i["codigo"] == "PRIMER_DIA_NO_PAGABLE" for i in issues)
    matching = next(i for i in issues if i["codigo"] == "PRIMER_DIA_NO_PAGABLE")
    assert matching["severidad"] == "ERROR"
    assert matching["categoria"] == "BUSINESS_RULE"


def test_primer_dia_no_pagable_does_not_fire_when_dates_differ():
    row = {
        "tipo": "ARL",
        "siniestro_id": uuid.uuid4(),
        "fecha_inicio": date(2026, 6, 2),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 9,
        "fecha_siniestro": date(2026, 6, 1),  # different
    }
    issues = validate_business_rules(row)
    assert not any(i["codigo"] == "PRIMER_DIA_NO_PAGABLE" for i in issues)


def test_primer_dia_no_pagable_does_not_fire_for_salud():
    """SALUD incapacidades have no siniestro, so rule must not apply."""
    row = {
        "tipo": "SALUD",
        "siniestro_id": None,
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": date(2026, 6, 1),  # same day — would fire for ARL
    }
    issues = validate_business_rules(row)
    assert not any(i["codigo"] == "PRIMER_DIA_NO_PAGABLE" for i in issues)


def test_primer_dia_no_pagable_does_not_fire_without_siniestro_id():
    """ARL with no siniestro_id: SINIESTRO_REQUERIDO fires but not PRIMER_DIA_NO_PAGABLE."""
    row = {
        "tipo": "ARL",
        "siniestro_id": None,
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": date(2026, 6, 1),
    }
    issues = validate_business_rules(row)
    assert not any(i["codigo"] == "PRIMER_DIA_NO_PAGABLE" for i in issues)
    assert any(i["codigo"] == "SINIESTRO_REQUERIDO" for i in issues)


def test_primer_dia_no_pagable_does_not_fire_without_fecha_siniestro():
    """ARL with siniestro_id but no fecha_siniestro in dict: rule must not fire."""
    row = {
        "tipo": "ARL",
        "siniestro_id": uuid.uuid4(),
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": None,
    }
    issues = validate_business_rules(row)
    assert not any(i["codigo"] == "PRIMER_DIA_NO_PAGABLE" for i in issues)
