"""
Service para Catálogo CIE-10.
"""

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.catalogo_repository import catalogo_repository
from app.models.catalogo_cie10 import CatalogoCIE10
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger


class CatalogoService:
    """Service para lógica de negocio del catálogo CIE-10."""
    
    def __init__(self):
        """Inicializa el service con el repositorio global."""
        self.repository = catalogo_repository
    
    async def search_cie10(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10
    ) -> List[CatalogoCIE10]:
        """
        Buscar códigos CIE-10 por código o descripción.
        
        Args:
            db: Sesión de base de datos
            query: Texto a buscar
            limit: Número máximo de resultados
            
        Returns:
            Lista de códigos CIE-10 que coinciden
            
        Raises:
            ValidationException: Si el término de búsqueda es muy corto
        """
        # Validar longitud mínima de búsqueda
        if not query or len(query.strip()) < 2:
            raise ValidationException(
                "El término de búsqueda debe tener al menos 2 caracteres"
            )
        
        return await self.repository.search_cie10(db, query.strip(), limit)
    
    async def get_cie10_by_codigo(
        self,
        db: AsyncSession,
        codigo: str
    ) -> CatalogoCIE10:
        """
        Obtener un código CIE-10 por su código exacto.
        
        Args:
            db: Sesión de base de datos
            codigo: Código CIE-10
            
        Returns:
            CatalogoCIE10 encontrado
            
        Raises:
            NotFoundException: Si el código no existe
        """
        cie10 = await self.repository.get_by_codigo(db, codigo)
        
        if not cie10:
            raise NotFoundException(
                f"Código CIE-10 '{codigo}' no encontrado en el catálogo"
            )
        
        return cie10
    
    async def codigos_existentes(
        self,
        db: AsyncSession,
        codigos: set[str]
    ) -> set[str]:
        """Devuelve el subconjunto de códigos CIE-10 que existen en el catálogo (batch).

        Pensado para validar la existencia de múltiples códigos en una sola
        consulta (radicación masiva/individual), evitando N+1.

        Args:
            db: Sesión de base de datos
            codigos: Conjunto de códigos CIE-10 a verificar

        Returns:
            Conjunto de códigos existentes (en mayúsculas)
        """
        return await self.repository.get_existing_codigos(db, codigos)

    async def get_all(
        self,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[CatalogoCIE10]:
        """
        Obtener todos los códigos CIE-10 (paginado).
        
        Args:
            db: Sesión de base de datos
            limit: Número máximo de resultados
            offset: Número de registros a saltar
            
        Returns:
            Lista de códigos CIE-10
        """
        if limit > 500:
            limit = 500  # Límite máximo
        
        return await self.repository.get_all(db, limit, offset)
    
    async def count(self, db: AsyncSession) -> int:
        """
        Obtener el número total de códigos CIE-10.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Número total de códigos
        """
        return await self.repository.count(db)
    
    async def create_cie10(
        self,
        db: AsyncSession,
        codigo: str,
        descripcion: str
    ) -> CatalogoCIE10:
        """
        Crear un nuevo código CIE-10 (solo para admin).
        
        Args:
            db: Sesión de base de datos
            codigo: Código CIE-10
            descripcion: Descripción del diagnóstico
            
        Returns:
            CatalogoCIE10 creado
            
        Raises:
            ValidationException: Si el código ya existe
        """
        # Verificar si el código ya existe
        existing = await self.repository.get_by_codigo(db, codigo)
        if existing:
            raise ValidationException(
                f"El código CIE-10 '{codigo}' ya existe en el catálogo"
            )
        
        created = await self.repository.create(db, codigo, descripcion)
        
        logger.info(
            f"Código CIE-10 creado",
            extra={"codigo": codigo}
        )
        
        return created


# Instancia global del servicio
catalogo_service = CatalogoService()
