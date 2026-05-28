"""
Endpoints para consultar historial de cambios de estado.

Proporciona endpoints REST para obtener el historial
de cambios de estado de cualquier entidad.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.historial_estado import (
    HistorialEstadoResponse,
    HistorialEstadoListResponse
)
from app.services.historial_estado_service import historial_estado_service

router = APIRouter()


@router.get("/", response_model=HistorialEstadoListResponse)
async def list_historial(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo de entidad"),
    entity_id: Optional[UUID] = Query(None, description="Filtrar por ID de entidad"),
    estado_nuevo: Optional[str] = Query(None, description="Filtrar por estado al que cambió"),
    cambiado_por_id: Optional[UUID] = Query(None, description="Filtrar por usuario que hizo el cambio"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha mínima del cambio"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha máxima del cambio"),
    db: AsyncSession = Depends(get_db)
):
    """
    Listar registros de historial con filtros opcionales.
    
    Permite filtrar por:
    - Tipo de entidad (incapacidad, siniestro, etc.)
    - ID de entidad específica
    - Estado al que cambió
    - Usuario que realizó el cambio
    - Rango de fechas
    """
    items = await historial_estado_service.search_historial(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        estado_nuevo=estado_nuevo,
        cambiado_por_id=cambiado_por_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        skip=skip,
        limit=limit
    )
    
    # Contar total si hay filtros específicos
    total = len(items)
    if entity_type and entity_id:
        total = await historial_estado_service.count_entity_changes(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id
        )
    
    return HistorialEstadoListResponse(
        items=[HistorialEstadoResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
        entity_type=entity_type,
        entity_id=entity_id
    )


@router.get("/recent", response_model=List[HistorialEstadoResponse])
async def get_recent_changes(
    limit: int = Query(50, ge=1, le=200, description="Número de cambios recientes"),
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo de entidad"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener cambios de estado más recientes.
    
    Útil para dashboards y monitoreo en tiempo real.
    """
    items = await historial_estado_service.get_recent_changes(
        db=db,
        limit=limit,
        entity_type=entity_type
    )
    
    return [HistorialEstadoResponse.model_validate(item) for item in items]


@router.get("/{entity_type}/{entity_id}", response_model=List[HistorialEstadoResponse])
async def get_entity_history(
    entity_type: str,
    entity_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener historial completo de una entidad específica.
    
    Args:
        entity_type: Tipo de entidad (incapacidad, siniestro, etc.)
        entity_id: ID de la entidad
    
    Returns:
        Lista de cambios de estado ordenados por fecha (más reciente primero)
    """
    items = await historial_estado_service.get_entity_history(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        skip=skip,
        limit=limit
    )
    
    # Convertir los objetos SQLAlchemy a dicts para evitar problemas con metadata
    return [HistorialEstadoResponse.model_validate(item, from_attributes=True) for item in items]


@router.get("/{entity_type}/{entity_id}/first", response_model=Optional[HistorialEstadoResponse])
async def get_first_state(
    entity_type: str,
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener el primer estado registrado de una entidad.
    
    Útil para determinar cuándo y cómo se creó la entidad.
    """
    item = await historial_estado_service.get_first_state(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id
    )
    
    return HistorialEstadoResponse.model_validate(item) if item else None


@router.get("/{entity_type}/{entity_id}/current", response_model=Optional[HistorialEstadoResponse])
async def get_current_state(
    entity_type: str,
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener el estado actual (último cambio) de una entidad.
    
    Útil para verificar el estado más reciente sin cargar todo el historial.
    """
    item = await historial_estado_service.get_current_state(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id
    )
    
    return HistorialEstadoResponse.model_validate(item) if item else None


@router.get("/{entity_type}/{entity_id}/count", response_model=dict)
async def count_entity_changes(
    entity_type: str,
    entity_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Contar cuántos cambios de estado ha tenido una entidad.
    
    Útil para métricas y análisis.
    """
    count = await historial_estado_service.count_entity_changes(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id
    )
    
    return {
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "count": count
    }
