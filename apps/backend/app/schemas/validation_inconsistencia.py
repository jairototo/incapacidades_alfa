"""
Pydantic schemas para ValidationInconsistencia.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ValidationInconsistenciaBase(BaseModel):
    """Base schema para inconsistencia de validación."""
    categoria: str = Field(..., description="FIELD_VALIDATION | BUSINESS_RULE | FRAUD_ALERT | INTEGRATION_CHECK")
    severidad: str = Field(default="WARNING", description="ERROR | WARNING | INFO")
    codigo: str = Field(..., description="Machine-readable code")
    descripcion: str = Field(...)
    campo_afectado: Optional[str] = None
    valor_encontrado: Optional[str] = None
    valor_esperado: Optional[str] = None


class ValidationInconsistenciaCreate(ValidationInconsistenciaBase):
    """Schema para crear inconsistencia."""
    pre_incapacidad_id: UUID
    incapacidad_id: Optional[UUID] = None


class ValidationInconsistenciaRead(ValidationInconsistenciaBase):
    """Schema para leer inconsistencia."""
    id: UUID
    pre_incapacidad_id: UUID
    incapacidad_id: Optional[UUID]
    fecha_deteccion: datetime

    class Config:
        from_attributes = True


class ValidationSummary(BaseModel):
    """Resumen de validación."""
    total_issues: int
    errors: int
    warnings: int
    infos: int
    issues: list[ValidationInconsistenciaRead]


class PromotionResult(BaseModel):
    """Resultado de promoción de pre-incapacidad."""
    success: bool
    pre_incapacidad_id: UUID
    incapacidad_id: Optional[UUID] = None
    validation_summary: ValidationSummary
    error_message: Optional[str] = None
    timestamp: datetime
