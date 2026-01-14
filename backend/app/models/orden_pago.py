"""
Modelo SQLAlchemy para OrdenPago.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import String, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP

from app.models.base import BaseModel
from app.utils.enums import BeneficiarioTipo, EstadoOrdenPago, MetodoPago, TipoCuenta


class OrdenPago(BaseModel):
    """Modelo de Orden de Pago."""
    
    __tablename__ = "orden_pago"
    
    # Número único de orden
    numero_orden: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Relación con incapacidad
    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidad.id"),
        nullable=False,
        index=True
    )
    
    # Información del beneficiario
    beneficiario_tipo: Mapped[BeneficiarioTipo] = mapped_column(String(20), nullable=False)
    beneficiario_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    beneficiario_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    beneficiario_documento: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Información bancaria
    cuenta_bancaria: Mapped[Optional[str]] = mapped_column(String(50))
    banco: Mapped[Optional[str]] = mapped_column(String(100))
    tipo_cuenta: Mapped[Optional[TipoCuenta]] = mapped_column(String(20))
    
    # Monto a pagar
    valor_pagar: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Estado y fechas
    estado_pago: Mapped[EstadoOrdenPago] = mapped_column(
        String(30),
        nullable=False,
        default=EstadoOrdenPago.GENERADA,
        index=True
    )
    fecha_generacion: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    fecha_pago: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    fecha_anulacion: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    
    # Información del pago
    metodo_pago: Mapped[Optional[MetodoPago]] = mapped_column(String(50))
    referencia_pago: Mapped[Optional[str]] = mapped_column(String(100))
    comprobante_ruta: Mapped[Optional[str]] = mapped_column(String(500))
    motivo_anulacion: Mapped[Optional[str]] = mapped_column(Text)
    
    # Usuarios que intervinieron
    creado_por_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id")
    )
    aprobado_por_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id")
    )
    
    # Relaciones
    incapacidad: Mapped["Incapacidad"] = relationship(
        "Incapacidad",
        back_populates="ordenes_pago",
        lazy="selectin"
    )
    creado_por: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
        foreign_keys=[creado_por_id],
        back_populates="ordenes_pago_creadas",
        lazy="selectin"
    )
    aprobado_por: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
        foreign_keys=[aprobado_por_id],
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<OrdenPago {self.numero_orden} - {self.estado_pago}>"
    
    @property
    def esta_pagada(self) -> bool:
        """Verifica si la orden ya fue pagada."""
        return self.estado_pago == EstadoOrdenPago.PAGADA
    
    @property
    def esta_anulada(self) -> bool:
        """Verifica si la orden fue anulada."""
        return self.estado_pago == EstadoOrdenPago.ANULADA
    
    @property
    def puede_pagar(self) -> bool:
        """Verifica si la orden puede ser pagada."""
        return self.estado_pago in [EstadoOrdenPago.GENERADA, EstadoOrdenPago.APROBADA]
