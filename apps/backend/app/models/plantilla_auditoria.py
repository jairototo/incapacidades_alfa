"""
Modelo SQLAlchemy para Plantilla de Auditoría.

Almacena una plantilla de texto reutilizable que el auditor llena
para generar líneas de autorización y notas para Arpis.

Relación ONE-TO-ONE con Incapacidad.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PlantillaAuditoria(BaseModel):
    """
    Plantilla de auditoría por incapacidad.

    Almacena datos estructurados que el auditor completa manualmente
    y que el sistema convierte en texto formateado para pegar en Arpis.

    Relación: ONE-TO-ONE con Incapacidad (unique=True en incapacidad_id).
    """

    __tablename__ = "plantilla_auditoria"

    # Relación con incapacidad (ONE-TO-ONE, CASCADE DELETE)
    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="ID de la incapacidad a la que pertenece esta plantilla",
    )

    # Canal de recepción del documento (Portal / Imaginex / Onbase)
    canal_recepcion: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Canal por el que se recibió la incapacidad: Portal / Imaginex / Onbase",
    )

    # IPS que emitió el documento
    nombre_ips: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Nombre de la IPS que emitió la incapacidad",
    )

    # Fecha de emisión del documento físico
    fecha_emision_incapacidad: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Fecha de emisión del documento de incapacidad",
    )

    # Días autorizados y rango
    dias_autorizados: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Número de días autorizados por el auditor",
    )

    fecha_inicio_autorizada: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Fecha de inicio del período autorizado",
    )

    fecha_fin_autorizada: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Fecha de fin del período autorizado",
    )

    # Diagnóstico
    diagnostico_cie10: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Código CIE-10 del diagnóstico",
    )

    descripcion_cie10: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descripción del diagnóstico CIE-10",
    )

    # Médico tratante
    nombre_medico: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Nombre del médico que emitió la incapacidad",
    )

    especialidad_medico: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Especialidad del médico tratante",
    )

    # Línea de autorización auto-generada
    linea_autorizacion: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Auto-generado: 'Se autoriza pago por X días desde ... hasta ...'",
    )

    # Aprobación parcial: datos del documento físico vs. rango pagado
    dias_documento: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Total de días en el documento físico (para aprobación parcial)",
    )

    rango_pagado_inicio: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Inicio del rango efectivamente pagado (aprobación parcial)",
    )

    rango_pagado_fin: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Fin del rango efectivamente pagado (aprobación parcial)",
    )

    # Auditor que completó la plantilla
    auditado_por_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id"),
        nullable=True,
        comment="ID del usuario auditor que completó la plantilla",
    )

    # Relaciones
    incapacidad: Mapped["Incapacidad"] = relationship(
        "Incapacidad",
        back_populates="plantilla_auditoria",
        foreign_keys=[incapacidad_id],
    )

    auditado_por: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
        foreign_keys=[auditado_por_id],
    )

    def __repr__(self) -> str:
        return (
            f"<PlantillaAuditoria("
            f"id={self.id}, "
            f"incapacidad_id={self.incapacidad_id}, "
            f"dias_autorizados={self.dias_autorizados}"
            f")>"
        )
