"""
Modelo SQLAlchemy para PreIncapacidad.
Registro plano de radicaciones recibidas desde el portal externo,
pendientes de procesamiento por job/tarea programada.
"""
from datetime import date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Date, Numeric, Text, BigInteger, Sequence
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PreIncapacidad(BaseModel):
    """
    Registro de pre-radicación de incapacidad ARL.
    No crea una Incapacidad real — es procesada posteriormente por un job.
    """

    __tablename__ = "pre_incapacidad"

    # Número secuencial legible, inicia en 202600001
    numero_radicacion: Mapped[int] = mapped_column(
        Integer,
        Sequence("pre_incapacidad_numero_seq", start=202600001, increment=1),
        unique=True,
        nullable=False,
        index=True,
    )

    # Estado del registro
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDIENTE",
        index=True,
        comment="PENDIENTE | PROCESADA | RECHAZADA | ERROR | DEVUELTA",
    )

    # ── Solicitante (datos planos) ───────────────────────────────────────────
    solicitante_correo: Mapped[str] = mapped_column(String(255), nullable=False)
    solicitante_nombres: Mapped[str] = mapped_column(String(200), nullable=False)
    solicitante_apellidos: Mapped[Optional[str]] = mapped_column(String(200))
    solicitante_telefono: Mapped[Optional[str]] = mapped_column(String(20))

    # ── Empresa (datos planos — None si independiente) ────────────────────────
    empresa_nit: Mapped[Optional[str]] = mapped_column(String(20))
    empresa_nombre: Mapped[Optional[str]] = mapped_column(String(255))

    # ── Empleado (datos planos) ───────────────────────────────────────────────
    empleado_tipo_documento: Mapped[str] = mapped_column(String(10), nullable=False)
    empleado_numero_documento: Mapped[str] = mapped_column(String(20), nullable=False)
    empleado_nombres: Mapped[str] = mapped_column(String(200), nullable=False)
    empleado_apellidos: Mapped[Optional[str]] = mapped_column(String(200))
    empleado_email: Mapped[Optional[str]] = mapped_column(String(255))
    empleado_telefono: Mapped[Optional[str]] = mapped_column(String(20))

    # ── Datos de la incapacidad ───────────────────────────────────────────────
    tipo: Mapped[str] = mapped_column(String(10), nullable=False, default="ARL")
    tipo_enfermedad: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="ACCIDENTE_TRABAJO | ENFERMEDAD_LABORAL | ACCIDENTE_TRAYECTO",
    )
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    dias_totales: Mapped[int] = mapped_column(Integer, nullable=False)
    diagnostico_cie10: Mapped[str] = mapped_column(String(10), nullable=False)
    descripcion_diagnostico: Mapped[Optional[str]] = mapped_column(Text)
    nombre_medico: Mapped[str] = mapped_column(String(200), nullable=False)
    registro_medico: Mapped[str] = mapped_column(String(50), nullable=False)
    ips: Mapped[Optional[str]] = mapped_column(String(255))
    valor_dia: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    observaciones: Mapped[Optional[str]] = mapped_column(Text)

    # ── Trazabilidad de procesamiento ─────────────────────────────────────────
    error_procesamiento: Mapped[Optional[str]] = mapped_column(Text)

    # ── Devolución (set by internal users) ───────────────────────────────────
    motivo_devolucion: Mapped[Optional[str]] = mapped_column(Text)

    # ── Relaciones ────────────────────────────────────────────────────────────
    documentos: Mapped[List["PreDocumento"]] = relationship(
        "PreDocumento",
        back_populates="pre_incapacidad",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    validation_inconsistencias: Mapped[List["ValidationInconsistencia"]] = relationship(
        "ValidationInconsistencia",
        back_populates="pre_incapacidad",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PreIncapacidad {self.numero_radicacion} [{self.estado}]>"
