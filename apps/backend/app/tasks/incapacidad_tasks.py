"""
Tareas de Celery para incapacidades.

IMPORTANTE: Usa sesiones SÍNCRONAS (psycopg2) para evitar problemas de event loop con asyncpg.
"""
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from loguru import logger

from app.tasks import celery_app
from app.core.exceptions import NotFoundException, ValidationException
from app.utils.enums import EstadoIncapacidad
from app.tasks.email_tasks import send_incapacidad_radicada_email_task


# Variables globales para lazy initialization
_sync_engine = None
_SyncSessionLocal = None


def get_sync_session():
    """
    Obtener sesión síncrona para Celery (lazy initialization).
    Evita problemas de import circular.
    """
    global _sync_engine, _SyncSessionLocal
    
    if _SyncSessionLocal is None:
        from app.core.config import settings
        
        # Motor síncrono: reemplazar +asyncpg con psycopg2
        sync_database_uri = settings.DATABASE_URL.replace("+asyncpg", "")
        _sync_engine = create_engine(
            sync_database_uri,
            pool_pre_ping=True,
            echo=False,
            pool_size=5,
            max_overflow=10
        )
        _SyncSessionLocal = sessionmaker(
            bind=_sync_engine,
            autoflush=False,
            autocommit=False
        )
    
    return _SyncSessionLocal()


