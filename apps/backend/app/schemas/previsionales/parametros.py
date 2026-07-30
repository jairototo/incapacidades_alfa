"""
Schemas Pydantic para Parámetros SMLMV Previsionales (Task 4.1).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SmlmvParametrosResponse(BaseModel):
    """Un valor de SMLMV configurado para un año calendario."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ano: int
    valor: Decimal
    vigente_desde: date
