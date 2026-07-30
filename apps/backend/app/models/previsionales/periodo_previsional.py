"""
Modelo SQLAlchemy para Periodo Previsional.

Segmento mensual de una incapacidad previsional (ver `segmentacion.py`,
función `segmentar()`), con su IBC/salario pareado y el valor liquidado de
ese tramo. `grupo_arpis` marca a qué grupo de salario ARPIS (máx. 3,
columnas K-M/N-P del cargue) pertenece este segmento — ver
`arpis_export.agrupar_salarios`, que alerta con `DemasiadosGruposError`
cuando hay más de 3 grupos consecutivos de salario distinto.

Relación: MANY-TO-ONE con IncapacidadPrevisional (CASCADE DELETE).
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PeriodoPrevisional(BaseModel):
    """
    Segmento mensual de una incapacidad previsional.

    Cada fila es un tramo (`Segmento` de `segmentacion.py`) con su
    IBC/salario y el valor liquidado para ese tramo específico, usando la
    fórmula `max(IBC * 0.5, SMLMV_ano) / 30 * dias` (ver
    `liquidacion_previsional.calcular_valor`).
    """

    __tablename__ = "periodos_previsionales"

    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidades_previsionales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Incapacidad previsional a la que pertenece este segmento",
    )

    orden: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Número secuencial del segmento (1-based), ver Segmento.orden"
    )

    fecha_inicio: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Fecha inicial (inclusiva) del segmento"
    )
    fecha_fin: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Fecha final (inclusiva) del segmento"
    )
    dias: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Días del segmento, conteo inclusivo (fecha_fin - fecha_inicio + 1)"
    )

    ibc: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Ingreso Base de Cotización del segmento — base real de la liquidación (NO salario)",
    )
    salario: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Salario reportado del segmento (informativo, no es la base)"
    )
    dias_cotizados: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Días cotizados del segmento según la AFP"
    )

    smlmv_aplicado: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="SMLMV del año del segmento, usado como piso"
    )
    base_diaria: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Base mensual aplicada (max(IBC*0.5, SMLMV)) dividida entre 30"
    )
    valor_segmento: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Valor liquidado de este segmento (base_diaria * dias)"
    )

    grupo_arpis: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Grupo de salario ARPIS (1-3) al que pertenece este segmento — ver agrupar_salarios()",
    )

    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    incapacidad: Mapped["IncapacidadPrevisional"] = relationship(
        "IncapacidadPrevisional",
        back_populates="periodos",
        foreign_keys=[incapacidad_id],
    )

    def __repr__(self) -> str:
        return (
            f"<PeriodoPrevisional("
            f"id={self.id}, "
            f"incapacidad_id={self.incapacidad_id}, "
            f"orden={self.orden}, "
            f"valor_segmento={self.valor_segmento}"
            f")>"
        )
