"""
Modelo SQLAlchemy para PreDocumento.
Archivos adjuntos asociados a una PreIncapacidad.
Garantiza que ningún documento se pierda durante la radicación del portal externo.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import String, BigInteger, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PreDocumento(BaseModel):
    """Documento adjunto a una pre-incapacidad del portal externo."""

    __tablename__ = "pre_documento"

    # Relación con pre_incapacidad (CASCADE DELETE)
    pre_incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pre_incapacidad.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Clasificación del documento
    tipo_documento: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="INCAPACIDAD_MEDICA | HISTORIA_CLINICA | SOPORTE_ADICIONAL",
    )

    # Información del archivo
    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_storage: Mapped[str] = mapped_column(String(500), nullable=False)
    bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanio_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Estado de la subida — permite detectar fallos para reintentos
    estado_subida: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="OK",
        comment="OK | ERROR",
    )
    error_subida: Mapped[Optional[str]] = mapped_column(Text)

    # ── Relaciones ────────────────────────────────────────────────────────────
    pre_incapacidad: Mapped["PreIncapacidad"] = relationship(
        "PreIncapacidad",
        back_populates="documentos",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PreDocumento {self.nombre_original} [{self.tipo_documento}]>"

    @property
    def tamanio_mb(self) -> float:
        return round(self.tamanio_bytes / (1024 * 1024), 2)
