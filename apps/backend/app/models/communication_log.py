"""Bitácora de intentos de integración con sistemas externos (ServiAlfa, Sicat).

Sirve como prueba de radicación y trazabilidad para auditorías.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from app.models.base import BaseModel


class CommunicationLog(BaseModel):
    __tablename__ = "communication_log"

    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    sistema: Mapped[str] = mapped_column(String(20), nullable=False, comment="SERVIALFA | SICAT")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, comment="SUCCESS | FAILURE | PENDING")
    payload_resumen: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    respuesta: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    mensaje: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incapacidad: Mapped["Incapacidad"] = relationship("Incapacidad", back_populates="communication_logs")

    def __repr__(self) -> str:
        return f"<CommunicationLog {self.sistema} [{self.estado}] inc={self.incapacidad_id}>"
