"""
Modelo SQLAlchemy para Empleado.
"""
from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from sqlalchemy import String, Date, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from apps.backend.app.models.base import BaseModel
from apps.backend.app.utils.enums import TipoDocumento, EstadoEmpleado, TipoCuenta, Genero, SyncSource


class Empleado(BaseModel):
    """Modelo de Empleado."""
    
    __tablename__ = "empleado"
    
    # Relación con empresa
    empresa_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("empresa.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Documento de identidad
    numero_documento: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo_documento: Mapped[TipoDocumento] = mapped_column(String(10), nullable=False)
    
    # Información personal
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date)
    genero: Mapped[Optional[Genero]] = mapped_column(String(10))
    
    # Información laboral
    cargo: Mapped[Optional[str]] = mapped_column(String(100))
    area: Mapped[Optional[str]] = mapped_column(String(100))
    fecha_ingreso: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_retiro: Mapped[Optional[date]] = mapped_column(Date)
    salario_base: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    
    # Información bancaria
    cuenta_bancaria: Mapped[Optional[str]] = mapped_column(String(50))
    banco: Mapped[Optional[str]] = mapped_column(String(100))
    tipo_cuenta: Mapped[Optional[TipoCuenta]] = mapped_column(String(20))
    
    # Estado
    estado: Mapped[EstadoEmpleado] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoEmpleado.ACTIVO,
        index=True
    )
    
    # Sincronización externa
    sync_source: Mapped[Optional[SyncSource]] = mapped_column(String(50))
    external_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Metadata adicional (usar name='metadata' porque es palabra reservada)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    
    # Relaciones
    empresa: Mapped["Empresa"] = relationship(
        "Empresa",
        back_populates="empleados",
        lazy="selectin"
    )
    incapacidades: Mapped[List["Incapacidad"]] = relationship(
        "Incapacidad",
        back_populates="empleado",
        lazy="selectin"
    )
    siniestros: Mapped[List["Siniestro"]] = relationship(
        "Siniestro",
        back_populates="empleado",
        lazy="selectin"
    )
    usuario: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
        back_populates="empleado",
        uselist=False,
        lazy="noload"
    )
    
    def __repr__(self) -> str:
        return f"<Empleado {self.tipo_documento} {self.numero_documento} - {self.nombres} {self.apellidos}>"
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del empleado."""
        return f"{self.nombres} {self.apellidos}"
