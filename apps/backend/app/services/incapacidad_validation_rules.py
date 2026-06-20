"""Reglas de validación reutilizables sobre una fila/dict de incapacidad.

Origen: PreIncapacidadValidationService. Aquí son funciones puras (dict -> issues),
reutilizadas por la radicación masiva (validación de Excel) y por el job de auditoría
(Phase 4, mapeando una Incapacidad a dict).
"""
from datetime import date


def _issue(codigo, categoria, severidad, descripcion, campo=None):
    return {"codigo": codigo, "categoria": categoria, "severidad": severidad,
            "descripcion": descripcion, "campo_afectado": campo}


def validate_field_level(row: dict) -> list[dict]:
    issues: list[dict] = []
    req = {
        "empleado_numero_documento": "EMPTY_EMPLEADO_NUMERO",
        "tipo_enfermedad": "EMPTY_TIPO_ENFERMEDAD",
        "diagnostico_cie10": "EMPTY_DIAGNOSTICO_CIE10",
        "nombre_medico": "EMPTY_NOMBRE_MEDICO",
        "registro_medico": "EMPTY_REGISTRO_MEDICO",
    }
    for campo, codigo in req.items():
        if not row.get(campo):
            issues.append(_issue(codigo, "FIELD_VALIDATION", "ERROR", f"{campo} es requerido", campo))

    if row.get("tipo") not in ("ARL", "SALUD"):
        issues.append(_issue("INVALID_TIPO", "FIELD_VALIDATION", "ERROR", "Tipo debe ser ARL o SALUD", "tipo"))
    if not row.get("fecha_inicio"):
        issues.append(_issue("EMPTY_FECHA_INICIO", "FIELD_VALIDATION", "ERROR", "Fecha de inicio requerida", "fecha_inicio"))
    if not row.get("fecha_fin"):
        issues.append(_issue("EMPTY_FECHA_FIN", "FIELD_VALIDATION", "ERROR", "Fecha de fin requerida", "fecha_fin"))
    if row.get("fecha_inicio") and row.get("fecha_fin") and row["fecha_fin"] < row["fecha_inicio"]:
        issues.append(_issue("INVALID_DATE_RANGE", "FIELD_VALIDATION", "ERROR",
                             "Fecha de fin no puede ser anterior a fecha de inicio", "fecha_fin"))
    return issues


def validate_business_rules(row: dict) -> list[dict]:
    issues: list[dict] = []
    fi, ff, dias = row.get("fecha_inicio"), row.get("fecha_fin"), row.get("dias_totales")
    if fi and ff:
        expected = (ff - fi).days + 1
        if dias is not None and dias != expected:
            issues.append(_issue("DIAS_TOTALES_MISMATCH", "BUSINESS_RULE", "WARNING",
                                 f"Días totales ({dias}) no coincide con el rango ({expected})", "dias_totales"))
    if fi and (date.today() - fi).days > 30:
        issues.append(_issue("RETROACTIVE_BEYOND_LIMIT", "BUSINESS_RULE", "WARNING",
                             "Incapacidad retroactiva más de 30 días", "fecha_inicio"))
    if dias and dias > 180:
        issues.append(_issue("DURATION_EXCEEDS_LIMIT", "BUSINESS_RULE", "WARNING",
                             "Duración excede 180 días", "dias_totales"))
    return issues


def validate_row(row: dict) -> list[dict]:
    return validate_field_level(row) + validate_business_rules(row)
