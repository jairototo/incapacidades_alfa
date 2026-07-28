"""Repositorio de consultas agregadas para analítica de empresas."""
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.empresa import Empresa
from app.models.incapacidad import Incapacidad


def _first_day_n_months_ago(n: int) -> datetime:
    """Primer día del mes que está `n - 1` meses antes del mes actual."""
    today = datetime.utcnow()
    year, month = today.year, today.month - (n - 1)
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1)


class AnaliticaRepository:
    """Consultas agregadas (server-side) para el dashboard de analítica de empresas."""

    async def top_empresas_radicadas(self, db: AsyncSession, limit: int = 10) -> Sequence[Any]:
        """Top `limit` empresas por total de incapacidades alguna vez radicadas (todo estado)."""
        query = (
            select(
                Empresa.id,
                Empresa.razon_social,
                Empresa.nit,
                func.count(Incapacidad.id).label("total"),
            )
            .join(Incapacidad, Incapacidad.empresa_id == Empresa.id)
            .group_by(Empresa.id, Empresa.razon_social, Empresa.nit)
            .order_by(func.count(Incapacidad.id).desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return result.all()

    async def tendencia_mensual_radicadas(self, db: AsyncSession, meses: int = 12) -> Sequence[Any]:
        """Total de incapacidades radicadas por mes, para los últimos `meses` meses."""
        cutoff = _first_day_n_months_ago(meses)
        periodo = func.date_trunc("month", Incapacidad.fecha_radicacion)
        query = (
            select(periodo.label("periodo"), func.count(Incapacidad.id).label("total"))
            .where(Incapacidad.fecha_radicacion >= cutoff)
            .group_by(periodo)
            .order_by(periodo)
        )
        result = await db.execute(query)
        return result.all()


# Instancia singleton del repositorio
analitica_repository = AnaliticaRepository()
