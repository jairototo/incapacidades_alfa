"""
Modelo de Afiliado - Asegurados de pólizas de salud.
"""
from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.utils.enums import TipoDocumento, EstadoAfiliado, TipoPoliza, Genero, TipoCuenta, SyncSource

if TYPE_CHECKING:
    from app.models.incapacidad import Incapacidad


class Afiliado(BaseModel):
    """
    Modelo de Afiliado para pólizas de salud.
    
    Representa a personas aseguradas que NO son empleados de empresas.
    Se identifican por número de póliza y pueden tener incapacidades de salud.
    """
    __tablename__ = "afiliado"
    
    # Identificación del afiliado
    numero_poliza: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    tipo_poliza: Mapped[str] = mapped_column(String(50), nullable=False)  # INDIVIDUAL, FAMILIAR, COLECTIVA
    
    # Datos personales
    tipo_documento: Mapped[str] = mapped_column(String(20), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    genero: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)  # M/F/O
    
    # Contacto
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    ciudad: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    departamento: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Vigencia de la póliza
    fecha_inicio_poliza: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin_poliza: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Datos bancarios para pagos
    cuenta_bancaria: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    banco: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tipo_cuenta: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # AHORROS, CORRIENTE
    
    # Estado
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVO")
    
    # Sincronización externa
    sync_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Relaciones
    incapacidades: Mapped[List["Incapacidad"]] = relationship(
        back_populates="afiliado",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Afiliado(numero_poliza='{self.numero_poliza}', nombres='{self.nombres}', apellidos='{self.apellidos}')>"
