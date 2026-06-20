from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RadicacionRowInput(BaseModel):
    """Una fila de radicación (individual = 1 fila). Sin datos de empresa/solicitante."""
    empleado_id: UUID
    tipo_enfermedad: str
    fecha_inicio: date
    fecha_fin: date
    dias_totales: int
    diagnostico_cie10: str
    descripcion_diagnostico: Optional[str] = None
    nombre_medico: str
    registro_medico: str
    ips: Optional[str] = None
    valor_dia: Optional[Decimal] = None
    prorroga: bool = False
    observaciones: Optional[str] = None


class RadicacionResultItem(BaseModel):
    empleado_id: UUID
    incapacidad_id: Optional[UUID] = None
    numero: Optional[str] = None
    success: bool
    error: Optional[str] = None


class RadicacionResponse(BaseModel):
    items: list[RadicacionResultItem]
    total_radicadas: int
    documentos_ignorados: list[dict] = []   # docs that couldn't be stored/matched

    model_config = ConfigDict(from_attributes=True)
