"""
Modelo SQLAlchemy para Solicitud Previsional.

Histórico de incapacidades ya radicadas en el sistema externo ARPIS/AFP,
keyed por `identificacion`. Usado como fuente de referencia por las reglas
AE (día 181 AFP) y AG (fecha CRIE) del motor de auditoría — ver
`auditoria_rules.SolicitudRef`.
"""
from datetime import date
from typing import Optional

from sqlalchemy import Date, String, Text

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SolicitudPrevisional(BaseModel):
    """
    Solicitud previsional histórica (AFP/ARPIS), keyed por `identificacion`.

    Refleja lo que el sistema externo ya tiene radicado para un afiliado —
    se usa como referencia de solo lectura al construir el
    `ContextoAuditoria` de un lote (nunca se modifica desde el motor de
    reglas).
    """

    __tablename__ = "solicitudes_previsionales"

    identificacion: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="Número de documento del afiliado"
    )
    radicado: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Número de radicado de la solicitud en ARPIS"
    )
    tipo_ingreso: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="INICIAL|PRORROGA|TUTELA_I|TUTELA_P|AJUSTE"
    )
    fecha_inicial: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha inicial de la incapacidad solicitada"
    )
    fecha_final: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha final de la incapacidad solicitada"
    )
    dia_181: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Día 181 según la AFP (regla AE, base de AF)"
    )
    fecha_crie: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha CRIE reportada por la AFP (regla AG)"
    )
    observacion: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Observación libre de la solicitud original"
    )

    def __repr__(self) -> str:
        return (
            f"<SolicitudPrevisional("
            f"id={self.id}, "
            f"identificacion={self.identificacion}, "
            f"radicado={self.radicado}"
            f")>"
        )
