"""
Repository para Catálogo CIE-10.
"""

from sqlalchemy import select, or_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.models.catalogo_cie10 import CatalogoCIE10


class CatalogoRepository:
    """Repository para operaciones de lectura del catálogo CIE-10."""
    
    def __init__(self):
        pass
    
    async def search_cie10(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10
    ) -> List[CatalogoCIE10]:
        """
        Buscar códigos CIE-10 por código o descripción.
        
        La búsqueda es case-insensitive y soporta búsqueda parcial.
        
        Args:
            db: Sesión de base de datos
            query: Texto a buscar (código o descripción)
            limit: Número máximo de resultados
            
        Returns:
            Lista de códigos CIE-10 que coinciden
        """
        search_term = f"%{query.upper()}%"
        
        # Priorizar coincidencias exactas de código
        stmt = (
            select(CatalogoCIE10)
            .where(
                or_(
                    CatalogoCIE10.codigo.ilike(search_term),
                    CatalogoCIE10.descripcion.ilike(search_term)
                )
            )
            .order_by(
                # Ordenar: códigos que empiezan con la búsqueda primero
                case(
                    (CatalogoCIE10.codigo.ilike(f"{query.upper()}%"), 1),
                    else_=2
                ),
                CatalogoCIE10.codigo
            )
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_codigo(self, db: AsyncSession, codigo: str) -> CatalogoCIE10 | None:
        """
        Obtener un código CIE-10 por su código exacto.
        
        Args:
            db: Sesión de base de datos
            codigo: Código CIE-10 exacto (ej: "A00.0")
            
        Returns:
            CatalogoCIE10 si existe, None en caso contrario
        """
        stmt = select(CatalogoCIE10).where(
            CatalogoCIE10.codigo == codigo.upper()
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
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
        stmt = (
            select(CatalogoCIE10)
            .order_by(CatalogoCIE10.codigo)
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def count(self, db: AsyncSession) -> int:
        """
        Contar el número total de códigos CIE-10 en el catálogo.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Número total de códigos
        """
        stmt = select(func.count()).select_from(CatalogoCIE10)
        result = await db.execute(stmt)
        return result.scalar_one()
    
    async def create(
        self,
        db: AsyncSession,
        codigo: str,
        descripcion: str
    ) -> CatalogoCIE10:
        """
        Crear un nuevo código CIE-10.
        
        Args:
            db: Sesión de base de datos
            codigo: Código CIE-10
            descripcion: Descripción del diagnóstico
            
        Returns:
            CatalogoCIE10 creado
        """
        cie10 = CatalogoCIE10(
            codigo=codigo.upper(),
            descripcion=descripcion
        )
        db.add(cie10)
        await db.commit()
        await db.refresh(cie10)
        return cie10


# Instancia global del repositorio
catalogo_repository = CatalogoRepository()

