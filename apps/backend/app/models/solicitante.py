"""
Modelo Solicitante - Persona que radica una incapacidad.

El solicitante puede ser diferente al empleado/afiliado beneficiario.
Por ejemplo: un representante legal, familiar, o la misma persona.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING

from apps.backend.app.models.base import BaseModel

if TYPE_CHECKING:
    from apps.backend.app.models.incapacidad import Incapacidad


class Solicitante(BaseModel):
    """
    Modelo para el solicitante que radica una incapacidad.
    
    Attributes:
        correo: Email del solicitante (único)
        nombres: Nombres del solicitante
        apellidos: Apellidos del solicitante
        telefono: Teléfono de contacto (opcional)
        incapacidades: Relación con las incapacidades radicadas por este solicitante
    """
    
    __tablename__ = "solicitante"
    
    correo: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Email del solicitante (único)"
    )
    
    nombres: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Nombres del solicitante"
    )
    
    apellidos: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Apellidos del solicitante"
    )
    
    telefono: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Teléfono de contacto"
    )
    
    # Relación con incapacidades
    incapacidades: Mapped[List["Incapacidad"]] = relationship(
        back_populates="solicitante",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Solicitante(id={self.id}, correo='{self.correo}', nombres='{self.nombres} {self.apellidos}')>"
    
    @property
    def nombre_completo(self) -> str:
        """Retorna el nombre completo del solicitante."""
        return f"{self.nombres} {self.apellidos}"