@celery_app.task(
    name="auditar_incapacidad",
    bind=True,
    max_retries=3,
    acks_late=True
)
def auditar_incapacidad_task(self, incapacidad_id: str):
    """
    Tarea de Celery para ejecutar la auditoría automática de una incapacidad (ASÍNCRONA).

    Transición: RADICADA → EN_AUDITORIA (+ persiste auditoria_resultado)

    Args:
        incapacidad_id: UUID de la incapacidad (como string)

    Raises:
        Exception: Si falla, reintenta hasta 3 veces con 10 s de espera
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    logger.info(f"[CELERY] Iniciando auditoría para incapacidad {incapacidad_id}")

    async def run():
        from app.core.config import settings
        from app.services.auditoria_service import auditar_incapacidad

        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )

        async with async_session() as db:
            await auditar_incapacidad(db, UUID(incapacidad_id))

        await engine.dispose()

    try:
        asyncio.run(run())
        logger.success(f"[CELERY] Auditoría completada para incapacidad {incapacidad_id}")
    except Exception as exc:
        logger.error(f"[CELERY] Error auditando incapacidad {incapacidad_id}: {exc}")
        raise self.retry(exc=exc, countdown=10)


def enqueue_auditoria_incapacidad(incapacidad_id) -> None:
    """Hook usado por RadicacionPipelineService (reemplaza el no-op de Phase 2)."""
    auditar_incapacidad_task.delay(str(incapacidad_id))


@celery_app.task(
    name="radicar_incapacidad_automatica",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30},
    retry_backoff=True,
    acks_late=True
)
def radicar_incapacidad_automatica_task(self, incapacidad_id: str):
    """
    Tarea de Celery para radicar una incapacidad automáticamente (SÍNCRONA).
    
    Transición: RADICADA → EN_AUDITORIA
    
    Args:
        incapacidad_id: UUID de la incapacidad (como string)
        
    Returns:
        dict: Resultado de la operación
        
    Raises:
        Exception: Si falla después de 3 reintentos
    """
    logger.info(f"[CELERY] Iniciando radicación automática para incapacidad {incapacidad_id}")
    
    try:
        incap_uuid = UUID(incapacidad_id)
    except ValueError as e:
        logger.error(f"[CELERY] ID de incapacidad inválido: {incapacidad_id}")
        return {
            "status": "error",
            "incapacidad_id": incapacidad_id,
            "error": "ID inválido"
        }
    
    db: Session = get_sync_session()
    try:
        # Importar modelos (lazy import para evitar circularidad)
        from app.models.incapacidad import Incapacidad
        from app.models.historial_estado import HistorialEstado
        
        # 1. Obtener incapacidad (query síncrona)
        incapacidad = db.query(Incapacidad).filter(Incapacidad.id == incap_uuid).first()
        
        if not incapacidad:
            logger.error(f"[CELERY] Incapacidad {incapacidad_id} no encontrada")
            return {
                "status": "error",
                "incapacidad_id": incapacidad_id,
                "error": "Incapacidad no encontrada"
            }
        
        # 2. Verificar estado actual (idempotencia)
        if incapacidad.estado == EstadoIncapacidad.EN_AUDITORIA:
            logger.warning(
                f"[CELERY] Incapacidad {incapacidad_id} ya está EN_AUDITORIA. No se requiere acción."
            )
            return {
                "status": "already_processed",
                "incapacidad_id": incapacidad_id,
                "estado": "EN_AUDITORIA",
                "numero": incapacidad.numero,
                "message": "Ya radicada previamente"
            }
        
        if incapacidad.estado != EstadoIncapacidad.RADICADA:
            logger.warning(
                f"[CELERY] Incapacidad {incapacidad_id} tiene estado {incapacidad.estado}, "
                f"no se puede radicar (solo desde RADICADA)"
            )
            return {
                "status": "invalid_state",
                "incapacidad_id": incapacidad_id,
                "estado_actual": incapacidad.estado.value if hasattr(incapacidad.estado, 'value') else str(incapacidad.estado),
                "message": "Estado inválido para radicación"
            }
        
        # 3. Cambiar estado
        estado_anterior = incapacidad.estado
        incapacidad.estado = EstadoIncapacidad.EN_AUDITORIA
        
        # 4. Crear registro en historial_estado
        historial = HistorialEstado(
            entity_type="incapacidad",
            entity_id=incapacidad.id,
            estado_anterior=estado_anterior.value if hasattr(estado_anterior, 'value') else str(estado_anterior),
            estado_nuevo=EstadoIncapacidad.EN_AUDITORIA.value,
            observacion="Radicación automática por sistema (background task)",
            cambiado_por_id=None  # Sistema
        )
        db.add(historial)
        
        # 5. Commit
        db.commit()
        db.refresh(incapacidad)
        
        logger.success(
            f"[CELERY] Incapacidad {incapacidad_id} radicada exitosamente. "
            f"Estado: {incapacidad.estado.value}. Número: {incapacidad.numero}"
        )
        
        # 6. Lanzar tarea de email (asíncrona, no bloqueante)
        try:
            # Preparar datos para el email
            from datetime import datetime
            
            # Determinar beneficiario (empleado o afiliado)
            beneficiario_nombre = "N/A"
            beneficiario_documento = "N/A"
            tipo_documento_str = "N/A"
            
            if incapacidad.empleado:
                beneficiario_nombre = f"{incapacidad.empleado.nombres} {incapacidad.empleado.apellidos}"
                beneficiario_documento = incapacidad.empleado.numero_documento
                tipo_documento_str = incapacidad.empleado.tipo_documento.value if hasattr(incapacidad.empleado.tipo_documento, 'value') else str(incapacidad.empleado.tipo_documento)
            elif incapacidad.afiliado:
                beneficiario_nombre = f"{incapacidad.afiliado.nombres} {incapacidad.afiliado.apellidos}"
                beneficiario_documento = incapacidad.afiliado.numero_documento
                tipo_documento_str = incapacidad.afiliado.tipo_documento.value if hasattr(incapacidad.afiliado.tipo_documento, 'value') else str(incapacidad.afiliado.tipo_documento)
            
            incapacidad_data = {
                "tipo": incapacidad.tipo.value if hasattr(incapacidad.tipo, 'value') else str(incapacidad.tipo),
                "beneficiario_nombre": beneficiario_nombre,
                "tipo_documento": tipo_documento_str,
                "numero_documento": beneficiario_documento,
                "fecha_inicio": incapacidad.fecha_inicio.isoformat() if incapacidad.fecha_inicio else None,
                "fecha_fin": incapacidad.fecha_fin.isoformat() if incapacidad.fecha_fin else None,
                "dias_totales": incapacidad.dias_totales,
                "diagnostico_cie10": incapacidad.diagnostico_cie10,
                "ips_nombre": incapacidad.ips_nombre if hasattr(incapacidad, 'ips_nombre') else "N/A",
                "medico_nombre": incapacidad.medico_nombre if hasattr(incapacidad, 'medico_nombre') else "N/A",
                "eps_nombre": incapacidad.eps if hasattr(incapacidad, 'eps') else "N/A"
            }
            
            send_incapacidad_radicada_email_task.delay(
                correo_solicitante=incapacidad.solicitante.correo,
                solicitante_nombre=incapacidad.solicitante.nombres + " " + incapacidad.solicitante.apellidos,
                numero_radicacion=incapacidad.numero,
                incapacidad_data=incapacidad_data
            )
            logger.info(f"[CELERY] Tarea de email programada para {incapacidad_id}")
        except Exception as email_error:
            logger.error(f"[CELERY] Error al programar email: {email_error}")
            # No fallar la radicación si falla el email
        
        return {
            "status": "success",
            "incapacidad_id": incapacidad_id,
            "estado_anterior": estado_anterior.value if hasattr(estado_anterior, 'value') else str(estado_anterior),
            "estado_nuevo": incapacidad.estado.value,
            "numero": incapacidad.numero
        }
    
    except Exception as e:
        db.rollback()
        logger.error(
            f"[CELERY] Error al radicar incapacidad {incapacidad_id}: {e}. "
            f"Intento {self.request.retries + 1}/3"
        )
        raise  # Autoretry lo manejará
    
    finally:
        db.close()


@celery_app.task(name="tasks.check_pendientes_alert")
def check_pendientes_alert() -> None:
    """
    Tarea diaria (beat). Registra en log las incapacidades atascadas en PENDIENTE
    durante más de PENDIENTE_ALERT_DAYS días sin respuesta.

    No realiza transiciones de estado; solo alerta. El auditor decide la acción.
    """
    import asyncio
    from app.core.config import settings

    asyncio.run(_check_pendientes_alert_async(settings.PENDIENTE_ALERT_DAYS))


async def _check_pendientes_alert_async(dias: int) -> None:
    """Lógica async de la alerta de PENDIENTE vencidos."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker as sa_sessionmaker
    from app.core.config import settings
    from app.db.repositories.incapacidad_repository import incapacidad_repository

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_factory = sa_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with async_session_factory() as db:
        vencidas = await incapacidad_repository.get_pendientes_vencidos(db, dias)
        count = len(vencidas)
        if count == 0:
            logger.info("[PENDIENTE-ALERT] No hay incapacidades vencidas en PENDIENTE.")
        else:
            logger.warning(
                f"[PENDIENTE-ALERT] {count} incapacidad(es) llevan >{dias} días en PENDIENTE."
            )
            for inc in vencidas:
                logger.warning(
                    f"[PENDIENTE-ALERT] {inc.numero} lleva >{dias} días sin respuesta"
                )

    await engine.dispose()


