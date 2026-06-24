"""
Modelo SQLAlchemy para parámetros IBL (Ingreso Base de Liquidación).

Almacena los porcentajes de aportes patronales y del trabajador por año.
El servicio de liquidación lee de esta tabla para el año en curso, evitando
hardcodear los porcentajes y permitiendo actualización anual sin código.

Relación: independiente (sin FK a otras tablas).
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class IblParametros(BaseModel):
    """
    Parámetros IBL por año.

    Cada fila representa los porcentajes vigentes para un año calendario.
    La columna `ano` tiene restricción UNIQUE para garantizar una sola
    configuración por año.

    Uso típico:
        params = await ibl_parametros_repository.get_by_ano(db, 2026)
        porcentaje_patronal = params.aporte_patronal_pension  # 12.00
    """

    __tablename__ = "ibl_parametros"

    # Año al que aplican los parámetros (UNIQUE — una fila por año)
    ano: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        comment="Año calendario al que aplican estos porcentajes de aporte",
    )

    # Aportes patronales
    aporte_patronal_pension: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Porcentaje aporte patronal pensión, e.g. 12.00",
    )

    aporte_patronal_salud: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Porcentaje aporte patronal salud, e.g. 8.50",
    )

    # Aportes del trabajador
    aporte_trabajador_pension: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Porcentaje aporte trabajador pensión, e.g. 4.00",
    )

    aporte_trabajador_salud: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Porcentaje aporte trabajador salud, e.g. 4.00",
    )

    def __repr__(self) -> str:
        return (
            f"<IblParametros("
            f"id={self.id}, "
            f"ano={self.ano}, "
            f"aporte_patronal_pension={self.aporte_patronal_pension}, "
            f"aporte_patronal_salud={self.aporte_patronal_salud}"
            f")>"
        )
