"""
Schemas Pydantic para Plantilla de Auditoría.

Usados para validar entrada y serializar salida de los endpoints
POST/GET /incapacidades/{id}/plantilla-auditoria.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlantillaAuditoriaCreate(BaseModel):
    """Schema de entrada para crear o actualizar una plantilla de auditoría."""

    canal_recepcion: str = Field(
        ...,
        max_length=100,
        description="Canal de recepción del documento: Portal / Imaginex / Onbase",
        examples=["Portal"],
    )

    nombre_ips: Optional[str] = Field(
        None,
        max_length=255,
        description="Nombre de la IPS que emitió la incapacidad",
    )

    fecha_emision_incapacidad: Optional[date] = Field(
        None,
        description="Fecha de emisión del documento de incapacidad",
    )

    dias_autorizados: int = Field(
        ...,
        gt=0,
        description="Número de días autorizados (debe ser mayor que 0)",
    )

    fecha_inicio_autorizada: date = Field(
        ...,
        description="Fecha de inicio del período autorizado",
    )

    fecha_fin_autorizada: date = Field(
        ...,
        description="Fecha de fin del período autorizado",
    )

    diagnostico_cie10: Optional[str] = Field(
        None,
        max_length=10,
        description="Código CIE-10 del diagnóstico",
    )

    descripcion_cie10: Optional[str] = Field(
        None,
        description="Descripción del diagnóstico CIE-10",
    )

    nombre_medico: Optional[str] = Field(
        None,
        max_length=200,
        description="Nombre del médico que emitió la incapacidad",
    )

    especialidad_medico: Optional[str] = Field(
        None,
        max_length=100,
        description="Especialidad del médico tratante",
    )

    dias_documento: Optional[int] = Field(
        None,
        gt=0,
        description="Total de días en el documento físico (para aprobación parcial)",
    )

    rango_pagado_inicio: Optional[date] = Field(
        None,
        description="Inicio del rango efectivamente pagado (aprobación parcial)",
    )

    rango_pagado_fin: Optional[date] = Field(
        None,
        description="Fin del rango efectivamente pagado (aprobación parcial)",
    )

    # Computed field — populated by validator, not by the client
    linea_autorizacion: Optional[str] = Field(
        None,
        description="Auto-generado por el servidor",
        exclude=True,
    )

    @model_validator(mode="after")
    def compute_linea_autorizacion(self) -> "PlantillaAuditoriaCreate":
        """Genera la línea de autorización automáticamente."""
        self.linea_autorizacion = (
            f"Se autoriza pago por {self.dias_autorizados} días "
            f"desde {self.fecha_inicio_autorizada.isoformat()} "
            f"hasta {self.fecha_fin_autorizada.isoformat()}"
        )
        return self


class PlantillaAuditoriaResponse(BaseModel):
    """Schema de respuesta con todos los campos de la plantilla."""

    id: UUID
    incapacidad_id: UUID
    canal_recepcion: str
    nombre_ips: Optional[str] = None
    fecha_emision_incapacidad: Optional[date] = None
    dias_autorizados: int
    fecha_inicio_autorizada: date
    fecha_fin_autorizada: date
    diagnostico_cie10: Optional[str] = None
    descripcion_cie10: Optional[str] = None
    nombre_medico: Optional[str] = None
    especialidad_medico: Optional[str] = None
    linea_autorizacion: Optional[str] = None
    dias_documento: Optional[int] = None
    rango_pagado_inicio: Optional[date] = None
    rango_pagado_fin: Optional[date] = None
    auditado_por_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
