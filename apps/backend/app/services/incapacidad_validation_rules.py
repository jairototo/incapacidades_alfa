"""Reglas de validación reutilizables sobre una fila/dict de incapacidad.

Origen: PreIncapacidadValidationService. Aquí son funciones puras (dict -> issues),
reutilizadas por la radicación masiva (validación de Excel) y por el job de auditoría
(Phase 4, mapeando una Incapacidad a dict).
"""
from datetime import date

from app.utils.validacion_incapacidad import REGEX_CIE10, TIPOS_ENFERMEDAD


def _issue(codigo, categoria, severidad, descripcion, campo=None):
    return {"codigo": codigo, "categoria": categoria, "severidad": severidad,
            "descripcion": descripcion, "campo_afectado": campo}


def validate_field_level(row: dict, catalogo_codigos: set[str] | None = None) -> list[dict]:
    """Valida campos a nivel de fila.

    ``catalogo_codigos``: si se pasa un set de códigos CIE-10 existentes (en
    mayúsculas), un ``diagnostico_cie10`` con formato válido que NO esté en el
    set genera ``CIE10_NO_EXISTE`` (ERROR). Si es ``None`` (por defecto) la
    verificación de existencia se omite — preserva la pureza para usos sin BD
    (p.ej. el job de auditoría).
    """
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

    # tipo_enfermedad debe pertenecer al catálogo cerrado (solo si viene diligenciado;
    # la ausencia ya la reporta EMPTY_TIPO_ENFERMEDAD arriba).
    tipo_enf = row.get("tipo_enfermedad")
    if tipo_enf and tipo_enf not in TIPOS_ENFERMEDAD:
        issues.append(_issue(
            "INVALID_TIPO_ENFERMEDAD", "FIELD_VALIDATION", "ERROR",
            f"Tipo de enfermedad debe ser uno de: {', '.join(TIPOS_ENFERMEDAD)}", "tipo_enfermedad"))

    # diagnostico_cie10 debe cumplir el formato CIE-10 (solo si viene diligenciado).
    cie10 = row.get("diagnostico_cie10")
    if cie10:
        cie10_norm = str(cie10).strip().upper()
        if not REGEX_CIE10.match(cie10_norm):
            issues.append(_issue(
                "INVALID_CIE10_FORMAT", "FIELD_VALIDATION", "ERROR",
                "Formato CIE-10 inválido (ej: A048, M545 o A09X)", "diagnostico_cie10"))
        elif catalogo_codigos is not None and cie10_norm not in catalogo_codigos:
            issues.append(_issue(
                "CIE10_NO_EXISTE", "FIELD_VALIDATION", "ERROR",
                f"El código CIE-10 '{cie10_norm}' no existe en el catálogo", "diagnostico_cie10"))
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
                             "Incapacidad retroactiva emisión de hace más de 30 días", "fecha_inicio"))
    if dias and dias > 180:
        issues.append(_issue("DURATION_EXCEEDS_LIMIT", "BUSINESS_RULE", "WARNING",
                             "Duración excede 180 días", "dias_totales"))
    return issues


def validate_row(row: dict, catalogo_codigos: set[str] | None = None) -> list[dict]:
    return validate_field_level(row, catalogo_codigos) + validate_business_rules(row)
