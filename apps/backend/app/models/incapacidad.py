"""
Modelo SQLAlchemy para Incapacidad.

Soporta dos tipos de incapacidades:
- ARL: Relacionadas con empleados de empresas y siniestros laborales
- SALUD: Relacionadas con afiliados de pólizas de salud (sin siniestro)
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Date, Numeric, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM as PGEnum

from app.models.base import BaseModel
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


class Incapacidad(BaseModel):
    """
    Modelo de Incapacidad.
    
    - ARL: Requiere empleado_id y empresa_id, puede tener siniestro_id
    - SALUD: Requiere afiliado_id, NO tiene empleado_id, empresa_id ni siniestro_id
    """
    
    __tablename__ = "incapacidad"
    
    __table_args__ = (
        CheckConstraint(
            "(tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL) OR "
            "(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)",
            name="check_tipo_incapacidad_relacion"
        ),
    )
    
    # Campos principales
    numero: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Relaciones según tipo (ARL o SALUD)
    empleado_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("empleado.id"), nullable=True)
    empresa_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("empresa.id"), nullable=True)
    afiliado_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("afiliado.id"), nullable=True)
    
    # Solicitante (persona que radica la incapacidad)
    solicitante_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("solicitante.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Solicitante que radicó la incapacidad"
    )
    
    # Siniestro (solo para ARL)
    siniestro_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("siniestro.id"))
    numero_siniestro: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Tipo y subtipo
    tipo: Mapped[TipoIncapacidad] = mapped_column(
        PGEnum(TipoIncapacidad, name='tipoincapacidad', create_type=False),
        nullable=False
    )
    subtipo: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Fechas
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    dias_totales: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Diagnóstico
    diagnostico_cie10: Mapped[Optional[str]] = mapped_column(String(10))
    descripcion_diagnostico: Mapped[Optional[str]] = mapped_column(Text)
    
    # Datos del médico tratante
    nombre_medico: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Nombre completo del médico tratante"
    )
    registro_medico: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Registro médico profesional"
    )
    
    # Entidades de salud
    eps: Mapped[Optional[str]] = mapped_column(String(255))
    ips: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Valores
    valor_dia: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    valor_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2))
    
    # Estado y observaciones
    estado: Mapped[EstadoIncapacidad] = mapped_column(
        PGEnum(EstadoIncapacidad, name='estadoincapacidad', create_type=False),
        nullable=False,
        default=EstadoIncapacidad.RADICADA
    )
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    motivo_rechazo: Mapped[Optional[str]] = mapped_column(Text)
    
    # Referencias a usuarios
    radicado_por_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuario.id"))
    auditado_por_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuario.id"))
    aprobado_por_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuario.id"))
    
    # Fechas de proceso
    fecha_radicacion: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    fecha_auditoria: Mapped[Optional[datetime]]
    fecha_aprobacion: Mapped[Optional[datetime]]
    fecha_rechazo: Mapped[Optional[datetime]]
    
    # Prioridad
    prioridad: Mapped[Prioridad] = mapped_column(
        PGEnum(Prioridad, name='prioridad', create_type=False),
        nullable=False,
        default=Prioridad.NORMAL
    )
    
    # Relaciones
    empleado: Mapped[Optional["Empleado"]] = relationship("Empleado", back_populates="incapacidades")
    empresa: Mapped[Optional["Empresa"]] = relationship("Empresa", back_populates="incapacidades")
    afiliado: Mapped[Optional["Afiliado"]] = relationship("Afiliado", back_populates="incapacidades")
    solicitante: Mapped[Optional["Solicitante"]] = relationship("Solicitante", back_populates="incapacidades")
    siniestro: Mapped[Optional["Siniestro"]] = relationship("Siniestro", back_populates="incapacidades", foreign_keys=[siniestro_id])
    documentos: Mapped[list["Documento"]] = relationship("Documento", back_populates="incapacidad", cascade="all, delete-orphan")
    # Nota: historial_estados ahora es polimórfico - usar historial_estado_service.get_incapacidad_history()
    ordenes_pago: Mapped[list["OrdenPago"]] = relationship("OrdenPago", back_populates="incapacidad")
    datos_aprobados: Mapped[Optional["AuditoriaDatosAprobados"]] = relationship(
        "AuditoriaDatosAprobados",
        back_populates="incapacidad",
        uselist=False,
        cascade="all, delete-orphan"
    )

    validation_inconsistencias: Mapped[list["ValidationInconsistencia"]] = relationship(
        "ValidationInconsistencia",
        back_populates="incapacidad",
        cascade="all, delete-orphan"
    )

    radicado_por: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[radicado_por_id])
    auditado_por: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[auditado_por_id])
    aprobado_por: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[aprobado_por_id])
    
    def __repr__(self) -> str:
        return f"<Incapacidad {self.numero} - {self.estado}>"
