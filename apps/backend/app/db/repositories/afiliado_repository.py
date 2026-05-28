"""
Repositorio para operaciones de base de datos con Afiliado.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.afiliado import Afiliado


class AfiliadoRepository(BaseRepository[Afiliado]):
    """
    Repositorio para gestionar afiliados en la base de datos.
    
    Hereda operaciones CRUD básicas de BaseRepository y añade
    métodos específicos para búsquedas de afiliados.
    """
    
    def __init__(self):
        """Inicializar repositorio de afiliados."""
        super().__init__(Afiliado)
    
    async def get_by_numero_poliza(
        self,
        db: AsyncSession,
        numero_poliza: str
    ) -> Optional[Afiliado]:
        """
        Obtener afiliado por número de póliza.
        
        Args:
            db: Sesión de base de datos
            numero_poliza: Número de póliza a buscar
            
        Returns:
            Afiliado encontrado o None
        """
        result = await db.execute(
            select(Afiliado).where(Afiliado.numero_poliza == numero_poliza)
        )
        return result.scalar_one_or_none()
    
    async def get_by_documento(
        self,
        db: AsyncSession,
        tipo_documento: str,
        numero_documento: str
    ) -> Optional[Afiliado]:
        """
        Obtener afiliado por documento de identidad.
        
        Args:
            db: Sesión de base de datos
            tipo_documento: Tipo de documento (CC, CE, TI, etc.)
            numero_documento: Número de documento
            
        Returns:
            Afiliado encontrado o None
        """
        result = await db.execute(
            select(Afiliado).where(
                Afiliado.tipo_documento == tipo_documento,
                Afiliado.numero_documento == numero_documento
            )
        )
        return result.scalar_one_or_none()
    
    async def search(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        numero_poliza: Optional[str] = None,
        tipo_poliza: Optional[str] = None,
        estado: Optional[str] = None,
        tipo_documento: Optional[str] = None,
        numero_documento: Optional[str] = None,
        search_text: Optional[str] = None
    ) -> List[Afiliado]:
        """
        Buscar afiliados con múltiples filtros.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            numero_poliza: Filtrar por número de póliza
            tipo_poliza: Filtrar por tipo de póliza
            estado: Filtrar por estado
            tipo_documento: Filtrar por tipo de documento
            numero_documento: Filtrar por número de documento
            search_text: Búsqueda en nombres y apellidos
            
        Returns:
            Lista de afiliados que cumplen los filtros
        """
        query = select(Afiliado)
        
        # Aplicar filtros exactos
        if numero_poliza:
            query = query.where(Afiliado.numero_poliza == numero_poliza)
        
        if tipo_poliza:
            query = query.where(Afiliado.tipo_poliza == tipo_poliza)
        
        if estado:
            query = query.where(Afiliado.estado == estado)
        
        if tipo_documento:
            query = query.where(Afiliado.tipo_documento == tipo_documento)
        
        if numero_documento:
            query = query.where(Afiliado.numero_documento == numero_documento)
        
        # Búsqueda por texto en nombres o apellidos
        if search_text:
            search_pattern = f"%{search_text}%"
            query = query.where(
                or_(
                    Afiliado.nombres.ilike(search_pattern),
                    Afiliado.apellidos.ilike(search_pattern)
                )
            )
        
        # Ordenar por fecha de creación descendente
        query = query.order_by(Afiliado.created_at.desc())
        
        # Aplicar paginación
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_activos(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Afiliado]:
        """
        Obtener afiliados activos.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de afiliados activos
        """
        query = (
            select(Afiliado)
            .where(Afiliado.estado == "ACTIVO")
            .order_by(Afiliado.created_at.desc())
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
    ) -> Optional[Afiliado]:
        """
        Obtener afiliado por ID externo (para sincronización).
        
        Args:
            db: Sesión de base de datos
            sync_source: Fuente de sincronización
            external_id: ID en el sistema externo
            
        Returns:
            Afiliado encontrado o None
        """
        result = await db.execute(
            select(Afiliado).where(
                Afiliado.sync_source == sync_source,
                Afiliado.external_id == external_id
            )
        )
        return result.scalar_one_or_none()


# Instancia singleton del repositorio
afiliado_repository = AfiliadoRepository()
