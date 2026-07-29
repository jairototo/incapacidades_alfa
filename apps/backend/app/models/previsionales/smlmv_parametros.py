"""
Modelo SQLAlchemy para parámetros SMLMV (Salario Mínimo Legal Mensual Vigente).

Almacena el valor anual del SMLMV usado como piso en cálculos de liquidación
de incapacidades. La tabla se siembra con los valores históricos (2024, 2025, 2026)
en la migración de creación.

Relación: independiente (sin FK a otras tablas).
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SmlmvParametros(BaseModel):
    """
    Parámetros SMLMV (Salario Mínimo Legal Mensual Vigente) por año.

    Cada fila representa el valor vigente para un año calendario.
    La columna `ano` tiene restricción UNIQUE para garantizar un solo
    valor de SMLMV configurado por año.

    Uso típico:
        params = await smlmv_parametros_repository.get_by_ano(db, 2026)
        valor_smlmv = params.valor  # Decimal("1750905.00")
    """

    __tablename__ = "smlmv_parametros"

    # Año al que aplican los parámetros (UNIQUE — un valor por año)
    ano: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        comment="Año calendario al que aplica este SMLMV",
    )

    # Valor del SMLMV en pesos colombianos
    valor: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        comment="Valor del SMLMV en pesos colombianos, p.ej. 1750905.00",
    )

    # Fecha desde la cual es vigente
    vigente_desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Fecha desde la cual es vigente este valor del SMLMV",
    )

    def __repr__(self) -> str:
        return (
            f"<SmlmvParametros("
            f"id={self.id}, "
            f"ano={self.ano}, "
            f"valor={self.valor}, "
            f"vigente_desde={self.vigente_desde}"
            f")>"
        )
