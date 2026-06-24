"""
Modelo SQLAlchemy para Liquidación de Incapacidad.

Almacena el cálculo detallado del valor a pagar por una incapacidad,
incluyendo el IBL (Ingreso Base de Liquidación) calculado a partir de
los parámetros de la tabla ibl_parametros, los días autorizados por
el auditor, y el desglose de aportes patronales y del trabajador.

Relación ONE-TO-ONE con Incapacidad (CASCADE DELETE).
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.utils.enums import MetodoPagoLiquidacion


class Liquidacion(BaseModel):
    """
    Liquidación de incapacidad.

    Contiene el cálculo económico completo de lo que debe pagarse por
    una incapacidad aprobada: IBL, días autorizados, desglose de aportes
    y valor total.

    Relación: ONE-TO-ONE con Incapacidad (unique=True en incapacidad_id).
    """

    __tablename__ = "liquidacion"

    # Relación con incapacidad (ONE-TO-ONE, CASCADE DELETE)
    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="ID de la incapacidad a la que pertenece esta liquidación",
    )

    # -------------------------------------------------------------------------
    # IBL (Ingreso Base de Liquidación)
    # -------------------------------------------------------------------------
    ibl: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Ingreso Base de Liquidación — promedio IBC 6 meses previos",
    )

    periodo_ibl_inicio: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Inicio del período de cálculo del IBL (6 meses previos)",
    )

    periodo_ibl_fin: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Fin del período de cálculo del IBL",
    )

    # -------------------------------------------------------------------------
    # Período autorizado (copiado de plantilla_auditoria)
    # -------------------------------------------------------------------------
    dias_autorizados: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Número de días autorizados por el auditor (fuente: plantilla_auditoria)",
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

    # -------------------------------------------------------------------------
    # Desglose de valores
    # (TODO: confirmar fórmulas de porcentajes con Helen — task C2)
    # -------------------------------------------------------------------------
    valor_incapacidad_temporal: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Valor de la incapacidad temporal calculada",
    )

    valor_aporte_patronal_pension: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Valor del aporte patronal a pensión",
    )

    valor_aporte_trabajador_pension: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Valor del aporte del trabajador a pensión",
    )

    valor_aporte_adicional_trabajador_pension: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Valor del aporte adicional del trabajador a pensión (si aplica)",
    )

    valor_aporte_patronal_salud: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Valor del aporte patronal a salud",
    )

    valor_aporte_trabajador_salud: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Valor del aporte del trabajador a salud",
    )

    valor_total: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Valor total a pagar (suma de todos los componentes)",
    )

    # -------------------------------------------------------------------------
    # Pago
    # -------------------------------------------------------------------------
    metodo_pago: Mapped[Optional[MetodoPagoLiquidacion]] = mapped_column(
        PGEnum(
            MetodoPagoLiquidacion,
            name="metodopagoliquidacion",
            create_type=False,
        ),
        nullable=True,
        comment="Método de pago (C2: pendiente lista de entidades por método del cliente)",
    )

    notas_liquidador: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Observaciones libres del liquidador",
    )

    liquidador_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id"),
        nullable=True,
        comment="ID del usuario que realizó la liquidación",
    )

    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    incapacidad: Mapped["Incapacidad"] = relationship(
        "Incapacidad",
        back_populates="liquidacion",
        foreign_keys=[incapacidad_id],
    )

    liquidador: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
        foreign_keys=[liquidador_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Liquidacion("
            f"id={self.id}, "
            f"incapacidad_id={self.incapacidad_id}, "
            f"valor_total={self.valor_total}, "
            f"dias_autorizados={self.dias_autorizados}"
            f")>"
        )
