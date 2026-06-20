"""Resultado de cada regla de auditoría evaluada sobre una Incapacidad.

A diferencia de validation_inconsistencia (solo problemas), aquí se guarda CADA regla
evaluada, incluidas las que pasan, con su booleano aprobado/no aprobado.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import BaseModel


class AuditoriaResultado(BaseModel):
    __tablename__ = "auditoria_resultado"

    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    regla: Mapped[str] = mapped_column(String(100), nullable=False, comment="Código de la regla evaluada")
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    detalle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incapacidad: Mapped["Incapacidad"] = relationship("Incapacidad", back_populates="auditoria_resultados")

    def __repr__(self) -> str:
        estado = "OK" if self.aprobado else "FAIL"
        return f"<AuditoriaResultado {self.regla} [{estado}] inc={self.incapacidad_id}>"
