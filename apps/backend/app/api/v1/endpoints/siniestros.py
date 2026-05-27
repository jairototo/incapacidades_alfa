"""
API endpoints para gestión de Siniestros.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.db.session import get_db
from apps.backend.app.schemas.siniestro import (
    SiniestroCreate,
    SiniestroUpdate,
    SiniestroInDB,
)
from apps.backend.app.schemas.incapacidad import IncapacidadInDB
from apps.backend.app.schemas.historial_estado import HistorialEstadoResponse
from apps.backend.app.services.siniestro_service import siniestro_service
from apps.backend.app.services.historial_estado_service import historial_estado_service
from apps.backend.app.utils.enums import TipoSiniestro, EstadoSiniestro

router = APIRouter()


@router.post(
    "/",
    response_model=SiniestroInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Crear siniestro",
    description="Crea un nuevo siniestro laboral con validaciones de negocio"
)
async def create_siniestro(
    siniestro_data: SiniestroCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuevo siniestro.
    
    Validaciones:
    - El empleado debe estar ACTIVO
    - La empresa debe estar ACTIVA
    - El empleado debe pertenecer a la empresa
    - La fecha del siniestro no puede ser futura
    - Genera número único automáticamente (SIN-YYYYMMDD-NNNN)
    - Estado inicial: REPORTADO
    """
    return await siniestro_service.create_siniestro(db, siniestro_data)


