"""
Schemas Pydantic para el registro manual de Siniestro Previsional (Task 4.4).

GAP DE ESQUEMA REAL (documentado, no resuelto aquí): el texto original del
plan (§4.2 del spec) describe un formulario "similar a la tabla siniestros,
más: ciudad, departamento, estado, eps, arl". El modelo realmente construido
en Task 2.1 (`SiniestroPrevisional`) NO tiene columnas `ciudad`,
`departamento`, `eps` ni `arl` -- solo `identificacion`, `numero_siniestro`,
`origen`, `estado`, `fecha_aviso`, `fecha_siniestro` (ver
`app/models/previsionales/siniestro_previsional.py`). Este request schema
se construye alrededor de lo que el modelo genuinamente tiene, NO se inventan
esas columnas ni se guardan en un JSONB catch-all. Si esos campos son
requeridos de verdad, hace falta una migración futura que agregue las
columnas al modelo -- fuera de alcance de esta tarea (mismo patrón de "flag,
no fix" que `observacion_alfa` en Task 4.2 y el mapeo `cie10`/`dia_181` en
Task 2.1).
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SiniestroPrevisionalCreateRequest(BaseModel):
    """Body de `POST /previsionales/siniestros`.

    `identificacion` es opcional en el schema (no `nullable=False` a nivel
    Pydantic) porque puede autocompletarse desde `incapacidad_id` -- ver
    docstring del endpoint para la regla exacta de resolución
    (requerido si no se da `incapacidad_id`; si se dan ambos, deben
    coincidir o se rechaza con 400). `numero_siniestro` es siempre
    requerido -- es NOT NULL en el modelo y no hay de dónde autocompletarlo
    (`IncapacidadPrevisional.numero_siniestro` es un campo *reportado* por
    la AFP en el excel de carga, no una referencia al siniestro real; usarlo
    para autocompletar sería inventar un dato, no autocompletar uno
    existente).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    identificacion: Optional[str] = None
    numero_siniestro: str
    origen: Optional[str] = None
    estado: Optional[str] = None
    fecha_aviso: Optional[date] = None
    fecha_siniestro: Optional[date] = None
    incapacidad_id: Optional[UUID] = None


class SiniestroPrevisionalResponse(BaseModel):
    """Fila de `SiniestroPrevisional` creada."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    identificacion: str
    numero_siniestro: str
    origen: Optional[str] = None
    estado: Optional[str] = None
    fecha_aviso: Optional[date] = None
    fecha_siniestro: Optional[date] = None
    created_at: datetime
    updated_at: datetime
