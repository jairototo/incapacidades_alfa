"""
Modelo SQLAlchemy para Siniestro (Accidente Laboral).
"""
from datetime import date, time, datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import String, Date, Time, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM as PGEnum

from app.models.base import BaseModel
from app.utils.enums import TipoSiniestro, GravedadSiniestro, EstadoSiniestro, SyncSource


class Siniestro(BaseModel):
    """Modelo de Siniestro (Accidente Laboral)."""
    
    __tablename__ = "siniestro"
    
    # Campos principales
    numero_siniestro: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    empleado_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("empleado.id"), nullable=False)
    empresa_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("empresa.id"), nullable=False)
    
    # Información del siniestro
    fecha_siniestro: Mapped[date] = mapped_column(Date, nullable=False)
    hora_siniestro: Mapped[Optional[time]] = mapped_column(Time)
    tipo_siniestro: Mapped[TipoSiniestro] = mapped_column(
        PGEnum(TipoSiniestro, name='tiposiniestro', create_type=False),
        nullable=False
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    lugar_ocurrencia: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Detalles de la lesión
    parte_cuerpo_afectada: Mapped[Optional[str]] = mapped_column(String(100))
    naturaleza_lesion: Mapped[Optional[str]] = mapped_column(String(100))
    agente_causante: Mapped[Optional[str]] = mapped_column(String(255))
    gravedad: Mapped[GravedadSiniestro] = mapped_column(
        PGEnum(GravedadSiniestro, name='gravedadsiniestro', create_type=False),
        nullable=False,
        default=GravedadSiniestro.LEVE
    )
    
    # Información adicional
    testigos: Mapped[Optional[str]] = mapped_column(Text)
    requirio_hospitalizacion: Mapped[bool] = mapped_column(Boolean, default=False)
    dias_estimados_incapacidad: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Estado y seguimiento
    estado: Mapped[EstadoSiniestro] = mapped_column(
        PGEnum(EstadoSiniestro, name='estadosiniestro', create_type=False),
        nullable=False,
        default=EstadoSiniestro.REPORTADO
    )
    fecha_reporte: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    reportado_por: Mapped[Optional[str]] = mapped_column(String(255))
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    
    # Sincronización con sistema externo
    sync_source: Mapped[Optional[SyncSource]] = mapped_column(
        PGEnum(SyncSource, name='syncsource', create_type=False)
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relaciones
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="siniestros", lazy="selectin")
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="siniestros", lazy="selectin")
    incapacidades: Mapped[list["Incapacidad"]] = relationship(
        "Incapacidad",
        back_populates="siniestro",
        foreign_keys="Incapacidad.siniestro_id",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Siniestro {self.numero_siniestro} - {self.empleado_id}>"
