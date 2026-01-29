"""
Tareas de Celery para incapacidades.
"""
import asyncio
from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.tasks import celery_app
from app.db.session import AsyncSessionLocal
from app.services.incapacidad_service import incapacidad_service
from app.core.exceptions import NotFoundException, ValidationException


@celery_app.task(
    name="radicar_incapacidad_automatica",
    bind=True,
    max_retries=3,
    default_retry_delay=60  # Reintentar después de 1 minuto
)
def radicar_incapacidad_automatica_task(self, incapacidad_id: str):
    """
    Tarea de Celery para radicar una incapacidad automáticamente.
    
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
        # Convertir string a UUID
        incap_uuid = UUID(incapacidad_id)
        
        # Ejecutar función async en event loop
        result = asyncio.run(_radicar_incapacidad_async(incap_uuid))
        
        logger.success(
            f"[CELERY] Incapacidad {incapacidad_id} radicada exitosamente. "
            f"Nuevo estado: {result['estado']}"
        )
        
        return {
            "status": "success",
            "incapacidad_id": incapacidad_id,
            "estado_anterior": "RADICADA",
            "estado_nuevo": result["estado"],
            "numero": result["numero"]
        }
        
    except NotFoundException as e:
        logger.error(f"[CELERY] Incapacidad {incapacidad_id} no encontrada: {e}")
        # No reintentar si no existe
        return {
            "status": "error",
            "incapacidad_id": incapacidad_id,
            "error": "Incapacidad no encontrada"
        }
        
    except ValidationException as e:
        logger.warning(
            f"[CELERY] Error de validación al radicar {incapacidad_id}: {e}. "
            f"Puede que ya esté radicada."
        )
        # No reintentar si ya está radicada
        return {
            "status": "skipped",
            "incapacidad_id": incapacidad_id,
            "error": str(e)
        }
        
    except Exception as e:
        logger.error(
            f"[CELERY] Error al radicar incapacidad {incapacidad_id}: {e}. "
            f"Intento {self.request.retries + 1}/3"
        )
        
        # Reintentar automáticamente
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.critical(
                f"[CELERY] FALLO CRÍTICO: Incapacidad {incapacidad_id} "
                f"no pudo ser radicada después de 3 intentos"
            )
            # Aquí podrías enviar una alerta al equipo
            return {
                "status": "failed",
                "incapacidad_id": incapacidad_id,
                "error": str(e),
                "retries": 3
            }


async def _radicar_incapacidad_async(incapacidad_id: UUID) -> dict:
    """
    Función async helper para radicar incapacidad.
    
    Args:
        incapacidad_id: UUID de la incapacidad
        
    Returns:
        dict: Datos de la incapacidad radicada
    """
    # Crear sesión de BD async
    async with AsyncSessionLocal() as db:
        try:
            # Llamar al servicio para radicar
            incapacidad = await incapacidad_service.radicar_incapacidad(
                db=db,
                incapacidad_id=incapacidad_id,
                usuario_id=None  # Sistema automático
            )
            
            # Confirmar transacción
            await db.commit()
            
            return {
                "id": str(incapacidad.id),
                "numero": incapacidad.numero,
                "estado": incapacidad.estado.value,
                "tipo": incapacidad.tipo.value
            }
            
        except Exception as e:
            # Rollback en caso de error
            await db.rollback()
            raise e


@celery_app.task(name="procesar_incapacidades_radicadas_pendientes")
def procesar_incapacidades_radicadas_pendientes_task(
    dias_antiguedad: int = 1
):
    """
    Tarea programada (Celery Beat) para radicar incapacidades antiguas.
    
    Encuentra incapacidades en estado RADICADA con más de X días
    y las envía a radicar automáticamente.
    
    Args:
        dias_antiguedad: Días mínimos en estado RADICADA
        
    Returns:
        dict: Resumen de procesamiento
    """
    logger.info(
        f"[CELERY BEAT] Buscando incapacidades RADICADAS con más de {dias_antiguedad} días"
    )
    
    try:
        result = asyncio.run(
            _procesar_incapacidades_pendientes_async(dias_antiguedad)
        )
        
        logger.info(
            f"[CELERY BEAT] Procesamiento completado: "
            f"{result['procesadas']} incapacidades enviadas a radicar"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"[CELERY BEAT] Error al procesar incapacidades pendientes: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


async def _procesar_incapacidades_pendientes_async(dias_antiguedad: int) -> dict:
    """
    Busca y radica incapacidades antiguas.
    
    Args:
        dias_antiguedad: Días mínimos
        
    Returns:
        dict: Resumen
    """
    from datetime import datetime, timedelta
    from app.utils.enums import EstadoIncapacidad
    from sqlalchemy import select, and_
    from app.models.incapacidad import Incapacidad
    
    async with AsyncSessionLocal() as db:
        fecha_limite = datetime.utcnow() - timedelta(days=dias_antiguedad)
        
        # Buscar incapacidades RADICADAS antiguas
        stmt = select(Incapacidad).where(
            and_(
                Incapacidad.estado == EstadoIncapacidad.RADICADA,
                Incapacidad.created_at <= fecha_limite
            )
        ).limit(100)  # Por seguridad, procesar máximo 100 a la vez
        
        result = await db.execute(stmt)
        incapacidades = result.scalars().all()
        
        # Enviar cada una a radicar
        count = 0
        for incap in incapacidades:
            radicar_incapacidad_automatica_task.delay(str(incap.id))
            count += 1
        
        return {
            "status": "success",
            "procesadas": count,
            "fecha_limite": fecha_limite.isoformat()
        }