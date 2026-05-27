"""
Modelo SQLAlchemy para Documento.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import String, BigInteger, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from apps.backend.app.models.base import BaseModel
from apps.backend.app.utils.enums import TipoDocumentoArchivo


class Documento(BaseModel):
    """Modelo de Documento adjunto a incapacidades."""
    
    __tablename__ = "documento"
    
    # Relación con incapacidad
    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Tipo de documento
    tipo_documento: Mapped[TipoDocumentoArchivo] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    # Información del archivo
    nombre_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_storage: Mapped[str] = mapped_column(String(500), nullable=False)
    bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    tamanio_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Hash para verificación de integridad
    hash_md5: Mapped[Optional[str]] = mapped_column(String(32))
    hash_sha256: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    
    # Usuario que subió el archivo
    uploaded_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id")
    )
    
    # Validación
    validado: Mapped[bool] = mapped_column(Boolean, default=False)
    observacion_validacion: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relaciones
    incapacidad: Mapped["Incapacidad"] = relationship(
        "Incapacidad",
        back_populates="documentos",
        lazy="selectin"
    )
    uploaded_by: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
        back_populates="documentos_subidos",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Documento {self.nombre_archivo} - {self.tipo_documento}>"
    
    @property
    def tamanio_mb(self) -> float:
        """Retorna el tamaño del archivo en MB."""
        return round(self.tamanio_bytes / (1024 * 1024), 2)
    
    @property
    def url_storage(self) -> str:
        """Construye la URL completa del storage."""
        return f"{self.bucket}/{self.ruta_storage}"
