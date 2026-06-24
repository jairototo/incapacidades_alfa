"""
Tareas de Celery para vinculación de siniestros externos.

Patrón asyncio.run() para evitar conflictos de event loop con Celery.
"""
import asyncio
from uuid import UUID

from celery.exceptions import Ignore
from loguru import logger

from app.tasks import celery_app
from app.utils.enums import EstadoIncapacidad


@celery_app.task(
    name="tasks.vincular_siniestro_externo",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
    acks_late=True,
)
def vincular_siniestro_externo_task(self, incapacidad_id: str, numero_siniestro: str) -> dict:
    """
    Tarea Celery: consulta siniestro externo, crea/encuentra registro local,
    y retorna la incapacidad a EN_AUDITORIA.

    Args:
        incapacidad_id: UUID de la incapacidad (como string)
        numero_siniestro: Número de siniestro en el sistema externo

    Returns:
        dict con status y detalles
    """
    logger.info(
        f"[CELERY] Vinculando siniestro {numero_siniestro} "
        f"para incapacidad {incapacidad_id}"
    )

    try:
        result = asyncio.run(
            _vincular_siniestro_async(UUID(incapacidad_id), numero_siniestro)
        )
        logger.success(
            f"[CELERY] Siniestro {numero_siniestro} vinculado a {incapacidad_id}: {result}"
        )
        return result
    except Exception as exc:
        logger.error(
            f"[CELERY] Error vinculando siniestro {numero_siniestro} "
            f"en incapacidad {incapacidad_id}: {exc}"
        )
        raise


