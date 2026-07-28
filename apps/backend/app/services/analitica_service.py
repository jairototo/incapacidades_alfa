"""Servicio de analítica de empresas: arma la respuesta agregada para el dashboard."""
from datetime import datetime
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.analitica_repository import analitica_repository
from app.schemas.analitica import AnaliticaEmpresasResponse, EmpresaTopItem, TendenciaMensualItem


class AnaliticaService:
    """Lógica de negocio para el endpoint de analítica de empresas."""

    def __init__(self):
        self.repository = analitica_repository

    async def get_analitica_empresas(self, db: AsyncSession) -> AnaliticaEmpresasResponse:
        top_rows = await self.repository.top_empresas_radicadas(db, limit=10)
        top_empresas = [
            EmpresaTopItem(
                empresa_id=row.id,
                razon_social=row.razon_social,
                nit=row.nit,
                total_radicadas=row.total,
            )
            for row in top_rows
        ]

        tendencia_rows = await self.repository.tendencia_mensual_radicadas(db, meses=12)
        por_periodo: Dict[str, int] = {
            row.periodo.strftime("%Y-%m"): row.total for row in tendencia_rows
        }
        tendencia_mensual = self._rellenar_meses_faltantes(por_periodo)

        return AnaliticaEmpresasResponse(
            top_empresas=top_empresas,
            tendencia_mensual=tendencia_mensual,
        )

    def _rellenar_meses_faltantes(self, por_periodo: Dict[str, int]) -> List[TendenciaMensualItem]:
        """Genera los últimos 12 periodos (YYYY-MM) en orden cronológico, con 0 donde no hubo datos."""
        hoy = datetime.utcnow()
        year, month = hoy.year, hoy.month
        periodos = []
        for _ in range(12):
            periodos.append(f"{year:04d}-{month:02d}")
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        periodos.reverse()
        return [
            TendenciaMensualItem(periodo=p, total=por_periodo.get(p, 0))
            for p in periodos
        ]


# Singleton
analitica_service = AnaliticaService()
