"""
Schemas Pydantic para Siniestro.
"""
from datetime import date, time, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.utils.enums import TipoSiniestro, GravedadSiniestro, EstadoSiniestro, SyncSource


class SiniestroBase(BaseModel):
    """Schema base de Siniestro."""
    empleado_id: UUID
    empresa_id: UUID
    fecha_siniestro: date
    hora_siniestro: Optional[time] = None
    tipo_siniestro: TipoSiniestro
    descripcion: str = Field(..., min_length=10)
    lugar_ocurrencia: Optional[str] = Field(None, max_length=255)
    parte_cuerpo_afectada: Optional[str] = Field(None, max_length=100)
    naturaleza_lesion: Optional[str] = Field(None, max_length=100)
    agente_causante: Optional[str] = Field(None, max_length=255)
    gravedad: GravedadSiniestro = GravedadSiniestro.LEVE
    testigos: Optional[str] = None
    requirio_hospitalizacion: bool = False
    dias_estimados_incapacidad: Optional[int] = Field(None, ge=0)
    reportado_por: Optional[str] = Field(None, max_length=255)
    observaciones: Optional[str] = None


class SiniestroCreate(SiniestroBase):
    """Schema para crear siniestro."""
    pass


class SiniestroUpdate(BaseModel):
    """Schema para actualizar siniestro."""
    descripcion: Optional[str] = None
    lugar_ocurrencia: Optional[str] = None
    parte_cuerpo_afectada: Optional[str] = None
    naturaleza_lesion: Optional[str] = None
    agente_causante: Optional[str] = None
    gravedad: Optional[GravedadSiniestro] = None
    testigos: Optional[str] = None
    requirio_hospitalizacion: Optional[bool] = None
    dias_estimados_incapacidad: Optional[int] = None
    estado: Optional[EstadoSiniestro] = None
    observaciones: Optional[str] = None


class SiniestroImport(BaseModel):
    """Schema para importar siniestro desde sistema externo."""
    numero_siniestro: str
    empleado_documento: str  # Se buscará el empleado por documento
    empresa_nit: str  # Se buscará la empresa por NIT
    fecha_siniestro: date
    hora_siniestro: Optional[time] = None
    tipo_siniestro: TipoSiniestro
    descripcion: str
    lugar_ocurrencia: Optional[str] = None
    parte_cuerpo_afectada: Optional[str] = None
    naturaleza_lesion: Optional[str] = None
    agente_causante: Optional[str] = None
    gravedad: GravedadSiniestro = GravedadSiniestro.LEVE
    testigos: Optional[str] = None
    requirio_hospitalizacion: bool = False
    dias_estimados_incapacidad: Optional[int] = None
    reportado_por: Optional[str] = None
    observaciones: Optional[str] = None
    external_id: Optional[str] = None  # ID del sistema externo


class SiniestroInDB(SiniestroBase):
    """Schema de siniestro completo desde DB."""
    id: UUID
    numero_siniestro: str
    estado: EstadoSiniestro
    fecha_reporte: datetime
    sync_source: Optional[SyncSource]
    external_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class EmpleadoSimple(BaseModel):
    """Schema simplificado de empleado."""
    id: UUID
    nombre_completo: str
    documento: str
    
    model_config = {"from_attributes": True}


class EmpresaSimple(BaseModel):
    """Schema simplificado de empresa."""
    id: UUID
    razon_social: str
    nit: str
    
    model_config = {"from_attributes": True}


class SiniestroResponse(SiniestroInDB):
    """Schema de respuesta de siniestro con relaciones."""
    empleado: EmpleadoSimple
    empresa: EmpresaSimple
    total_incapacidades: int = 0
    
    model_config = {"from_attributes": True}


class SiniestroListResponse(BaseModel):
    """Schema de lista de siniestros."""
    id: UUID
    numero_siniestro: str
    empleado: EmpleadoSimple
    empresa: EmpresaSimple
    fecha_siniestro: date
    tipo_siniestro: TipoSiniestro
    gravedad: GravedadSiniestro
    estado: EstadoSiniestro
    descripcion: str
    parte_cuerpo_afectada: Optional[str]
    dias_estimados_incapacidad: Optional[int]
    fecha_reporte: datetime
    
    model_config = {"from_attributes": True}


class SiniestroImportResult(BaseModel):
    """Schema de resultado de importación."""
    total_procesados: int
    exitosos: int
    fallidos: int
    errores: list[dict] = []
