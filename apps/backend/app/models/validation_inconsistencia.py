"""
Modelo para almacenar inconsistencias de validación encontradas
durante la promoción de pre-incapacidades.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import BaseModel


class ValidationInconsistencia(BaseModel):
    """
    Registro de inconsistencias encontradas en validación de pre-incapacidades.

    Puede estar vinculada a:
    - pre_incapacidad_id: durante validación previa a creación
    - incapacidad_id: después de creación si se encuentran issues
    """

    __tablename__ = "validation_inconsistencia"

    __table_args__ = (
        Index("idx_pre_incapacidad_id", "pre_incapacidad_id"),
        Index("idx_incapacidad_id", "incapacidad_id"),
        Index("idx_categoria", "categoria"),
        Index("idx_severidad", "severidad"),
    )

    # Relación con pre-incapacidad (siempre presente)
    pre_incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pre_incapacidad.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relación con incapacidad (opcional, si se creó a pesar del issue)
    incapacidad_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=True
    )

    # Categoría de validación
    categoria: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="FIELD_VALIDATION | BUSINESS_RULE | FRAUD_ALERT | INTEGRATION_CHECK"
    )

    # Severidad del issue
    severidad: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="WARNING",
        comment="ERROR | WARNING | INFO"
    )

    # Código del issue (máquina-readable)
    codigo: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Descripción legible
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)

    # Campo afectado (si aplica)
    campo_afectado: Mapped[Optional[str]] = mapped_column(String(100))

    # Valor encontrado
    valor_encontrado: Mapped[Optional[str]] = mapped_column(Text)

    # Valor esperado
    valor_esperado: Mapped[Optional[str]] = mapped_column(Text)

    # Fecha de detección
    fecha_deteccion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Relaciones
    pre_incapacidad: Mapped["PreIncapacidad"] = relationship(
        "PreIncapacidad",
        back_populates="validation_inconsistencias"
    )
    incapacidad: Mapped[Optional["Incapacidad"]] = relationship(
        "Incapacidad",
        back_populates="validation_inconsistencias",
        foreign_keys=[incapacidad_id]
    )

    def __repr__(self) -> str:
        return f"<ValidationInconsistencia [{self.severidad}] {self.codigo}>"
