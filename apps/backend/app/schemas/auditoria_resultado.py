"""Pydantic schema para AuditoriaResultado."""
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditoriaResultadoSchema(BaseModel):
    id: UUID
    incapacidad_id: UUID
    regla: str
    categoria: str
    aprobado: bool
    severidad: str
    detalle: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
