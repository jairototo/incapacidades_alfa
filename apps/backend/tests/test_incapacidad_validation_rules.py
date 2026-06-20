import datetime as dt
from app.services.incapacidad_validation_rules import validate_field_level, validate_business_rules


def _valid_row():
    return dict(
        empleado_numero_documento="123456", tipo="ARL", tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="M545", nombre_medico="Dr X", registro_medico="RM-1",
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


def test_field_level_flags_invalid_tipo_enfermedad():
    row = _valid_row(); row["tipo_enfermedad"] = "GRIPA"
    issues = validate_field_level(row)
    assert any(i["codigo"] == "INVALID_TIPO_ENFERMEDAD" and i["severidad"] == "ERROR" for i in issues)


def test_field_level_accepts_every_catalog_tipo_enfermedad():
    for tipo in ("ACCIDENTE_TRABAJO", "ENFERMEDAD_LABORAL", "ACCIDENTE_TRAYECTO"):
        row = _valid_row(); row["tipo_enfermedad"] = tipo
        assert not any(i["codigo"] == "INVALID_TIPO_ENFERMEDAD" for i in validate_field_level(row))


def test_field_level_flags_invalid_cie10_format():
    row = _valid_row(); row["diagnostico_cie10"] = "BADCODE"
    issues = validate_field_level(row)
    assert any(i["codigo"] == "INVALID_CIE10_FORMAT" and i["severidad"] == "ERROR" for i in issues)


def test_field_level_accepts_lowercase_cie10():
    row = _valid_row(); row["diagnostico_cie10"] = "m545"
    assert not any(i["codigo"] == "INVALID_CIE10_FORMAT" for i in validate_field_level(row))


def test_field_level_accepts_x_filler_cie10():
    # Código colombiano con cuarto carácter "X" de relleno (sin subcategoría), ej: A09X.
    row = _valid_row(); row["diagnostico_cie10"] = "A09X"
    assert not any(i["codigo"] == "INVALID_CIE10_FORMAT" for i in validate_field_level(row))


def test_field_level_rejects_dotted_cie10():
    # El formato internacional con punto (A04.8) NO se usa en Colombia → debe rechazarse.
    row = _valid_row(); row["diagnostico_cie10"] = "A04.8"
    assert any(i["codigo"] == "INVALID_CIE10_FORMAT" for i in validate_field_level(row))


def test_field_level_flags_nonexistent_cie10_when_catalog_provided():
    # U999 cumple el formato pero no está en el catálogo → CIE10_NO_EXISTE (ERROR).
    row = _valid_row(); row["diagnostico_cie10"] = "U999"
    issues = validate_field_level(row, catalogo_codigos={"M545"})
    assert any(i["codigo"] == "CIE10_NO_EXISTE" and i["severidad"] == "ERROR" for i in issues)


def test_field_level_accepts_existing_cie10_when_catalog_provided():
    row = _valid_row(); row["diagnostico_cie10"] = "m545"  # normaliza a M545
    assert not any(i["codigo"] == "CIE10_NO_EXISTE" for i in validate_field_level(row, catalogo_codigos={"M545"}))


def test_field_level_skips_catalog_check_when_no_catalog():
    # Sin catálogo (None, por defecto) la verificación de existencia se omite.
    row = _valid_row(); row["diagnostico_cie10"] = "U999"
    assert not any(i["codigo"] == "CIE10_NO_EXISTE" for i in validate_field_level(row))


def test_field_level_no_existence_check_when_format_invalid():
    # Si el formato es inválido no tiene sentido evaluar existencia (sería ruido).
    row = _valid_row(); row["diagnostico_cie10"] = "BADCODE"
    codigos = {i["codigo"] for i in validate_field_level(row, catalogo_codigos={"M545"})}
    assert "INVALID_CIE10_FORMAT" in codigos
    assert "CIE10_NO_EXISTE" not in codigos


def test_empty_cie10_reports_empty_not_format():
    row = _valid_row(); row["diagnostico_cie10"] = ""
    codigos = {i["codigo"] for i in validate_field_level(row)}
    assert "EMPTY_DIAGNOSTICO_CIE10" in codigos
    assert "INVALID_CIE10_FORMAT" not in codigos


def test_valid_row_has_no_field_issues():
    assert validate_field_level(_valid_row()) == []