async def _vincular_siniestro_async(
    incapacidad_id: UUID, numero_siniestro: str
) -> dict:
    """
    Lógica async principal: busca el siniestro en API externa, lo crea localmente
    si no existe, vincula a la incapacidad y transiciona a EN_AUDITORIA.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker as sa_sessionmaker
    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async_session_factory = sa_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        async with async_session_factory() as db:
            result = await _vincular_en_session(db, incapacidad_id, numero_siniestro)
    finally:
        await engine.dispose()

    return result


async def _vincular_en_session(
    db, incapacidad_id: UUID, numero_siniestro: str
) -> dict:
    """
    Operación principal en sesión activa.
    Separado para facilitar testing directo con db_session de conftest.

    All mutations are flushed individually and committed once at the end.
    If anything raises, the async with AsyncSession block rolls back automatically.
    """
    from app.db.repositories.siniestro_repository import SiniestroRepository
    from app.db.repositories.incapacidad_repository import incapacidad_repository
    from app.models.siniestro import Siniestro
    from app.models.historial_estado import HistorialEstado
    from app.schemas.historial_estado import HistorialEstadoCreate

    # 1. Obtener incapacidad
    inc = await incapacidad_repository.get_by_id(db, incapacidad_id)
    if not inc:
        logger.error(f"[SINIESTRO-TASK] Incapacidad {incapacidad_id} no encontrada")
        return {"status": "error", "error": "Incapacidad no encontrada"}

    if inc.estado != EstadoIncapacidad.CREACION_SINIESTRO:
        logger.warning(
            f"[SINIESTRO-TASK] Incapacidad {incapacidad_id} ya no está en "
            f"CREACION_SINIESTRO (estado actual: {inc.estado})"
        )
        return {"status": "skipped", "estado_actual": str(inc.estado)}

    # 2. Obtener datos del siniestro externo
    siniestro_data = await _fetch_external_siniestro(numero_siniestro, inc)

    # 3. Buscar o crear siniestro local — flush only (no commit yet)
    siniestro_repo = SiniestroRepository()
    siniestro = await siniestro_repo.get_by_numero(db, numero_siniestro)

    if not siniestro:
        logger.info(
            f"[SINIESTRO-TASK] Creando siniestro local para {numero_siniestro}"
        )
        siniestro = await siniestro_repo.create_flushed(db, siniestro_data)

    # 4. Vincular siniestro a incapacidad y transicionar a EN_AUDITORIA — flush only
    estado_anterior = inc.estado
    await incapacidad_repository.update_flushed(
        db,
        id=incapacidad_id,
        obj_in={
            "siniestro_id": siniestro.id,
            "estado": EstadoIncapacidad.EN_AUDITORIA,
        },
    )

    # 5. Crear entrada de historial — flush only
    historial_data = HistorialEstadoCreate(
        entity_type="incapacidad",
        entity_id=incapacidad_id,
        estado_anterior=estado_anterior.value,
        estado_nuevo=EstadoIncapacidad.EN_AUDITORIA.value,
        observacion=f"Siniestro {numero_siniestro} vinculado automáticamente por el sistema",
        cambiado_por_id=None,
    )
    historial = HistorialEstado(**historial_data.model_dump())
    db.add(historial)
    await db.flush()

    # 6. Single commit — atomically persists steps 3, 4, and 5
    await db.commit()

    logger.success(
        f"[SINIESTRO-TASK] Incapacidad {incapacidad_id} retornada a EN_AUDITORIA "
        f"con siniestro {siniestro.id}"
    )

    return {
        "status": "success",
        "incapacidad_id": str(incapacidad_id),
        "siniestro_id": str(siniestro.id),
        "numero_siniestro": numero_siniestro,
    }


async def _fetch_external_siniestro(numero_siniestro: str, incapacidad=None) -> dict:
    """
    Consulta API_RRHH_BASE_URL para obtener datos del siniestro.
    Si la API no responde o no está configurada, retorna un stub con datos de la incapacidad.

    Raises:
        Ignore: When empleado_id or empresa_id are None (permanent failure, stop retrying).

    Returns:
        dict con campos requeridos para crear un Siniestro local
    """
    from app.core.config import settings
    from app.utils.enums import TipoSiniestro, GravedadSiniestro, SyncSource, EstadoSiniestro
    from datetime import date as date_type, datetime

    # Datos de fallback derivados de la incapacidad
    fallback_empleado_id = incapacidad.empleado_id if incapacidad else None
    fallback_empresa_id = incapacidad.empresa_id if incapacidad else None
    fallback_fecha = incapacidad.fecha_inicio if incapacidad else date_type.today()

    if settings.API_RRHH_BASE_URL:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                headers = {}
                if settings.API_RRHH_API_KEY:
                    headers["X-Api-Key"] = settings.API_RRHH_API_KEY

                resp = await client.get(
                    f"{settings.API_RRHH_BASE_URL}/siniestros/{numero_siniestro}",
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info(
                        f"[SINIESTRO-TASK] Datos obtenidos de API externa para {numero_siniestro}"
                    )
                    # Normalizar campos requeridos, usando fallbacks de la incapacidad
                    resolved_empleado_id = data.get("empleado_id") or fallback_empleado_id
                    resolved_empresa_id = data.get("empresa_id") or fallback_empresa_id

                    if resolved_empleado_id is None or resolved_empresa_id is None:
                        logger.error(
                            f"[SINIESTRO-TASK] empleado_id o empresa_id es None para "
                            f"siniestro {numero_siniestro} — falla permanente, no reintentar"
                        )
                        raise Ignore()

                    return {
                        "numero_siniestro": numero_siniestro,
                        "empleado_id": resolved_empleado_id,
                        "empresa_id": resolved_empresa_id,
                        "fecha_siniestro": data.get("fecha_siniestro") or fallback_fecha,
                        "tipo_siniestro": TipoSiniestro(
                            data.get("tipo_siniestro", TipoSiniestro.ACCIDENTE_TRABAJO)
                        ),
                        "descripcion": data.get("descripcion") or f"Siniestro {numero_siniestro}",
                        "gravedad": GravedadSiniestro(
                            data.get("gravedad", GravedadSiniestro.LEVE)
                        ),
                        "estado": EstadoSiniestro.REPORTADO,
                        "sync_source": SyncSource.API,
                        "external_id": numero_siniestro,
                        "fecha_reporte": datetime.utcnow(),
                    }
                else:
                    logger.warning(
                        f"[SINIESTRO-TASK] API externa retornó {resp.status_code} "
                        f"para {numero_siniestro}"
                    )
        except Ignore:
            raise
        except Exception as exc:
            logger.warning(
                f"[SINIESTRO-TASK] No se pudo contactar API externa: {exc} — usando stub"
            )

    # Stub cuando API no está disponible
    logger.info(
        f"[SINIESTRO-TASK] Usando stub para siniestro {numero_siniestro}"
    )
    from datetime import datetime

    # Guard: empleado_id and empresa_id must not be None (NOT NULL FK constraint)
    if fallback_empleado_id is None or fallback_empresa_id is None:
        logger.error(
            f"[SINIESTRO-TASK] empleado_id o empresa_id es None en stub fallback para "
            f"siniestro {numero_siniestro} — falla permanente, no reintentar"
        )
        raise Ignore()

    from app.utils.enums import TipoSiniestro, GravedadSiniestro, SyncSource, EstadoSiniestro

    return {
        "numero_siniestro": numero_siniestro,
        "empleado_id": fallback_empleado_id,
        "empresa_id": fallback_empresa_id,
        "fecha_siniestro": fallback_fecha,
        "tipo_siniestro": TipoSiniestro.ACCIDENTE_TRABAJO,
        "descripcion": (
            f"Siniestro {numero_siniestro} (pendiente de sincronización con sistema externo)"
        ),
        "gravedad": GravedadSiniestro.LEVE,
        "estado": EstadoSiniestro.REPORTADO,
        "sync_source": SyncSource.API,
        "external_id": numero_siniestro,
        "fecha_reporte": datetime.utcnow(),
    }
