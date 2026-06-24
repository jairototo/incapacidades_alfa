"""Tests for SINIESTRO_REQUERIDO business rule in validate_business_rules.

Task 3.1: ARL incapacidades without a linked siniestro must be flagged as an ERROR.
"""
from datetime import date
import uuid

from app.services.incapacidad_validation_rules import validate_business_rules


def test_siniestro_requerido_fires_when_no_siniestro():
    row = {
        "tipo": "ARL",
        "siniestro_id": None,
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": None,
    }
    issues = validate_business_rules(row)
    assert any(i["codigo"] == "SINIESTRO_REQUERIDO" for i in issues)
    assert next(i for i in issues if i["codigo"] == "SINIESTRO_REQUERIDO")["severidad"] == "ERROR"


def test_siniestro_requerido_does_not_fire_when_linked():
    row = {
        "tipo": "ARL",
        "siniestro_id": uuid.uuid4(),
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": date(2026, 5, 15),
    }
    issues = validate_business_rules(row)
    assert not any(i["codigo"] == "SINIESTRO_REQUERIDO" for i in issues)


def test_siniestro_requerido_not_checked_for_salud():
    row = {
        "tipo": "SALUD",
        "siniestro_id": None,
        "fecha_inicio": date(2026, 6, 1),
        "fecha_fin": date(2026, 6, 10),
        "dias_totales": 10,
        "fecha_siniestro": None,
    }
    issues = validate_business_rules(row)
    assert not any(i["codigo"] == "SINIESTRO_REQUERIDO" for i in issues)
