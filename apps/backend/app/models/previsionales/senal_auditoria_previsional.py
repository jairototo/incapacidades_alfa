"""
Modelo SQLAlchemy para Señal de Auditoría Previsional.

Persiste cada `Senal` (dataclass en memoria, `auditoria_rules.py`) producida
al correr las 19 reglas AB-AT sobre una fila del lote. Tabla NUEVA —
deliberadamente NO reutiliza `AuditoriaResultado` (`app/models/
auditoria_resultado.py`): ese modelo tiene FK dura a `incapacidad.id` (flujo
ARL/SALUD) con `ondelete=CASCADE` y `back_populates` en `Incapacidad`, así
que apuntarlo aquí exigiría tocar el flujo ARL. También difieren en forma:
`AuditoriaResultado.aprobado` es un booleano (regla pasa/no pasa);
`SenalAuditoriaPrevisional.valor` es heterogéneo (`Senal.valor: Any` — date,
dict, bool, str o list), por eso es JSONB y no un booleano.

Relación: MANY-TO-ONE con IncapacidadPrevisional (CASCADE DELETE).
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SenalAuditoriaPrevisional(BaseModel):
    """
    Resultado persistido de UNA regla AB-AT evaluada sobre una fila del
    lote (una `Senal` de `auditoria_rules.py`).
    """

    __tablename__ = "senales_auditoria_previsionales"

    __table_args__ = (
        CheckConstraint(
            "estado IN ('OK', 'ALERTA', 'PENDIENTE', 'INFO')",
            name="chk_senal_auditoria_previsional_estado",
        ),
    )

    incapacidad_previsional_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidades_previsionales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Incapacidad previsional sobre la que se evaluó la regla",
    )

    codigo: Mapped[str] = mapped_column(
        String(2), nullable=False, comment="Código de columna de la regla, 'AB'..'AT' (Senal.codigo)"
    )
    nombre: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Nombre descriptivo de la regla (Senal.nombre)"
    )
    estado: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="OK|ALERTA|PENDIENTE|INFO — mismos 4 valores que EstadoSenal en auditoria_rules.py",
    )
    valor: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Senal.valor serializado — heterogéneo: date, dict, bool, str o list",
    )
    detalle: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Senal.detalle — explicación libre del resultado"
    )

    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    incapacidad_previsional: Mapped["IncapacidadPrevisional"] = relationship(
        "IncapacidadPrevisional",
        back_populates="senales_auditoria",
        foreign_keys=[incapacidad_previsional_id],
    )

    def __repr__(self) -> str:
        return (
            f"<SenalAuditoriaPrevisional("
            f"id={self.id}, "
            f"codigo={self.codigo}, "
            f"estado={self.estado}, "
            f"incapacidad_previsional_id={self.incapacidad_previsional_id}"
            f")>"
        )
