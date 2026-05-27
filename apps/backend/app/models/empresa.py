"""
Modelo SQLAlchemy para Empresa.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from apps.backend.app.models.base import BaseModel
from apps.backend.app.utils.enums import EstadoEmpresa, TipoEmpresa, SyncSource


class Empresa(BaseModel):
    """Modelo de Empresa afiliada."""
    
    __tablename__ = "empresa"
    
    # Campos de identificación
    nit: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Información de contacto
    email_contacto: Mapped[Optional[str]] = mapped_column(String(255))
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    direccion: Mapped[Optional[str]] = mapped_column(Text)
    ciudad: Mapped[Optional[str]] = mapped_column(String(100))
    departamento: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Tipo y estado
    tipo_empresa: Mapped[Optional[TipoEmpresa]] = mapped_column(String(50))
    estado: Mapped[EstadoEmpresa] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoEmpresa.ACTIVA,
        index=True
    )
    
    # Sincronización externa
    sync_source: Mapped[Optional[SyncSource]] = mapped_column(String(50))
    external_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Metadata adicional (usar name='metadata' porque es palabra reservada)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    
    # Relaciones
    empleados: Mapped[List["Empleado"]] = relationship(
        "Empleado",
        back_populates="empresa",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    incapacidades: Mapped[List["Incapacidad"]] = relationship(
        "Incapacidad",
        back_populates="empresa",
        lazy="selectin"
    )
    siniestros: Mapped[List["Siniestro"]] = relationship(
        "Siniestro",
        back_populates="empresa",
        lazy="selectin"
    )
    usuarios: Mapped[List["Usuario"]] = relationship(
        "Usuario",
        back_populates="empresa",
        lazy="noload"
    )
    
    def __repr__(self) -> str:
        return f"<Empresa {self.nit} - {self.razon_social}>"
