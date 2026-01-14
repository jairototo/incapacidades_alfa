"""
Modelo SQLAlchemy para HistorialEstado (polimórfico).
Registra cambios de estado para Incapacidades y Siniestros.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class HistorialEstado(BaseModel):
    """
    Modelo polimórfico de Historial de Estados.
    
    Registra cambios de estado para múltiples entidades (Incapacidad, Siniestro, etc.)
    usando un enfoque polimórfico con entity_type y entity_id.
    """
    
    __tablename__ = "historial_estado"
    
    # Relación polimórfica
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Tipo de entidad: 'incapacidad', 'siniestro', etc."
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID de la entidad relacionada"
    )
    
    # Estados (almacenados como string para flexibilidad)
    estado_anterior: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Estado previo al cambio"
    )
    estado_nuevo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Nuevo estado después del cambio"
    )
    
    # Información del cambio
    observacion: Mapped[Optional[str]] = mapped_column(Text)
    fecha_cambio: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
    # Usuario que realizó el cambio
    cambiado_por_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id"),
        comment="Usuario que realizó el cambio"
    )
    
    # Relaciones
    cambiado_por: Mapped[Optional["Usuario"]] = relationship("Usuario", lazy="select")
    
    # Índice compuesto para búsquedas eficientes
    __table_args__ = (
        Index('ix_historial_entity', 'entity_type', 'entity_id'),
    )
    
    def __repr__(self) -> str:
        return f"<HistorialEstado {self.entity_type}:{self.entity_id} {self.estado_anterior} → {self.estado_nuevo}>"
    
    @property
    def descripcion_cambio(self) -> str:
        """Retorna una descripción legible del cambio de estado."""
        if self.estado_anterior:
            return f"Cambio de {self.estado_anterior.value} a {self.estado_nuevo.value}"
        return f"Estado inicial: {self.estado_nuevo.value}"
