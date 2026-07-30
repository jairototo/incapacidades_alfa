"""
Schemas Pydantic para Lotes e Incapacidades Previsionales (Task 4.1).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LotePrevisionalResponse(BaseModel):
    """Resumen de un lote previsional -- usado en list (GET /lotes) y en
    detalle (GET /lotes/{id}). Los "contadores" del listado son los que ya
    persiste `LotePrevisional` (`total_filas`, `total_incapacidades`) -- ver
    nota en `endpoints/previsionales/lotes.py::listar_lotes` sobre por qué
    no se agregan desgloses adicionales por filtro aquí."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre_archivo: str
    estado: str
    fecha_cargue: datetime
    cargado_por_id: Optional[UUID] = None
    total_filas: int
    total_incapacidades: int
    observaciones: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IncapacidadPrevisionalResponse(BaseModel):
    """Fila de incapacidad previsional dentro de un lote (datos crudos de
    carga + resultado de auditoría/liquidación, ver
    `IncapacidadPrevisional`)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lote_id: UUID
    tipo_identificacion: Optional[str] = None
    identificacion: Optional[str] = None
    radicado: Optional[str] = None
    radicado_normalizado: Optional[str] = None
    tipo_ingreso: Optional[str] = None
    fecha_inicial: Optional[date] = None
    fecha_final: Optional[date] = None
    dia_181_alfa: Optional[date] = None
    dia_181_afp: Optional[date] = None
    dia_181_arpis: Optional[date] = None
    fecha_crie: Optional[date] = None
    fecha_radicacion_afp: Optional[date] = None
    fecha_radicacion_alfa: Optional[date] = None
    numero_siniestro: Optional[str] = None
    valor_afp: Optional[Decimal] = None
    cie10: Optional[str] = None
    observacion: Optional[str] = None
    observacion_causal: Optional[str] = None
    aval: Optional[str] = None
    motivo_no_aval: Optional[str] = None
    estado: str
    prorroga_de_id: Optional[UUID] = None
    incapacidad_origen_id: Optional[UUID] = None
    es_duplicado_interno: bool
    valor_auditado: Optional[Decimal] = None
    diferencia_valor_afp: Optional[Decimal] = None
    errores_carga: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
