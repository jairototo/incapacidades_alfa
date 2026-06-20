import datetime as dt
from app.services.incapacidad_validation_rules import validate_field_level, validate_business_rules


def _valid_row():
    return dict(
        empleado_numero_documento="123456", tipo="ARL", tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1",
    )


def test_field_level_flags_missing_document():
    row = _valid_row(); row["empleado_numero_documento"] = ""
    issues = validate_field_level(row)
    assert any(i["codigo"] == "EMPTY_EMPLEADO_NUMERO" for i in issues)


def test_field_level_flags_inverted_dates():
    row = _valid_row(); row["fecha_fin"] = dt.date(2026, 5, 1)
    issues = validate_field_level(row)
    assert any(i["codigo"] == "INVALID_DATE_RANGE" for i in issues)


def test_business_rules_flag_dias_mismatch():
    row = _valid_row(); row["dias_totales"] = 99
    issues = validate_business_rules(row)
    assert any(i["codigo"] == "DIAS_TOTALES_MISMATCH" for i in issues)


def test_valid_row_has_no_field_issues():
    assert validate_field_level(_valid_row()) == []
