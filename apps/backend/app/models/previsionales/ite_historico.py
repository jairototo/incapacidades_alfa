"""
Modelo SQLAlchemy para ITE Histórico.

Histórico de pagos de Incapacidad Temporal por Enfermedad (ITE) ya
realizados, usado para detectar posible doble pago (regla AT del motor de
auditoría: `ALERTA` si `(identificacion, fecha_inicial)` ya existe aquí —
ver `auditoria_rules.regla_at_doble_pago` y `ContextoAuditoria.ite_por_clave`).
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Index, Numeric, String

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class IteHistorico(BaseModel):
    """
    Registro histórico de pago de ITE, keyed por `identificacion` +
    `fecha_inicial` para respaldar la detección de doble pago (regla AT).
    """

    __tablename__ = "ite_historico"

    __table_args__ = (
        Index(
            "ix_ite_historico_ident_fecha_inicial",
            "identificacion",
            "fecha_inicial",
        ),
    )

    identificacion: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Número de documento del afiliado"
    )
    fecha_inicial: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Fecha inicial del periodo de ITE ya pagado"
    )
    fecha_final: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha final del periodo de ITE ya pagado"
    )
    valor_pagado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Valor pagado en ese periodo"
    )
    fecha_pago: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha en que se realizó el pago"
    )

    def __repr__(self) -> str:
        return (
            f"<IteHistorico("
            f"id={self.id}, "
            f"identificacion={self.identificacion}, "
            f"fecha_inicial={self.fecha_inicial}"
            f")>"
        )
