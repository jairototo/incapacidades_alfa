"""
Repositorio para operaciones de base de datos con Empresa.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.db.repositories.base_repository import BaseRepository
from apps.backend.app.models.empresa import Empresa


class EmpresaRepository(BaseRepository[Empresa]):
    """
    Repositorio para gestionar empresas en la base de datos.
    
    Hereda operaciones CRUD básicas de BaseRepository y añade
    métodos específicos para búsquedas de empresas.
    """
    
    def __init__(self):
        """Inicializar repositorio de empresas."""
        super().__init__(Empresa)
    
    async def get_by_nit(
        self,
        db: AsyncSession,
        nit: str
    ) -> Optional[Empresa]:
        """
        Obtener empresa por NIT.
        
        Args:
            db: Sesión de base de datos
            nit: NIT de la empresa a buscar
            
        Returns:
            Empresa encontrada o None
        """
        result = await db.execute(
            select(Empresa).where(Empresa.nit == nit)
        )
        return result.scalar_one_or_none()
    
    async def get_by_razon_social(
        self,
        db: AsyncSession,
        razon_social: str
    ) -> Optional[Empresa]:
        """
        Obtener empresa por razón social exacta.
        
        Args:
            db: Sesión de base de datos
            razon_social: Razón social a buscar
            
        Returns:
            Empresa encontrada o None
        """
        result = await db.execute(
            select(Empresa).where(Empresa.razon_social == razon_social)
        )
        return result.scalar_one_or_none()
    
    async def search(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        nit: Optional[str] = None,
        tipo_empresa: Optional[str] = None,
        estado: Optional[str] = None,
        ciudad: Optional[str] = None,
        departamento: Optional[str] = None,
        search_text: Optional[str] = None
    ) -> List[Empresa]:
        """
        Buscar empresas con múltiples filtros.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            nit: Filtrar por NIT (parcial)
            tipo_empresa: Filtrar por tipo de empresa
            estado: Filtrar por estado
            ciudad: Filtrar por ciudad
            departamento: Filtrar por departamento
            search_text: Búsqueda en NIT o razón social
            
        Returns:
            Lista de empresas que cumplen los filtros
        """
        query = select(Empresa)
        
        # Filtro por NIT (puede ser parcial)
        if nit:
            query = query.where(Empresa.nit.ilike(f"%{nit}%"))
        
        # Filtros exactos
        if tipo_empresa:
            query = query.where(Empresa.tipo_empresa == tipo_empresa)
        
        if estado:
            query = query.where(Empresa.estado == estado)
        
        if ciudad:
            query = query.where(Empresa.ciudad.ilike(f"%{ciudad}%"))
        
        if departamento:
            query = query.where(Empresa.departamento.ilike(f"%{departamento}%"))
        
        # Búsqueda por texto en NIT o razón social
        if search_text:
            search_pattern = f"%{search_text}%"
            query = query.where(
                or_(
                    Empresa.nit.ilike(search_pattern),
                    Empresa.razon_social.ilike(search_pattern)
                )
            )
        
        # Ordenar por razón social
        query = query.order_by(Empresa.razon_social)
        
        # Aplicar paginación
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_activas(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Empresa]:
        """
        Obtener empresas activas.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de empresas activas
        """
        query = (
            select(Empresa)
            .where(Empresa.estado == "ACTIVA")
            .order_by(Empresa.razon_social)
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_external_id(
        self,
        db: AsyncSession,
        sync_source: str,
        external_id: str
    ) -> Optional[Empresa]:
        """
        Obtener empresa por ID externo (para sincronización).
        
        Args:
            db: Sesión de base de datos
            sync_source: Fuente de sincronización
            external_id: ID en el sistema externo
            
        Returns:
            Empresa encontrada o None
        """
        result = await db.execute(
            select(Empresa).where(
                Empresa.sync_source == sync_source,
                Empresa.external_id == external_id
            )
        )
        return result.scalar_one_or_none()


# Instancia singleton del repositorio
empresa_repository = EmpresaRepository()
