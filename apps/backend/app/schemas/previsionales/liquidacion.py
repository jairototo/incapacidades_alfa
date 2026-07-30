"""
Schemas Pydantic para los endpoints de liquidación previsional (Task 4.3) --
ver `app/api/v1/endpoints/previsionales/liquidacion.py`.
"""
from __future__ import annotations

from pydantic import BaseModel


class LiquidarLoteResponse(BaseModel):
    """Resultado de POST /previsionales/lotes/{lote_id}/liquidar -- cuántas
    incapacidades del lote se liquidaron efectivamente (excluye duplicados
    internos y filas omitidas por error, ver
    `liquidacion_previsional_service.liquidar_lote`)."""

    liquidadas: int
