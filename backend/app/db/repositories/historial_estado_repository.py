"""
Repository para gestionar operaciones de HistorialEstado.

Proporciona acceso a datos de historial de cambios de estado
para cualquier tipo de entidad (polimórfico).
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.historial_estado import HistorialEstado


class HistorialEstadoRepository(BaseRepository[HistorialEstado]):
    """Repository para HistorialEstado con soporte polimórfico."""

    async def get_by_entity(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[HistorialEstado]:
        """
        Obtener historial de cambios para una entidad específica.
        
        Args:
            db: Sesión de base de datos
            entity_type: Tipo de entidad ('incapacidad', 'siniestro', etc.)
            entity_id: ID de la entidad
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de registros de historial ordenados por fecha (más reciente primero)
        """
        stmt = (
            select(HistorialEstado)
            .where(
                and_(
                    HistorialEstado.entity_type == entity_type,
                    HistorialEstado.entity_id == entity_id
                )
            )
            .order_by(desc(HistorialEstado.fecha_cambio))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[HistorialEstado]:
        """
        Shortcut para obtener historial de una incapacidad.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de registros de historial de la incapacidad
        """
        return await self.get_by_entity(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            skip=skip,
            limit=limit
        )

    async def get_by_siniestro(
        self,
        db: AsyncSession,
        siniestro_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[HistorialEstado]:
        """
        Shortcut para obtener historial de un siniestro.
        
        Args:
            db: Sesión de base de datos
            siniestro_id: ID del siniestro
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de registros de historial del siniestro
        """
        return await self.get_by_entity(
            db=db,
            entity_type="siniestro",
            entity_id=siniestro_id,
            skip=skip,
            limit=limit
        )

    async def get_recent(
        self,
        db: AsyncSession,
        limit: int = 50,
        entity_type: Optional[str] = None
    ) -> List[HistorialEstado]:
        """
        Obtener cambios recientes de estado, opcionalmente filtrados por tipo.
        
        Args:
            db: Sesión de base de datos
            limit: Máximo de registros a retornar
            entity_type: Tipo de entidad opcional para filtrar
            
        Returns:
            Lista de cambios de estado ordenados por fecha (más reciente primero)
        """
        stmt = select(HistorialEstado)
        
        if entity_type:
            stmt = stmt.where(HistorialEstado.entity_type == entity_type)
        
        stmt = stmt.order_by(desc(HistorialEstado.fecha_cambio)).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def search(
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
        Búsqueda de registros de historial con múltiples filtros.
        
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
        conditions = []
        
        if entity_type:
            conditions.append(HistorialEstado.entity_type == entity_type)
        
        if entity_id:
            conditions.append(HistorialEstado.entity_id == entity_id)
        
        if estado_nuevo:
            conditions.append(HistorialEstado.estado_nuevo == estado_nuevo)
        
        if cambiado_por_id:
            conditions.append(HistorialEstado.cambiado_por_id == cambiado_por_id)
        
        if fecha_desde:
            conditions.append(HistorialEstado.fecha_cambio >= fecha_desde)
        
        if fecha_hasta:
            conditions.append(HistorialEstado.fecha_cambio <= fecha_hasta)
        
        stmt = select(HistorialEstado)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = (
            stmt
            .order_by(desc(HistorialEstado.fecha_cambio))
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_entity(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID
    ) -> int:
        """
        Contar cambios de estado para una entidad.
        
        Args:
            db: Sesión de base de datos
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            
        Returns:
            Número total de cambios de estado
        """
        stmt = (
            select(HistorialEstado)
            .where(
                and_(
                    HistorialEstado.entity_type == entity_type,
                    HistorialEstado.entity_id == entity_id
                )
            )
        )
        result = await db.execute(stmt)
        return len(result.scalars().all())

    async def get_first_change(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID
    ) -> Optional[HistorialEstado]:
        """
        Obtener el primer cambio de estado de una entidad.
        
        Args:
            db: Sesión de base de datos
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            
        Returns:
            Primer registro de historial o None si no existe
        """
        stmt = (
            select(HistorialEstado)
            .where(
                and_(
                    HistorialEstado.entity_type == entity_type,
                    HistorialEstado.entity_id == entity_id
                )
            )
            .order_by(HistorialEstado.fecha_cambio.asc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_last_change(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID
    ) -> Optional[HistorialEstado]:
        """
        Obtener el último cambio de estado de una entidad.
        
        Args:
            db: Sesión de base de datos
            entity_type: Tipo de entidad
            entity_id: ID de la entidad
            
        Returns:
            Último registro de historial o None si no existe
        """
        stmt = (
            select(HistorialEstado)
            .where(
                and_(
                    HistorialEstado.entity_type == entity_type,
                    HistorialEstado.entity_id == entity_id
                )
            )
            .order_by(desc(HistorialEstado.fecha_cambio))
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# Instancia global del repository
historial_estado_repository = HistorialEstadoRepository(HistorialEstado)
