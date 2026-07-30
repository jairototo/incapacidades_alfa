"""
Modelo SQLAlchemy para Incapacidad Previsional.

Fila individual de un lote de auditoría previsional (AFP): datos crudos de
carga (cols A-AA del excel de la aseguradora) más los campos de auditoría
que un `AUDITOR_PREVISIONALES` humano agrega (aval, motivo_no_aval, etc.)

Contratos NO negociables heredados de `auditoria_rules.py` (Task 1.4):
- `aval` NUNCA se autocalcula. Es nullable, sin default, y solo lo cambia
  una acción explícita de un auditor humano.
- `prorroga_de_id` / `incapacidad_origen_id` son auto-FK: encadenamiento de
  prórrogas (ver `encadenar_prorrogas`) y detección de duplicados internos
  respectivamente. Ninguno se resuelve "silenciosamente" con heurísticas.

Relación: MANY-TO-ONE con LotePrevisional (CASCADE DELETE). ONE-TO-MANY con
PeriodoPrevisional y SenalAuditoriaPrevisional (ambas CASCADE DELETE).
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class IncapacidadPrevisional(BaseModel):
    """
    Incapacidad previsional (AFP) dentro de un lote de auditoría.

    Datos crudos de carga (identificación, fechas, tipo de ingreso, etc.)
    más los resultados de auditoría (aval, valor auditado) que se agregan
    después de correr el motor de reglas AB-AT.
    """

    __tablename__ = "incapacidades_previsionales"

    __table_args__ = (
        CheckConstraint(
            "aval IN ('SI', 'NO')",
            name="chk_incapacidad_previsional_aval",
        ),
        CheckConstraint(
            "tipo_ingreso IS NULL OR tipo_ingreso IN "
            "('INICIAL', 'PRORROGA', 'TUTELA_I', 'TUTELA_P', 'AJUSTE')",
            name="chk_incapacidad_previsional_tipo_ingreso",
        ),
        CheckConstraint(
            "estado IN ('SIN_SINIESTRO', 'CON_SINIESTRO', 'EN_AUDITORIA', "
            "'AVALADO', 'NO_AVALADO', 'LIQUIDADO', 'PAGADO')",
            name="chk_incapacidad_previsional_estado",
        ),
        Index(
            "ix_incapacidades_previsionales_lote_ident_fecha",
            "lote_id",
            "identificacion",
            "fecha_inicial",
        ),
    )

    # -------------------------------------------------------------------------
    # Relación con el lote
    # -------------------------------------------------------------------------
    lote_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lotes_previsionales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Lote de carga al que pertenece esta incapacidad",
    )

    # -------------------------------------------------------------------------
    # Datos crudos de carga (cols A-AA del excel AFP)
    # -------------------------------------------------------------------------
    tipo_identificacion: Mapped[Optional[str]] = mapped_column(
        String(5), nullable=True, comment="Tipo de documento del afiliado (CC, CE, etc.)"
    )
    identificacion: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True, comment="Número de documento del afiliado"
    )
    radicado: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Número de radicado tal como llega del archivo AFP"
    )
    radicado_normalizado: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True,
        comment="Radicado normalizado (ver normalizar_radicado en arpis_export.py) — 16 dígitos",
    )
    tipo_ingreso: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="INICIAL|PRORROGA|TUTELA_I|TUTELA_P|AJUSTE (ver mapear_tipo_ingreso)",
    )
    fecha_inicial: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, index=True, comment="Fecha inicial de la incapacidad"
    )
    fecha_final: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha final de la incapacidad"
    )
    dia_181_alfa: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Día 181 auditado (Alfa) — usado por regla AB, distinto del de AFP"
    )
    dia_181_afp: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Día 181 según la AFP — usado por reglas AE/AL"
    )
    dia_181_arpis: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Día 181 según ARPIS — comparado contra dia_181_afp en regla AL"
    )
    fecha_crie: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha CRIE de la solicitud AFP — usada por regla AG"
    )
    fecha_radicacion_afp: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha de radicación ante la AFP"
    )
    fecha_radicacion_alfa: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha de radicación interna (Alfa)"
    )
    numero_siniestro: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Número de siniestro asociado (regla AM-AP, AR)"
    )
    valor_afp: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Valor reportado por la AFP (regla AR, base de diferencia_valor_afp)"
    )
    cie10: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Primer código CIE10 de la incapacidad"
    )
    observacion: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Observación AFP cruda (fuente de 'Rad No. ' cuando el radicado no es numérico)"
    )
    observacion_causal: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Observación de la causal de excepción (tutelas)"
    )

    # -------------------------------------------------------------------------
    # Resultado de auditoría (agregado por un AUDITOR_PREVISIONALES humano)
    # -------------------------------------------------------------------------
    aval: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
        comment="'SI'/'NO' — jamás se autocalcula (regla AC); solo lo define un auditor humano",
    )
    motivo_no_aval: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Motivo cuando aval='NO'"
    )
    usuario_auditoria_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id"),
        nullable=True,
        comment="Usuario (AUDITOR_PREVISIONALES) que definió el aval",
    )
    fecha_auditoria: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, comment="Fecha/hora en que se definió el aval"
    )

    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SIN_SINIESTRO",
        server_default="SIN_SINIESTRO",
        comment="SIN_SINIESTRO|CON_SINIESTRO|EN_AUDITORIA|AVALADO|NO_AVALADO|LIQUIDADO|PAGADO",
    )

    # -------------------------------------------------------------------------
    # Encadenamiento de prórrogas y deduplicación interna
    # -------------------------------------------------------------------------
    prorroga_de_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidades_previsionales.id", ondelete="SET NULL"),
        nullable=True,
        comment="Incapacidad previa de la que esta es prórroga/tutela/ajuste (ver encadenar_prorrogas)",
    )
    incapacidad_origen_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidades_previsionales.id", ondelete="SET NULL"),
        nullable=True,
        comment="Incapacidad original de la que esta es duplicado interno (ver es_duplicado_interno)",
    )
    es_duplicado_interno: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True si esta fila es un duplicado interno de otra fila del mismo lote (regla AD)",
    )

    # -------------------------------------------------------------------------
    # Resultado de liquidación y comparación contra AFP
    # -------------------------------------------------------------------------
    valor_auditado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Valor calculado por liquidacion_previsional.calcular_valor()"
    )
    diferencia_valor_afp: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="valor_auditado - valor_afp (glosa potencial)"
    )

    # -------------------------------------------------------------------------
    # Errores de carga
    # -------------------------------------------------------------------------
    errores_carga: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Errores de parseo tolerante capturados durante la carga (CeldaInvalidaError por columna)",
    )

    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    lote: Mapped["LotePrevisional"] = relationship(
        "LotePrevisional",
        back_populates="incapacidades",
        foreign_keys=[lote_id],
    )

    periodos: Mapped[list["PeriodoPrevisional"]] = relationship(
        "PeriodoPrevisional",
        back_populates="incapacidad",
        cascade="all, delete-orphan",
        order_by="PeriodoPrevisional.orden",
    )

    senales_auditoria: Mapped[list["SenalAuditoriaPrevisional"]] = relationship(
        "SenalAuditoriaPrevisional",
        back_populates="incapacidad_previsional",
        cascade="all, delete-orphan",
    )

    prorroga_de: Mapped[Optional["IncapacidadPrevisional"]] = relationship(
        "IncapacidadPrevisional",
        remote_side="IncapacidadPrevisional.id",
        foreign_keys=[prorroga_de_id],
    )

    incapacidad_origen: Mapped[Optional["IncapacidadPrevisional"]] = relationship(
        "IncapacidadPrevisional",
        remote_side="IncapacidadPrevisional.id",
        foreign_keys=[incapacidad_origen_id],
    )

    def __repr__(self) -> str:
        return (
            f"<IncapacidadPrevisional("
            f"id={self.id}, "
            f"identificacion={self.identificacion}, "
            f"estado={self.estado}, "
            f"aval={self.aval}"
            f")>"
        )
