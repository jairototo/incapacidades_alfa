"""
Schemas Pydantic para HistorialEstado.

Define los modelos de validación para las operaciones
de historial de cambios de estado (polimórfico).
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class HistorialEstadoBase(BaseModel):
    """Campos base compartidos de HistorialEstado."""
    
    entity_type: str = Field(..., description="Tipo de entidad: incapacidad, siniestro, etc.", max_length=50)
    entity_id: UUID = Field(..., description="ID de la entidad relacionada")
    estado_anterior: Optional[str] = Field(None, description="Estado previo al cambio", max_length=50)
    estado_nuevo: str = Field(..., description="Nuevo estado después del cambio", max_length=50)
    observacion: Optional[str] = Field(None, description="Observaciones sobre el cambio")


class HistorialEstadoCreate(HistorialEstadoBase):
    """Schema para crear un registro de historial."""
    
    cambiado_por_id: Optional[UUID] = Field(None, description="ID del usuario que realizó el cambio")
    metadata: Optional[dict] = Field(None, description="Metadata adicional en formato JSON")


class HistorialEstadoUpdate(BaseModel):
    """
    Schema para actualizar un registro de historial.
    
    Nota: Generalmente no se actualizan registros de historial,
    pero se incluye por consistencia con el patrón.
    """
    
    observacion: Optional[str] = Field(None, description="Actualizar observación")
    metadata: Optional[dict] = Field(None, description="Actualizar metadata")


class HistorialEstadoInDB(HistorialEstadoBase):
    """Schema para registro completo en base de datos."""
    
    id: UUID
    fecha_cambio: datetime
    cambiado_por_id: Optional[UUID]
    cambiado_por_nombre: Optional[str] = Field(
        None, description="Nombre del usuario que realizó el cambio (None si fue automático)"
    )
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = Field(None, validation_alias="metadata_")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HistorialEstadoResponse(HistorialEstadoInDB):
    """Schema para respuesta de API."""
    
    pass


class HistorialEstadoListResponse(BaseModel):
    """Schema para lista paginada de registros de historial."""
    
    items: list[HistorialEstadoResponse]
    total: int
    skip: int
    limit: int
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None