@celery_app.task(name="procesar_incapacidades_radicadas_pendientes")
def procesar_incapacidades_radicadas_pendientes_task():
    """
    Tarea programada (beat) para procesar incapacidades en estado RADICADA.
    
    Se ejecuta periódicamente para asegurar que todas las incapacidades
    se radiquen automáticamente, incluso si hubo errores temporales.
    
    Returns:
        dict: Resumen del procesamiento
    """
    logger.info("[CELERY-BEAT] Iniciando procesamiento de incapacidades RADICADAS pendientes")
    
    db: Session = get_sync_session()
    try:
        from app.models.incapacidad import Incapacidad
        
        # Buscar todas las incapacidades en estado RADICADA
        incapacidades_pendientes = db.query(Incapacidad).filter(
            Incapacidad.estado == EstadoIncapacidad.RADICADA
        ).all()
        
        count = len(incapacidades_pendientes)
        logger.info(f"[CELERY-BEAT] Encontradas {count} incapacidades RADICADAS pendientes")
        
        if count == 0:
            return {
                "status": "completed",
                "processed": 0,
                "message": "No hay incapacidades pendientes"
            }
        
        # Lanzar tarea para cada una
        processed = 0
        errors = 0
        for incapacidad in incapacidades_pendientes:
            try:
                radicar_incapacidad_automatica_task.delay(str(incapacidad.id))
                processed += 1
                logger.debug(f"[CELERY-BEAT] Programada radicación para {incapacidad.id}")
            except Exception as e:
                errors += 1
                logger.error(f"[CELERY-BEAT] Error al programar {incapacidad.id}: {e}")
        
        logger.success(
            f"[CELERY-BEAT] Procesamiento completado. "
            f"Programadas: {processed}, Errores: {errors}"
        )
        
        return {
            "status": "completed",
            "total_found": count,
            "processed": processed,
            "errors": errors
        }
    
    except Exception as e:
        logger.error(f"[CELERY-BEAT] Error en procesamiento batch: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

    finally:
        db.close()


@celery_app.task(
    name="promote_pre_incapacidad",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 60},
    retry_backoff=True,
    acks_late=True
)
def promote_pre_incapacidad_task(self, pre_incapacidad_id: str):
    """
    Tarea de Celery para promocionar pre-incapacidad a incapacidad (ASÍNCRONA).

    Args:
        pre_incapacidad_id: UUID de la pre-incapacidad (como string)

    Returns:
        dict: Resultado de la promoción

    Raises:
        Exception: Si falla después de 2 reintentos
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    logger.info(f"[CELERY] Iniciando promoción de pre-incapacidad {pre_incapacidad_id}")

    try:
        pre_inc_uuid = UUID(pre_incapacidad_id)
    except ValueError as e:
        logger.error(f"[CELERY] ID de pre-incapacidad inválido: {pre_incapacidad_id}")
        return {
            "status": "error",
            "pre_incapacidad_id": pre_incapacidad_id,
            "error": "ID inválido"
        }

    async def run_promotion():
        """Ejecutar promoción en contexto async."""
        from app.core.config import settings
        from app.services.pre_incapacidad_promotion_service import PromotePreIncapacidadService

        # Crear sesión async
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )

        async with async_session() as db:
            service = PromotePreIncapacidadService(db)
            result = await service.promote_pre_incapacidad(pre_inc_uuid)

            await engine.dispose()

            return result

    try:
        # Ejecutar async function en sync context
        result = asyncio.run(run_promotion())

        logger.success(
            f"[CELERY] Pre-incapacidad {pre_incapacidad_id} promoción completada. "
            f"Success: {result.success}, Issues: {result.validation_summary.total_issues}"
        )

        return {
            "status": "success" if result.success else "validation_failed",
            "pre_incapacidad_id": str(result.pre_incapacidad_id),
            "success": result.success,
            "total_issues": result.validation_summary.total_issues,
            "errors": result.validation_summary.errors,
            "warnings": result.validation_summary.warnings,
            "error_message": result.error_message,
        }

    except Exception as e:
        logger.error(f"[CELERY] Error promocionando pre-incapacidad {pre_incapacidad_id}: {str(e)}")
        return {
            "status": "error",
            "pre_incapacidad_id": pre_incapacidad_id,
            "error": str(e)
        }
