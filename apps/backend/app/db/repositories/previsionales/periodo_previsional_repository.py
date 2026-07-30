"""
Repositorio para Periodo Previsional.

Provee `get_by_incapacidad`, que devuelve los segmentos mensuales de una
incapacidad ordenados por `orden` (1-based, ver `segmentacion.Segmento`).
`get_by_incapacidades` (Task 3.4) es la versión batch, agregada para que
`liquidacion_service.liquidar_lote` pueda cargar los periodos de TODAS las
incapacidades del lote en una sola query en vez de hacer N+1 (una por
incapacidad) — mismo principio "nunca N+1" de CLAUDE.md que ya aplican
`auditoria_service._cargar_incapacidades_y_contexto` y
`lote_service.cargar_lote` (smlmv_cache por año). CRUD básico heredado de
BaseRepository para el resto.
"""
from collections import defaultdict
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

    async def get_by_incapacidades(
        self,
        db: AsyncSession,
        incapacidad_ids: list[UUID],
    ) -> dict[UUID, list[PeriodoPrevisional]]:
        """
        Versión batch de `get_by_incapacidad`: UNA sola query para los
        periodos de TODAS las incapacidades listadas, agrupados por
        `incapacidad_id`, cada grupo ya ordenado por `orden` ascendente.

        Args:
            db: Sesión de base de datos
            incapacidad_ids: UUIDs de las incapacidades a cargar (lista
                vacía devuelve un dict vacío sin consultar la BD)

        Returns:
            dict incapacidad_id -> lista de PeriodoPrevisional (orden asc).
            Una incapacidad sin periodos persistidos simplemente no aparece
            como clave (el llamador debe usar `.get(id, [])`).
        """
        if not incapacidad_ids:
            return {}

        query = (
            select(PeriodoPrevisional)
            .where(PeriodoPrevisional.incapacidad_id.in_(incapacidad_ids))
            .order_by(PeriodoPrevisional.incapacidad_id, PeriodoPrevisional.orden.asc())
        )
        result = await db.execute(query)
        agrupados: dict[UUID, list[PeriodoPrevisional]] = defaultdict(list)
        for periodo in result.scalars().all():
            agrupados[periodo.incapacidad_id].append(periodo)
        return dict(agrupados)


# Instancia global del repositorio
periodo_previsional_repository = PeriodoPrevisionalRepository()
