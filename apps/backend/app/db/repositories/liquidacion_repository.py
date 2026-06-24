"""
Repositorio para operaciones de Liquidación.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.liquidacion import Liquidacion


class LiquidacionRepository(BaseRepository[Liquidacion]):
    """Repositorio para operaciones con Liquidacion."""

    def __init__(self) -> None:
        super().__init__(Liquidacion)

    async def get_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
    ) -> Optional[Liquidacion]:
        """
        Obtener la liquidación para una incapacidad dada (relación 1:1).

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad

        Returns:
            Liquidacion si existe, None en caso contrario
        """
        result = await db.execute(
            select(Liquidacion).where(Liquidacion.incapacidad_id == incapacidad_id)
        )
        return result.scalar_one_or_none()


# Instancia global del repositorio
liquidacion_repository = LiquidacionRepository()
