"""
Schemas Pydantic para Liquidación de Incapacidad.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.utils.enums import MetodoPagoLiquidacion


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class LiquidacionGuardar(BaseModel):
    """Payload para crear o actualizar la liquidación de una incapacidad."""

    model_config = ConfigDict(from_attributes=True)

    ibl: Optional[Decimal] = None
    periodo_ibl_inicio: Optional[date] = None
    periodo_ibl_fin: Optional[date] = None

    dias_autorizados: int
    fecha_inicio_autorizada: date
    fecha_fin_autorizada: date

    # Desglose calculado (todo opcional — pendiente confirmación fórmulas C1/C2)
    valor_incapacidad_temporal: Optional[Decimal] = None
    valor_aporte_patronal_pension: Optional[Decimal] = None
    valor_aporte_trabajador_pension: Optional[Decimal] = None
    valor_aporte_adicional_trabajador_pension: Optional[Decimal] = None
    valor_aporte_patronal_salud: Optional[Decimal] = None
    valor_aporte_trabajador_salud: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None

    metodo_pago: Optional[MetodoPagoLiquidacion] = None
    notas_liquidador: Optional[str] = None


class LiquidacionDevolver(BaseModel):
    """Payload para devolver una incapacidad de LIQUIDACION a EN_AUDITORIA."""

    observacion: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class LiquidacionResponse(BaseModel):
    """Respuesta completa de una liquidación."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incapacidad_id: UUID

    ibl: Optional[Decimal] = None
    periodo_ibl_inicio: Optional[date] = None
    periodo_ibl_fin: Optional[date] = None

    dias_autorizados: int
    fecha_inicio_autorizada: date
    fecha_fin_autorizada: date

    valor_incapacidad_temporal: Optional[Decimal] = None
    valor_aporte_patronal_pension: Optional[Decimal] = None
    valor_aporte_trabajador_pension: Optional[Decimal] = None
    valor_aporte_adicional_trabajador_pension: Optional[Decimal] = None
    valor_aporte_patronal_salud: Optional[Decimal] = None
    valor_aporte_trabajador_salud: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None

    metodo_pago: Optional[MetodoPagoLiquidacion] = None
    notas_liquidador: Optional[str] = None
    liquidador_id: Optional[UUID] = None


class BreakdownResponse(BaseModel):
    """
    Respuesta del cálculo de desglose (placeholder — fórmulas C1/C2 pendientes).

    Todos los valores de breakdown retornan None hasta confirmar con Helen.
    """

    ibl: Optional[Decimal]
    dias: int
    incapacidad_temporal: Optional[Decimal]
    aporte_patronal_pension: Optional[Decimal]
    aporte_trabajador_pension: Optional[Decimal]
    aporte_adicional_trabajador_pension: Optional[Decimal]
    aporte_patronal_salud: Optional[Decimal]
    aporte_trabajador_salud: Optional[Decimal]
    valor_total: Optional[Decimal]
    nota: str


class IblStubResponse(BaseModel):
    """Respuesta del stub de cálculo IBL desde Imaginex (integración pendiente)."""

    ibl: None = None
    nota: str = "Integración con Imaginex pendiente de especificación"
