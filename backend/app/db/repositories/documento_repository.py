"""
Repository para gestión de documentos.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.documento import Documento


class DocumentoRepository(BaseRepository[Documento]):
    """Repository para operaciones con documentos."""
    
    def __init__(self):
        """Inicializa el repository."""
        super().__init__(Documento)
    
    async def get(self, db: AsyncSession, id: UUID) -> Optional[Documento]:
        """
        Obtiene un documento por ID.
        
        Args:
            db: Sesión de base de datos
            id: ID del documento
            
        Returns:
            Documento si existe, None en caso contrario
        """
        result = await db.execute(select(Documento).where(Documento.id == id))
        return result.scalar_one_or_none()
    
    async def get_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Documento]:
        """
        Obtiene todos los documentos de una incapacidad.
        
        Args:
            db: Sesión async de base de datos
            incapacidad_id: ID de la incapacidad
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de documentos de la incapacidad
        """
        query = (
            select(Documento)
            .where(Documento.incapacidad_id == incapacidad_id)
            .order_by(Documento.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_siniestro(
        self,
        db: AsyncSession,
        siniestro_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Documento]:
        """
        Obtiene todos los documentos de un siniestro a través de incapacidades.
        
        Args:
            db: Sesión async de base de datos
            siniestro_id: ID del siniestro
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de documentos del siniestro
        """
        from app.models.incapacidad import Incapacidad
        
        query = (
            select(Documento)
            .join(Incapacidad)
            .where(Incapacidad.numero_siniestro == siniestro_id)
            .order_by(Documento.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_hash_md5(
        self,
        db: AsyncSession,
        hash_md5: str
    ) -> Optional[Documento]:
        """
        Obtiene un documento por su hash MD5.
        
        Args:
            db: Sesión async de base de datos
            hash_md5: Hash MD5 del archivo
            
        Returns:
            Documento si existe, None en caso contrario
        """
        query = select(Documento).where(Documento.hash_md5 == hash_md5)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_hash_sha256(
        self,
        db: AsyncSession,
        hash_sha256: str
    ) -> Optional[Documento]:
        """
        Obtiene un documento por su hash SHA256.
        
        Args:
            db: Sesión async de base de datos
            hash_sha256: Hash SHA256 del archivo
            
        Returns:
            Documento si existe, None en caso contrario
        """
        query = select(Documento).where(Documento.hash_sha256 == hash_sha256)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_tipo(
        self,
        db: AsyncSession,
        tipo_documento: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Documento]:
        """
        Obtiene documentos por tipo.
        
        Args:
            db: Sesión async de base de datos
            tipo_documento: Tipo de documento
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de documentos del tipo especificado
        """
        query = (
            select(Documento)
            .where(Documento.tipo_documento == tipo_documento)
            .order_by(Documento.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def count_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID
    ) -> int:
        """
        Cuenta los documentos de una incapacidad.
        
        Args:
            db: Sesión async de base de datos
            incapacidad_id: ID de la incapacidad
            
        Returns:
            Número de documentos
        """
        from sqlalchemy import func
        
        query = (
            select(func.count())
            .select_from(Documento)
            .where(Documento.incapacidad_id == incapacidad_id)
        )
        result = await db.execute(query)
        return result.scalar_one()
