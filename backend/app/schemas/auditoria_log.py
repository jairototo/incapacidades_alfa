"""
Schemas de Pydantic para AuditoriaLog.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditoriaLogBase(BaseModel):
    """Schema base para AuditoriaLog."""
    accion: str = Field(..., description="Acción realizada")
    entidad: str = Field(..., max_length=100, description="Tipo de entidad afectada")
    entidad_id: UUID = Field(..., description="ID de la entidad afectada")
    detalles: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales en formato JSON")


class AuditoriaLogCreate(AuditoriaLogBase):
    """Schema para crear un registro de auditoría."""
    usuario_id: Optional[UUID] = Field(None, description="ID del usuario que realizó la acción")
    ip_address: Optional[str] = Field(None, description="Dirección IP")
    user_agent: Optional[str] = Field(None, description="User agent del navegador")
    request_id: Optional[str] = Field(None, max_length=100, description="ID de la petición")


class AuditoriaLogResponse(AuditoriaLogBase):
    """Schema para respuesta de log de auditoría."""
    id: UUID
    usuario_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditoriaLogListItem(BaseModel):
    """Schema para item en listado de logs de auditoría."""
    id: UUID
    accion: str
    entidad: str
    entidad_id: UUID
    usuario_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditoriaLogFilter(BaseModel):
    """Schema para filtrar logs de auditoría."""
    usuario_id: Optional[UUID] = Field(None, description="Filtrar por usuario")
    accion: Optional[str] = Field(None, description="Filtrar por acción")
    entidad: Optional[str] = Field(None, description="Filtrar por tipo de entidad")
    entidad_id: Optional[UUID] = Field(None, description="Filtrar por ID de entidad específica")
    fecha_desde: Optional[datetime] = Field(None, description="Fecha inicio")
    fecha_hasta: Optional[datetime] = Field(None, description="Fecha fin")
