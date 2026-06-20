"""
Schemas Pydantic para Auditoría Datos Aprobados.

Estos schemas se utilizan para validar los datos aprobados por el auditor
durante la auditoría cuando se realiza una aprobación parcial.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class AuditoriaDatosAprobadosBase(BaseModel):
    """Schema base para datos aprobados en auditoría."""
    
    fecha_inicio_aprobada: date = Field(
        ...,
        description="Fecha de inicio aprobada por el auditor"
    )
    
    fecha_fin_aprobada: date = Field(
        ...,
        description="Fecha de fin aprobada por el auditor"
    )
    
    dias_aprobados: int = Field(
        ...,
        ge=1,
        description="Cantidad de días aprobados (calculados automáticamente)"
    )
    
    cie10_aprobado: str = Field(
        ...,
        max_length=10,
        description="Código CIE-10 aprobado por el auditor"
    )
    
    diagnostico_aprobado: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Descripción del diagnóstico aprobado"
    )
    
    observacion_auditoria: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Observaciones del auditor justificando las modificaciones"
    )
    
    @field_validator('cie10_aprobado')
    @classmethod
    def validate_cie10(cls, v: str) -> str:
        """Validar formato de código CIE-10."""
        # Formato: Letra + 2 dígitos + opcional (punto + 1-2 dígitos)
        pattern = r'^[A-Z]\d{3}(\.\d{1,2})?$'
        if not re.match(pattern, v):
            raise ValueError(
                'Código CIE-10 inválido. Formato esperado: A00 o A00.1 o A00.12'
            )
        return v.upper()
    
    @field_validator('fecha_fin_aprobada')
    @classmethod
    def validate_fechas(cls, v: date, info) -> date:
        """Validar que fecha_fin_aprobada sea posterior a fecha_inicio_aprobada."""
        if 'fecha_inicio_aprobada' in info.data:
            fecha_inicio = info.data['fecha_inicio_aprobada']
            if v < fecha_inicio:
                raise ValueError(
                    'La fecha de fin aprobada debe ser posterior a la fecha de inicio'
                )
        return v


class AuditoriaDatosAprobadosCreate(AuditoriaDatosAprobadosBase):
    """Schema para crear datos aprobados en auditoría."""
    
    incapacidad_id: UUID = Field(
        ...,
        description="ID de la incapacidad auditada"
    )
    
    auditado_por_id: UUID = Field(
        ...,
        description="ID del usuario auditor"
    )
    
    fecha_auditoria: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha y hora de la auditoría"
    )


class AuditoriaDatosAprobadosUpdate(BaseModel):
    """Schema para actualizar datos aprobados (si se requiere re-auditoría)."""
    
    fecha_inicio_aprobada: Optional[date] = None
    fecha_fin_aprobada: Optional[date] = None
    dias_aprobados: Optional[int] = Field(None, ge=1)
    cie10_aprobado: Optional[str] = Field(None, max_length=10)
    diagnostico_aprobado: Optional[str] = Field(None, min_length=3, max_length=500)
    observacion_auditoria: Optional[str] = Field(None, min_length=10, max_length=1000)
    
    @field_validator('cie10_aprobado')
    @classmethod
    def validate_cie10(cls, v: Optional[str]) -> Optional[str]:
        """Validar formato de código CIE-10."""
        if v is None:
            return v
        
        pattern = r'^[A-Z]\d{3}(\.\d{1,2})?$'
        if not re.match(pattern, v):
            raise ValueError(
                'Código CIE-10 inválido. Formato esperado: A00 o A00.1 o A00.12'
            )
        return v.upper()


class AuditoriaDatosAprobadosResponse(AuditoriaDatosAprobadosBase):
    """Schema de respuesta con datos completos."""
    
    id: UUID
    incapacidad_id: UUID
    auditado_por_id: UUID
    fecha_auditoria: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditoriaDatosAprobadosInDB(AuditoriaDatosAprobadosResponse):
    """Schema para datos en base de datos (alias de Response)."""
    pass
