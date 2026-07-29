"""
Repositorio para parámetros SMLMV (Salario Mínimo Legal Mensual Vigente).

Proporciona acceso a los valores del SMLMV configurados por año,
usados como piso en cálculos de liquidación de incapacidades.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.previsionales.smlmv_parametros import SmlmvParametros


class SmlmvParametrosRepository(BaseRepository[SmlmvParametros]):
    """Repositorio para operaciones con SmlmvParametros."""

    def __init__(self) -> None:
        super().__init__(SmlmvParametros)

    async def get_by_ano(
        self,
        db: AsyncSession,
        ano: int,
    ) -> Optional[SmlmvParametros]:
        """
        Obtener los parámetros SMLMV para un año específico.

        Args:
            db: Sesión de base de datos
            ano: Año calendario (p.ej. 2026)

        Returns:
            SmlmvParametros si existe para ese año, None en caso contrario
        """
        result = await db.execute(
            select(SmlmvParametros).where(SmlmvParametros.ano == ano)
        )
        return result.scalar_one_or_none()


# Instancia global del repositorio
smlmv_parametros_repository = SmlmvParametrosRepository()