@router.get(
    "/",
    response_model=List[SiniestroInDB],
    summary="Listar siniestros",
    description="Lista siniestros con filtros opcionales"
)
async def list_siniestros(
    tipo: Optional[TipoSiniestro] = Query(None, description="Filtrar por tipo"),
    estado: Optional[EstadoSiniestro] = Query(None, description="Filtrar por estado"),
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    empleado_id: Optional[UUID] = Query(None, description="Filtrar por empleado"),
    fecha_desde: Optional[date] = Query(None, description="Fecha mínima del siniestro"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha máxima del siniestro"),
    numero: Optional[str] = Query(None, description="Búsqueda parcial en número"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista siniestros con filtros opcionales.
    
    Filtros disponibles:
    - tipo: ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, ACCIDENTE_TRAYECTO
    - estado: REPORTADO, EN_INVESTIGACION, CERRADO, ANULADO
    - empresa_id: UUID de la empresa
    - empleado_id: UUID del empleado
    - fecha_desde/hasta: Rango de fechas del siniestro
    - numero: Búsqueda parcial en número de siniestro
    
    Ordenamiento: Por fecha de siniestro descendente
    """
    return await siniestro_service.list_siniestros(
        db,
        tipo=tipo,
        estado=estado,
        empresa_id=empresa_id,
        empleado_id=empleado_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        numero=numero,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{id}",
    response_model=SiniestroInDB,
    summary="Obtener siniestro",
    description="Obtiene un siniestro específico por ID"
)
async def get_siniestro(
    id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un siniestro por su ID.
    
    Returns:
        Siniestro con todos sus datos
        
    Raises:
        404: Si el siniestro no existe
    """
    return await siniestro_service.get_siniestro(db, id)


@router.put(
    "/{id}",
    response_model=SiniestroInDB,
    summary="Actualizar siniestro",
    description="Actualiza un siniestro existente"
)
async def update_siniestro(
    id: UUID,
    siniestro_data: SiniestroUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un siniestro existente.
    
    Restricciones:
    - No se pueden modificar siniestros CERRADOS o ANULADOS
    - No se puede cambiar empleado o empresa
    - Solo se pueden actualizar campos específicos
    
    Returns:
        Siniestro actualizado
        
    Raises:
        404: Si el siniestro no existe
        400: Si la operación no es permitida
    """
    return await siniestro_service.update_siniestro(db, id, siniestro_data)


@router.post(
    "/{id}/reportar",
    response_model=SiniestroInDB,
    summary="Reportar siniestro",
    description="Cambia el estado del siniestro a EN_INVESTIGACION"
)
async def reportar_siniestro(
    id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Reporta un siniestro, cambiando su estado a EN_INVESTIGACION.
    
    Transición: REPORTADO → EN_INVESTIGACION
    
    Este paso marca el inicio de la investigación formal del siniestro.
    
    Returns:
        Siniestro con estado actualizado
        
    Raises:
        404: Si el siniestro no existe
        400: Si la transición de estado no es válida
    """
    return await siniestro_service.reportar_siniestro(db, id)


@router.post(
    "/{id}/cerrar",
    response_model=SiniestroInDB,
    summary="Cerrar siniestro",
    description="Cierra el siniestro (estado final)"
)
async def cerrar_siniestro(
    id: UUID,
    observaciones: Optional[str] = Body(None, description="Observaciones de cierre"),
    db: AsyncSession = Depends(get_db)
):
    """
    Cierra un siniestro (estado final).
    
    Transición: EN_INVESTIGACION → CERRADO
    
    El cierre indica que el siniestro ha sido completamente procesado
    y no requiere más acciones. Este es un estado final.
    
    Args:
        observaciones: Observaciones finales del cierre (opcional)
    
    Returns:
        Siniestro con estado CERRADO
        
    Raises:
        404: Si el siniestro no existe
        400: Si la transición de estado no es válida
    """
    return await siniestro_service.cerrar_siniestro(db, id, observaciones)


@router.post(
    "/{id}/anular",
    response_model=SiniestroInDB,
    summary="Anular siniestro",
    description="Anula el siniestro (estado final)"
)
async def anular_siniestro(
    id: UUID,
    motivo: str = Body(..., min_length=10, description="Motivo de la anulación"),
    db: AsyncSession = Depends(get_db)
):
    """
    Anula un siniestro (estado final).
    
    Transiciones válidas:
    - REPORTADO → ANULADO
    - EN_INVESTIGACION → ANULADO
    
    La anulación se usa cuando el siniestro fue reportado por error
    o cuando se determina que no procede. Este es un estado final.
    
    Args:
        motivo: Motivo de la anulación (mínimo 10 caracteres, requerido)
    
    Returns:
        Siniestro con estado ANULADO
        
    Raises:
        404: Si el siniestro no existe
        400: Si no se proporciona motivo válido o la transición no es permitida
    """
    return await siniestro_service.anular_siniestro(db, id, motivo)


@router.get(
    "/{id}/incapacidades",
    response_model=List[IncapacidadInDB],
    summary="Incapacidades del siniestro",
    description="Obtiene todas las incapacidades asociadas al siniestro"
)
async def get_incapacidades_siniestro(
    id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene todas las incapacidades asociadas a un siniestro.
    
    Un siniestro puede tener múltiples incapacidades relacionadas
    a lo largo del proceso de recuperación del empleado.
    
    Returns:
        Lista de incapacidades del siniestro
        
    Raises:
        404: Si el siniestro no existe
    """
    return await siniestro_service.get_incapacidades_siniestro(db, id)


@router.get(
    "/{id}/historial",
    response_model=List[HistorialEstadoResponse],
    summary="Obtener historial de estados",
    description="Lista todos los cambios de estado de un siniestro"
)
async def get_historial(
    id: UUID,
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el historial completo de cambios de estado de un siniestro.
    
    Retorna una lista ordenada cronológicamente (más reciente primero) con:
    - Estado anterior y nuevo
    - Fecha del cambio
    - Usuario que realizó el cambio
    - Observaciones
    
    Útil para seguimiento de la investigación y auditoría del siniestro.
    
    Returns:
        Lista de cambios de estado del siniestro
        
    Raises:
        404: Si el siniestro no existe
    """
    # Validar que el siniestro existe
    siniestro = await siniestro_service.get_siniestro(db, id)
    if not siniestro:
        from apps.backend.app.core.exceptions import NotFoundException
        raise NotFoundException(f"Siniestro con ID {id} no encontrado")
    
    # Obtener historial
    items = await historial_estado_service.get_siniestro_history(
        db=db,
        siniestro_id=id,
        skip=skip,
        limit=limit
    )
    
    return [HistorialEstadoResponse.model_validate(item) for item in items]
