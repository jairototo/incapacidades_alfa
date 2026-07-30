"""
Modelo SQLAlchemy para Lote Previsional.

Un lote representa una carga masiva (archivo Excel/AFP) de incapacidades
previsionales a auditar. Agrupa N `IncapacidadPrevisional` y funciona como
la unidad de trabajo del flujo CARGADO -> EN_AUDITORIA -> AUDITADO ->
LIQUIDADO -> RESPONDIDO.

Relación: ONE-TO-MANY con IncapacidadPrevisional (CASCADE DELETE — borrar
un lote borra sus incapacidades y, en cadena, los periodos de esas
incapacidades vía el CASCADE de `periodos_previsionales`).
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LotePrevisional(BaseModel):
    """
    Lote de carga de incapacidades previsionales.

    Cada fila representa un archivo Excel cargado por un auditor, con su
    estado de procesamiento y totales de filas/incapacidades resultantes.
    """

    __tablename__ = "lotes_previsionales"

    __table_args__ = (
        CheckConstraint(
            "estado IN ('CARGADO', 'EN_AUDITORIA', 'AUDITADO', 'LIQUIDADO', 'RESPONDIDO')",
            name="chk_lote_previsional_estado",
        ),
    )

    nombre_archivo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre del archivo Excel cargado (p.ej. RADICADOS_AUDITORIA_20260706.xlsx)",
    )

    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="CARGADO",
        server_default="CARGADO",
        comment="Estado del lote en el flujo CARGADO->EN_AUDITORIA->AUDITADO->LIQUIDADO->RESPONDIDO",
    )

    fecha_cargue: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Fecha/hora en que se cargó el archivo (distinta de created_at si se reprocesa)",
    )

    cargado_por_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id", ondelete="SET NULL"),
        nullable=True,
        comment="Usuario que cargó el archivo del lote",
    )

    total_filas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total de filas leídas del archivo Excel (incluye filas con errores de parseo)",
    )

    total_incapacidades: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total de incapacidades previsionales creadas exitosamente a partir del lote",
    )

    observaciones: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Notas libres sobre el procesamiento del lote",
    )

    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    incapacidades: Mapped[list["IncapacidadPrevisional"]] = relationship(
        "IncapacidadPrevisional",
        back_populates="lote",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<LotePrevisional("
            f"id={self.id}, "
            f"nombre_archivo={self.nombre_archivo!r}, "
            f"estado={self.estado}, "
            f"total_incapacidades={self.total_incapacidades}"
            f")>"
        )
