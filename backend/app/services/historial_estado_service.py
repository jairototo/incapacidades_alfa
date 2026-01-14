"""
Service para gestión de historial de cambios de estado.

Proporciona lógica de negocio para crear y consultar
el historial de cambios de estado de cualquier entidad.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.historial_estado_repository import historial_estado_repository
from app.schemas.historial_estado import HistorialEstadoCreate
from app.models.historial_estado import HistorialEstado


class HistorialEstadoService:
    """Service para HistorialEstado con operaciones polimórficas."""

    def __init__(self):
        """Inicializar service con repository."""
        self.repository = historial_estado_repository

    async def create_historial_entry(
        self,
        db: AsyncSession,
        *,
        entity_type: str,
        entity_id: UUID,
        estado_anterior: Optional[str],
        estado_nuevo: str,
        observacion: Optional[str] = None,
        cambiado_por_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> HistorialEstado:
        """
        Crear un registro de historial de cambio de estado.
        
        Args:
            db: Sesión de base de datos
            entity_type: Tipo de entidad ('incapacidad', 'siniestro', etc.)
            entity_id: ID de la entidad
            estado_anterior: Estado previo (None si es el primer estado)
            estado_nuevo: Nuevo estado
            observacion: Observaciones opcionales
            cambiado_por_id: ID del usuario que realizó el cambio
            metadata: Metadata adicional (JSON)
            
        Returns:
            Registro de historial creado
        """
        historial_data = HistorialEstadoCreate(
            entity_type=entity_type,
            entity_id=entity_id,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            observacion=observacion,
            cambiado_por_id=cambiado_por_id,
            metadata=metadata
        )
        
        return await self.repository.create(db, obj_in=historial_data.model_dump())

    async def get_entity_history(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[HistorialEstado]:
        """
        Obtener el historial completo de una entidad.
        
        Args:
            db: Sesión de base de datos
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de cambios de estado ordenados por fecha (más reciente primero)
        """
        return await self.repository.get_by_entity(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id,
            skip=skip,
            limit=limit
        )

    async def get_incapacidad_history(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[HistorialEstado]:
        """
        Obtener historial de una incapacidad.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de cambios de estado de la incapacidad
        """
        return await self.repository.get_by_incapacidad(
            db=db,
            incapacidad_id=incapacidad_id,
            skip=skip,
            limit=limit
        )

    async def get_siniestro_history(
        self,
        db: AsyncSession,
        siniestro_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[HistorialEstado]:
        """
        Obtener historial de un siniestro.
        
        Args:
            db: Sesión de base de datos
            siniestro_id: ID del siniestro
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de cambios de estado del siniestro
        """
        return await self.repository.get_by_siniestro(
            db=db,
            siniestro_id=siniestro_id,
            skip=skip,
            limit=limit
        )

    async def get_recent_changes(
        self,
        db: AsyncSession,
        limit: int = 50,
        entity_type: Optional[str] = None
    ) -> List[HistorialEstado]:
        """
        Obtener cambios recientes de estado.
        
        Args:
            db: Sesión de base de datos
            limit: Máximo de registros
            entity_type: Filtrar por tipo de entidad (opcional)
            
        Returns:
            Lista de cambios recientes
        """
        return await self.repository.get_recent(
            db=db,
            limit=limit,
            entity_type=entity_type
        )

    async def search_historial(
        self,
        db: AsyncSession,
        *,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        estado_nuevo: Optional[str] = None,
        cambiado_por_id: Optional[UUID] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[HistorialEstado]:
        """
        Buscar registros de historial con múltiples filtros.
        
        Args:
            db: Sesión de base de datos
            entity_type: Filtrar por tipo de entidad
            entity_id: Filtrar por ID de entidad
            estado_nuevo: Filtrar por estado al que cambió
            cambiado_por_id: Filtrar por usuario que realizó el cambio
            fecha_desde: Fecha mínima del cambio
            fecha_hasta: Fecha máxima del cambio
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de registros que cumplen los criterios
        """
        return await self.repository.search(
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

    async def count_entity_changes(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID
    ) -> int:
        """
        Contar cambios de estado de una entidad.
        
        Args:
            db: Sesión de base de datos
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            
        Returns:
            Número total de cambios de estado
        """
        return await self.repository.count_by_entity(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id
        )

    async def get_first_state(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID
    ) -> Optional[HistorialEstado]:
        """
        Obtener el primer estado registrado de una entidad.
        
        Args:
            db: Sesión de base de datos
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            
        Returns:
            Primer registro de historial o None
        """
        return await self.repository.get_first_change(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id
        )

    async def get_current_state(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID
    ) -> Optional[HistorialEstado]:
        """
        Obtener el estado actual (último cambio) de una entidad.
        
        Args:
            db: Sesión de base de datos
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            
        Returns:
            Último registro de historial o None
        """
        return await self.repository.get_last_change(
            db=db,
            entity_type=entity_type,
            entity_id=entity_id
        )


# Instancia global del service
historial_estado_service = HistorialEstadoService()
