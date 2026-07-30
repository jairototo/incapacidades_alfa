"""
Repositorio para Periodo Previsional.

Provee `get_by_incapacidad`, que devuelve los segmentos mensuales de una
incapacidad ordenados por `orden` (1-based, ver `segmentacion.Segmento`).
CRUD básico heredado de BaseRepository para el resto.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.previsionales.periodo_previsional import PeriodoPrevisional


class PeriodoPrevisionalRepository(BaseRepository[PeriodoPrevisional]):
    """Repositorio para operaciones con PeriodoPrevisional."""

    def __init__(self) -> None:
        super().__init__(PeriodoPrevisional)

    async def get_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
    ) -> list[PeriodoPrevisional]:
        """
        Listar los segmentos (periodos) de una incapacidad, ordenados por
        `orden` ascendente.

        Args:
            db: Sesión de base de datos
            incapacidad_id: UUID de la IncapacidadPrevisional

        Returns:
            Lista de PeriodoPrevisional ordenada por `orden`
        """
        query = (
            select(PeriodoPrevisional)
            .where(PeriodoPrevisional.incapacidad_id == incapacidad_id)
            .order_by(PeriodoPrevisional.orden.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())


# Instancia global del repositorio
periodo_previsional_repository = PeriodoPrevisionalRepository()
