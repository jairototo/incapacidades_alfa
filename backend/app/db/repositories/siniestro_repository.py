"""
Repository para operaciones de base de datos de Siniestros.
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.siniestro import Siniestro
from app.utils.enums import TipoSiniestro, EstadoSiniestro


class SiniestroRepository(BaseRepository[Siniestro]):
    """Repository para Siniestro con métodos específicos de búsqueda."""
    
    def __init__(self):
        super().__init__(Siniestro)
    
    async def get_by_numero(
        self,
        db: AsyncSession,
        numero: str
    ) -> Optional[Siniestro]:
        """
        Obtener siniestro por número único.
        
        Args:
            db: Sesión de base de datos
            numero: Número del siniestro (ej: SIN-20260108-0001)
            
        Returns:
            Siniestro encontrado o None
        """
        query = select(Siniestro).where(Siniestro.numero_siniestro == numero)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_empresa(
        self,
        db: AsyncSession,
        empresa_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Siniestro]:
        """
        Obtener todos los siniestros de una empresa.
        
        Args:
            db: Sesión de base de datos
            empresa_id: ID de la empresa
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de siniestros de la empresa
        """
        query = select(Siniestro).where(
            Siniestro.empresa_id == empresa_id
        ).order_by(
            Siniestro.fecha_siniestro.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_empleado(
        self,
        db: AsyncSession,
        empleado_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Siniestro]:
        """
        Obtener todos los siniestros de un empleado.
        
        Args:
            db: Sesión de base de datos
            empleado_id: ID del empleado
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de siniestros del empleado
        """
        query = select(Siniestro).where(
            Siniestro.empleado_id == empleado_id
        ).order_by(
            Siniestro.fecha_siniestro.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_estado(
        self,
        db: AsyncSession,
        estado: EstadoSiniestro,
        skip: int = 0,
        limit: int = 100
    ) -> List[Siniestro]:
        """
        Obtener siniestros por estado.
        
        Args:
            db: Sesión de base de datos
            estado: Estado del siniestro
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de siniestros en el estado especificado
        """
        query = select(Siniestro).where(
            Siniestro.estado == estado
        ).order_by(
            Siniestro.fecha_siniestro.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def search(
        self,
        db: AsyncSession,
        tipo: Optional[TipoSiniestro] = None,
        estado: Optional[EstadoSiniestro] = None,
        empresa_id: Optional[UUID] = None,
        empleado_id: Optional[UUID] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        numero: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Siniestro]:
        """
        Búsqueda avanzada de siniestros con múltiples filtros.
        
        Args:
            db: Sesión de base de datos
            tipo: Filtrar por tipo de siniestro
            estado: Filtrar por estado
            empresa_id: Filtrar por empresa
            empleado_id: Filtrar por empleado
            fecha_desde: Fecha mínima del siniestro
            fecha_hasta: Fecha máxima del siniestro
            numero: Búsqueda parcial en número
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de siniestros que cumplen los criterios
        """
        query = select(Siniestro)
        
        # Aplicar filtros
        if tipo:
            query = query.where(Siniestro.tipo_siniestro == tipo)
        
        if estado:
            query = query.where(Siniestro.estado == estado)
        
        if empresa_id:
            query = query.where(Siniestro.empresa_id == empresa_id)
        
        if empleado_id:
            query = query.where(Siniestro.empleado_id == empleado_id)
        
        if fecha_desde:
            query = query.where(Siniestro.fecha_siniestro >= fecha_desde)
        
        if fecha_hasta:
            query = query.where(Siniestro.fecha_siniestro <= fecha_hasta)
        
        if numero:
            query = query.where(Siniestro.numero_siniestro.ilike(f"%{numero}%"))
        
        # Ordenar por fecha de siniestro descendente
        query = query.order_by(Siniestro.fecha_siniestro.desc())
        
        # Paginación
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_en_investigacion(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Siniestro]:
        """
        Obtener siniestros en investigación ordenados por fecha.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de siniestros en investigación
        """
        query = select(Siniestro).where(
            Siniestro.estado == EstadoSiniestro.EN_INVESTIGACION
        ).order_by(
            Siniestro.fecha_siniestro.asc()  # Los más antiguos primero
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_external_id(
        self,
        db: AsyncSession,
        external_id: str
    ) -> Optional[Siniestro]:
        """
        Obtener siniestro por ID externo (sincronización).
        
        Args:
            db: Sesión de base de datos
            external_id: ID del siniestro en sistema externo
            
        Returns:
            Siniestro encontrado o None
        """
        query = select(Siniestro).where(Siniestro.external_id == external_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Singleton instance
siniestro_repository = SiniestroRepository()
