"""
Modelo SQLAlchemy para Siniestro Previsional.

Siniestro laboral usado como referencia por las reglas AM-AP del motor de
auditoría previsional (ver `auditoria_rules.SiniestroRef`). Deliberadamente
SEPARADO de la tabla `siniestro` (ARL): esa tabla se llega por FK a
`empleado`/`empresa`, que no aplican al dominio previsional (afiliados
identificados solo por número de documento, sin relación con empresas ARL).
Se referencia por `identificacion` en vez de FK a `empleado`.
"""
from datetime import date
from typing import Optional

from sqlalchemy import Date, String

from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SiniestroPrevisional(BaseModel):
    """
    Siniestro previsional, keyed por `identificacion` (número de documento).

    Puede haber múltiples siniestros para la misma identificación — la
    regla AM del motor de auditoría trata eso como ambigüedad que requiere
    selección manual (ver `_seleccionar_siniestro` en `auditoria_rules.py`),
    nunca elige "el primero" o "el más reciente" silenciosamente.
    """

    __tablename__ = "siniestros_previsionales"

    identificacion: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Número de documento del afiliado (no hay FK a empleado/empresa — dominio previsional)",
    )
    numero_siniestro: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Número de siniestro (regla AM)"
    )
    origen: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Origen del siniestro (regla AN)"
    )
    estado: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, comment="Estado del siniestro (regla AO)"
    )
    fecha_aviso: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha de aviso del siniestro (regla AP)"
    )
    fecha_siniestro: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Fecha de ocurrencia del siniestro (regla AP)"
    )

    def __repr__(self) -> str:
        return (
            f"<SiniestroPrevisional("
            f"id={self.id}, "
            f"identificacion={self.identificacion}, "
            f"numero_siniestro={self.numero_siniestro}"
            f")>"
        )
