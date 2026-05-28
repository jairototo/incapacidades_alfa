"""
Repository para Solicitante.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.repositories.base_repository import BaseRepository
from app.models.solicitante import Solicitante


class SolicitanteRepository(BaseRepository[Solicitante]):
    """Repository para operaciones CRUD de Solicitante."""
    
    def __init__(self):
        super().__init__(Solicitante)
    
    async def get_by_correo(self, db: AsyncSession, correo: str) -> Solicitante | None:
        """
        Buscar solicitante por correo exacto.
        
        Args:
            db: Sesión de base de datos
            correo: Email del solicitante
            
        Returns:
            Solicitante si existe, None en caso contrario
        """
        query = select(Solicitante).where(
            Solicitante.correo == correo.lower().strip()
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_by_correo(
        self,
        db: AsyncSession,
        correo_partial: str,
        limit: int = 10
    ) -> List[Solicitante]:
        """
        Buscar solicitantes cuyo correo contenga el texto proporcionado.
        
        Args:
            db: Sesión de base de datos
            correo_partial: Texto a buscar en el correo
            limit: Número máximo de resultados
            
        Returns:
            Lista de solicitantes que coinciden con la búsqueda
        """
        query = (
            select(Solicitante)
            .where(Solicitante.correo.ilike(f"%{correo_partial.lower().strip()}%"))
            .limit(limit)
            .order_by(Solicitante.correo)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def search_by_nombre(
        self,
        db: AsyncSession,
        nombre_partial: str,
        limit: int = 10
    ) -> List[Solicitante]:
        """
        Buscar solicitantes por nombre o apellido.
        
        Args:
            db: Sesión de base de datos
            nombre_partial: Texto a buscar en nombres o apellidos
            limit: Número máximo de resultados
            
        Returns:
            Lista de solicitantes que coinciden con la búsqueda
        """
        search_term = f"%{nombre_partial.lower().strip()}%"
        query = (
            select(Solicitante)
            .where(
                (Solicitante.nombres.ilike(search_term)) |
                (Solicitante.apellidos.ilike(search_term))
            )
            .limit(limit)
            .order_by(Solicitante.apellidos, Solicitante.nombres)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


# Instancia global del repositorio
solicitante_repository = SolicitanteRepository()

