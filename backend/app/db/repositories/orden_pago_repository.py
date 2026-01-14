"""
Repository para operaciones de base de datos de OrdenPago.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base_repository import BaseRepository
from app.models.orden_pago import OrdenPago
from app.models.incapacidad import Incapacidad
from app.utils.enums import EstadoOrdenPago


class OrdenPagoRepository(BaseRepository[OrdenPago]):
    """Repository para OrdenPago con operaciones específicas."""

    def __init__(self):
        """Inicializa el repository con el modelo OrdenPago."""
        super().__init__(OrdenPago)

    async def get_by_numero_orden(
        self,
        db: AsyncSession,
        numero_orden: str
    ) -> Optional[OrdenPago]:
        """
        Obtiene una orden de pago por su número único.
        
        Args:
            db: Sesión de base de datos
            numero_orden: Número de la orden
            
        Returns:
            OrdenPago si existe, None si no
        """
        query = select(OrdenPago).where(OrdenPago.numero_orden == numero_orden)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_incapacidad_id(
        self,
        db: AsyncSession,
        incapacidad_id: UUID
    ) -> List[OrdenPago]:
        """
        Obtiene todas las órdenes de pago de una incapacidad.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            
        Returns:
            Lista de órdenes de pago
        """
        query = select(OrdenPago).where(
            OrdenPago.incapacidad_id == incapacidad_id
        ).order_by(OrdenPago.fecha_generacion.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def list_by_estado(
        self,
        db: AsyncSession,
        estado: EstadoOrdenPago,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrdenPago]:
        """
        Obtiene órdenes de pago por estado.
        
        Args:
            db: Sesión de base de datos
            estado: Estado de la orden
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de órdenes en el estado especificado
        """
        query = select(OrdenPago).where(
            OrdenPago.estado_pago == estado
        ).order_by(
            OrdenPago.fecha_generacion.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def list_by_empresa(
        self,
        db: AsyncSession,
        empresa_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrdenPago]:
        """
        Obtiene órdenes de pago de una empresa.
        
        Args:
            db: Sesión de base de datos
            empresa_id: ID de la empresa
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de órdenes de la empresa
        """
        query = select(OrdenPago).join(
            Incapacidad, OrdenPago.incapacidad_id == Incapacidad.id
        ).where(
            Incapacidad.empresa_id == empresa_id
        ).order_by(
            OrdenPago.fecha_generacion.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def list_pending_payment(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrdenPago]:
        """
        Obtiene órdenes pendientes de pago (APROBADA).
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de órdenes pendientes de pago
        """
        query = select(OrdenPago).where(
            OrdenPago.estado_pago == EstadoOrdenPago.APROBADA
        ).order_by(
            OrdenPago.fecha_generacion.asc()  # Más antiguas primero
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_with_incapacidad(
        self,
        db: AsyncSession,
        orden_pago_id: UUID
    ) -> Optional[OrdenPago]:
        """
        Obtiene una orden de pago con su incapacidad cargada.
        
        Args:
            db: Sesión de base de datos
            orden_pago_id: ID de la orden
            
        Returns:
            OrdenPago con incapacidad, o None si no existe
        """
        query = select(OrdenPago).options(
            selectinload(OrdenPago.incapacidad)
        ).where(OrdenPago.id == orden_pago_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_last_numero_orden(
        self,
        db: AsyncSession,
        year: int
    ) -> Optional[str]:
        """
        Obtiene el último número de orden del año especificado.
        
        Args:
            db: Sesión de base de datos
            year: Año para filtrar
            
        Returns:
            Último número de orden del año, o None si no hay
        """
        # Patrón: OP-2026-00001
        pattern = f"OP-{year}-%"
        
        query = select(OrdenPago.numero_orden).where(
            OrdenPago.numero_orden.like(pattern)
        ).order_by(OrdenPago.numero_orden.desc()).limit(1)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def exists_for_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        exclude_estados: Optional[List[EstadoOrdenPago]] = None
    ) -> bool:
        """
        Verifica si existe una orden de pago para una incapacidad.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            exclude_estados: Estados a excluir de la búsqueda (ej: ANULADA, RECHAZADA)
            
        Returns:
            True si existe al menos una orden, False si no
        """
        conditions = [OrdenPago.incapacidad_id == incapacidad_id]
        
        if exclude_estados:
            conditions.append(OrdenPago.estado_pago.not_in(exclude_estados))
        
        query = select(func.count(OrdenPago.id)).where(and_(*conditions))
        result = await db.execute(query)
        count = result.scalar_one()
        
        return count > 0

    async def list_by_fecha_range(
        self,
        db: AsyncSession,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrdenPago]:
        """
        Obtiene órdenes de pago en un rango de fechas.
        
        Args:
            db: Sesión de base de datos
            fecha_inicio: Fecha inicial
            fecha_fin: Fecha final
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de órdenes en el rango de fechas
        """
        query = select(OrdenPago).where(
            and_(
                OrdenPago.fecha_generacion >= fecha_inicio,
                OrdenPago.fecha_generacion <= fecha_fin
            )
        ).order_by(
            OrdenPago.fecha_generacion.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
