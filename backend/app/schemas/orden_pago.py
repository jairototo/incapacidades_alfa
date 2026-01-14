"""
Schemas de Pydantic para OrdenPago.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrdenPagoBase(BaseModel):
    """Schema base para OrdenPago."""
    beneficiario_tipo: str = Field(..., description="Tipo de beneficiario (EMPLEADO/EMPRESA/IPS)")
    beneficiario_id: UUID = Field(..., description="ID del beneficiario")
    beneficiario_nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del beneficiario")
    beneficiario_documento: str = Field(..., min_length=1, max_length=20, description="Documento del beneficiario")
    cuenta_bancaria: str = Field(..., min_length=1, max_length=50, description="Número de cuenta")
    banco: str = Field(..., min_length=1, max_length=100, description="Nombre del banco")
    tipo_cuenta: str = Field(..., description="Tipo de cuenta (AHORROS/CORRIENTE)")
    valor_pagar: Decimal = Field(..., ge=0, description="Valor a pagar")


class OrdenPagoCreate(OrdenPagoBase):
    """Schema para crear una orden de pago."""
    incapacidad_id: UUID = Field(..., description="ID de la incapacidad")
    metodo_pago: str = Field(default="TRANSFERENCIA", description="Método de pago")


class OrdenPagoUpdate(BaseModel):
    """Schema para actualizar una orden de pago."""
    estado_pago: Optional[str] = Field(None, description="Estado de la orden de pago")
    fecha_pago: Optional[date] = Field(None, description="Fecha de pago efectivo")
    referencia_pago: Optional[str] = Field(None, max_length=100, description="Referencia del pago")
    comprobante_ruta: Optional[str] = Field(None, description="Ruta del comprobante")


class OrdenPagoAnular(BaseModel):
    """Schema para anular una orden de pago."""
    motivo_anulacion: str = Field(..., min_length=10, description="Motivo de la anulación")


class OrdenPagoAprobar(BaseModel):
    """Schema para aprobar una orden de pago."""
    observaciones: Optional[str] = Field(None, description="Observaciones de la aprobación")


class OrdenPagoResponse(OrdenPagoBase):
    """Schema para respuesta de orden de pago."""
    id: UUID
    numero_orden: str
    incapacidad_id: UUID
    estado_pago: str
    fecha_generacion: date
    fecha_pago: Optional[date] = None
    fecha_anulacion: Optional[date] = None
    metodo_pago: str
    referencia_pago: Optional[str] = None
    comprobante_ruta: Optional[str] = None
    motivo_anulacion: Optional[str] = None
    creado_por_id: UUID
    aprobado_por_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrdenPagoListItem(BaseModel):
    """Schema para item en listado de órdenes de pago."""
    id: UUID
    numero_orden: str
    beneficiario_nombre: str
    beneficiario_tipo: str
    valor_pagar: Decimal
    estado_pago: str
    fecha_generacion: date
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
