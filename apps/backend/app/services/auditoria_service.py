"""Auditoría de una Incapacidad: evalúa reglas, persiste cada resultado y transiciona a EN_AUDITORIA.

Reusa las funciones puras de incapacidad_validation_rules (Phase 3 Task 3).
Por cada regla en REGLAS_ESPERADAS registra un AuditoriaResultado con aprobado=True cuando la regla
no disparó, o aprobado=False con el detalle del issue cuando sí.
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.incapacidad import Incapacidad
from app.models.auditoria_resultado import AuditoriaResultado
from app.services.incapacidad_validation_rules import validate_field_level, validate_business_rules, validate_audit_only_rules
from app.utils.enums import EstadoIncapacidad

# Reglas que SIEMPRE se evalúan (para registrar también las que pasan).
REGLAS_ESPERADAS = [
    ("EMPTY_EMPLEADO_NUMERO", "FIELD_VALIDATION"),
    ("EMPTY_TIPO_ENFERMEDAD", "FIELD_VALIDATION"),
    ("EMPTY_DIAGNOSTICO_CIE10", "FIELD_VALIDATION"),
    ("EMPTY_NOMBRE_MEDICO", "FIELD_VALIDATION"),
    ("EMPTY_REGISTRO_MEDICO", "FIELD_VALIDATION"),
    ("INVALID_DATE_RANGE", "FIELD_VALIDATION"),
    ("DIAS_TOTALES_MISMATCH", "BUSINESS_RULE"),
    ("RETROACTIVE_BEYOND_LIMIT", "BUSINESS_RULE"),
    ("DURATION_EXCEEDS_LIMIT", "BUSINESS_RULE"),
    ("SINIESTRO_REQUERIDO", "BUSINESS_RULE"),
    ("PRIMER_DIA_NO_PAGABLE", "BUSINESS_RULE"),  # added in Task 3.2
]


def _incapacidad_to_row(inc: Incapacidad) -> dict:
    """Mapea una Incapacidad ORM a un dict que entienden validate_field_level / validate_business_rules."""
    return {
        "tipo": inc.tipo.value if hasattr(inc.tipo, "value") else str(inc.tipo),
        "empleado_numero_documento": inc.empleado.numero_documento if inc.empleado else None,
        "tipo_enfermedad": inc.subtipo,
        "fecha_inicio": inc.fecha_inicio,
        "fecha_fin": inc.fecha_fin,
        "dias_totales": inc.dias_totales,
        "diagnostico_cie10": inc.diagnostico_cie10,
        "nombre_medico": inc.nombre_medico,
        "registro_medico": inc.registro_medico,
        "siniestro_id": inc.siniestro_id,
        "fecha_siniestro": inc.siniestro.fecha_siniestro if inc.siniestro else None,
    }


async def auditar_incapacidad(db: AsyncSession, incapacidad_id: UUID) -> None:
    """
    Evalúa todas las reglas de REGLAS_ESPERADAS sobre la Incapacidad dada,
    persiste un AuditoriaResultado por regla y transiciona el estado a EN_AUDITORIA.

    Args:
        db: Sesión async de SQLAlchemy (el caller maneja el ciclo de vida de la sesión)
        incapacidad_id: ID de la incapacidad a auditar
    """
    # Eager-load empleado y siniestro para evitar MissingGreenlet en _incapacidad_to_row
    inc = (await db.execute(
        select(Incapacidad)
        .options(
            selectinload(Incapacidad.empleado),
            selectinload(Incapacidad.siniestro),
        )
        .where(Incapacidad.id == incapacidad_id)
    )).scalar_one_or_none()

    if inc is None:
        logger.warning(f"Auditoría: incapacidad {incapacidad_id} no encontrada")
        return

    # Evaluar reglas y construir mapa {codigo: issue}
    row = _incapacidad_to_row(inc)
    issues = validate_field_level(row) + validate_business_rules(row) + validate_audit_only_rules(row)
    failed_by_code = {i["codigo"]: i for i in issues}

    # Persistir un AuditoriaResultado por cada regla esperada
    for codigo, categoria in REGLAS_ESPERADAS:
        issue = failed_by_code.get(codigo)
        db.add(AuditoriaResultado(
            incapacidad_id=inc.id,
            regla=codigo,
            categoria=categoria,
            aprobado=issue is None,
            severidad=issue["severidad"] if issue else "INFO",
            detalle=issue["descripcion"] if issue else "Regla cumplida",
        ))

    # Transicionar estado RADICADA → EN_AUDITORIA
    estado_anterior = inc.estado
    inc.estado = EstadoIncapacidad.EN_AUDITORIA
    db.add(inc)

    # Registrar historial usando historial_estado_service (best-effort)
    await _registrar_historial(db, inc, estado_anterior)

    await db.commit()
    logger.info(
        f"Auditoría completa para {inc.numero}: {len(REGLAS_ESPERADAS)} reglas evaluadas "
        f"({len(failed_by_code)} fallidas) → EN_AUDITORIA"
    )


async def _registrar_historial(
    db: AsyncSession,
    inc: Incapacidad,
    estado_anterior: EstadoIncapacidad,
) -> None:
    """
    Registra el cambio de estado en historial_estado mediante historial_estado_service.create_historial_entry.

    La llamada real coincide con la firma usada en incapacidad_service.radicar_incapacidad:
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=<UUID>,
            estado_anterior=<str|None>,
            estado_nuevo=<str>,
            observacion=<str>,
            cambiado_por_id=None,
            flush_only=True,  # commit lo hace auditar_incapacidad después
        )
    Está envuelto en try/except para que un fallo de historial nunca bloquee la transición.
    """
    try:
        from app.services.historial_estado_service import historial_estado_service
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=inc.id,
            estado_anterior=estado_anterior.value if estado_anterior else None,
            estado_nuevo=EstadoIncapacidad.EN_AUDITORIA.value,
            observacion="Transición automática por job de auditoría",
            cambiado_por_id=None,
            flush_only=True,
        )
    except Exception as exc:
        logger.error(f"No se pudo registrar historial para {inc.id}: {exc}")
