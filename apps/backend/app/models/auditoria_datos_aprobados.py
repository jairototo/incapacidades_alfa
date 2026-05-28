"""
Modelo SQLAlchemy para Auditoría Datos Aprobados.

Almacena los datos modificados/aprobados por el auditor durante la auditoría
cuando los valores aprobados difieren de los solicitados (aprobación parcial).
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import String, Date, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import BaseModel


class AuditoriaDatosAprobados(BaseModel):
    """
    Datos aprobados por el auditor durante la auditoría.
    
    Esta tabla almacena los valores finales aprobados cuando difieren
    de los valores solicitados originalmente en la incapacidad.
    
    Relación: ONE-TO-ONE con Incapacidad
    """
    
    __tablename__ = "auditoria_datos_aprobados"
    
    __table_args__ = (
        UniqueConstraint('incapacidad_id', name='uq_auditoria_datos_incapacidad'),
    )
    
    # Relación con incapacidad (ONE-TO-ONE)
    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="ID de la incapacidad auditada"
    )
    
    # Fechas aprobadas
    fecha_inicio_aprobada: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Fecha de inicio aprobada por el auditor"
    )
    
    fecha_fin_aprobada: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Fecha de fin aprobada por el auditor"
    )
    
    dias_aprobados: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Cantidad de días aprobados (calculados automáticamente)"
    )
    
    # Diagnóstico aprobado
    cie10_aprobado: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Código CIE-10 aprobado por el auditor"
    )
    
    diagnostico_aprobado: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Descripción del diagnóstico aprobado"
    )
    
    # Observación del auditor
    observacion_auditoria: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Observaciones del auditor justificando las modificaciones"
    )
    
    # Auditoría
    auditado_por_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id", ondelete="RESTRICT"),
        nullable=False,
        comment="ID del usuario auditor que aprobó estos datos"
    )
    
    fecha_auditoria: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="Fecha y hora de la auditoría"
    )
    
    # Relaciones
    incapacidad: Mapped["Incapacidad"] = relationship(
        "Incapacidad",
        back_populates="datos_aprobados",
        foreign_keys=[incapacidad_id],
        lazy="selectin"
    )
    
    auditado_por: Mapped["Usuario"] = relationship(
        "Usuario",
        foreign_keys=[auditado_por_id],
        lazy="selectin"
    )
    
    def __repr__(self):
        return (
            f"<AuditoriaDatosAprobados("
            f"id={self.id}, "
            f"incapacidad_id={self.incapacidad_id}, "
            f"dias_aprobados={self.dias_aprobados}, "
            f"auditado_por_id={self.auditado_por_id}"
            f")>"
        )
