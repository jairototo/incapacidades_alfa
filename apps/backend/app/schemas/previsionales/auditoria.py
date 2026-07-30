"""
Schemas Pydantic para el workflow de auditoría previsional (Task 4.2) --
ver `app/api/v1/endpoints/previsionales/auditoria.py` y
`app/services/previsionales/auditoria_service.py`.

Sobre `IncapacidadPrevisionalPatchRequest` -- gap real de columnas, NO un
descuido de esta tarea: el brief original del plan menciona "campos ALFA de
auditoría" (`dia_181_alfa`, `fecha_crie_alfa`, `observacion_alfa`) como si
los 3 fueran editables por el auditor. Verificado contra el modelo
(`incapacidad_previsional.py`, Task 3.3):

- `dia_181_alfa` SÍ existe y SÍ es la columna auditor-owned (comment: "Día
  181 auditado (Alfa)... usado por regla AB") -- es el único campo que este
  schema expone.
- `fecha_crie` SÍ existe como columna, pero NO es "fecha_crie_alfa": su
  comment dice "Fecha CRIE de la solicitud AFP -- usada por regla AG", es
  decir, se puebla desde el cruce con SOLICITUDES (Task 3.2/3.3), no desde
  una edición manual del auditor. No se expone aquí.
- `observacion_alfa` NO EXISTE como columna. Solo existen `observacion` (el
  texto libre crudo de la AFP, columna W del excel) y `observacion_causal`
  (texto de causal de tutela/legal) -- ninguna de las dos es "la
  observación propia del auditor". Añadir esta columna requiere una
  migración futura; no se aproxima aquí con JSONB (`metadata_`) porque el
  brief de esta tarea es explícito en que estas son decisiones de auditor
  genuinamente consultables/auditables, no datos informativos de relleno.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SenalAuditoriaPrevisionalResponse(BaseModel):
    """Una señal persistida (una de las 19 reglas AB-AT) para una incapacidad."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incapacidad_previsional_id: UUID
    codigo: str
    nombre: str
    estado: str
    valor: Optional[Any] = None
    detalle: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IncapacidadPrevisionalPatchRequest(BaseModel):
    """
    PATCH parcial de una incapacidad previsional -- ÚNICO campo soportado:
    `dia_181_alfa` (ver docstring del módulo para el porqué de
    `fecha_crie_alfa`/`observacion_alfa` NO están aquí: gap real de
    columnas, no un olvido).
    """

    dia_181_alfa: Optional[date] = None


class AvalRequest(BaseModel):
    """Body de POST /previsionales/incapacidades/{id}/aval."""

    aval: Literal["SI", "NO"]
    motivo: Optional[str] = None


class DuplicarRequest(BaseModel):
    """Body de POST /previsionales/incapacidades/{id}/duplicar."""

    fecha_inicial: date
    fecha_final: date
