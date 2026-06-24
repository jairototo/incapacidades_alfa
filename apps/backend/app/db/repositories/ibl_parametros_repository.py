"""
Repositorio para parámetros IBL (Ingreso Base de Liquidación).

Proporciona acceso a los porcentajes de aportes configurados por año.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.ibl_parametros import IblParametros


class IblParametrosRepository(BaseRepository[IblParametros]):
    """Repositorio para operaciones con IblParametros."""

    def __init__(self) -> None:
        super().__init__(IblParametros)

    async def get_by_ano(
        self,
        db: AsyncSession,
        ano: int,
    ) -> Optional[IblParametros]:
        """
        Obtener los parámetros IBL para un año específico.

        Args:
            db: Sesión de base de datos
            ano: Año calendario (p.ej. 2026)

        Returns:
            IblParametros si existe para ese año, None en caso contrario
        """
        result = await db.execute(
            select(IblParametros).where(IblParametros.ano == ano)
        )
        return result.scalar_one_or_none()


# Instancia global del repositorio
ibl_parametros_repository = IblParametrosRepository()
