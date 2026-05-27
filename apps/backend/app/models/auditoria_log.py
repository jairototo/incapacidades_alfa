"""
Modelo SQLAlchemy para AuditoriaLog.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, INET, TIMESTAMP

from apps.backend.app.models.base import BaseModel
from apps.backend.app.utils.enums import AccionAuditoria


class AuditoriaLog(BaseModel):
    """Modelo de Log de Auditoría."""
    
    __tablename__ = "auditoria_log"
    
    # Usuario que realizó la acción
    usuario_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id"),
        index=True
    )
    
    # Acción realizada
    accion: Mapped[AccionAuditoria] = mapped_column(String(50), nullable=False, index=True)
    
    # Entidad afectada
    entidad: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entidad_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), index=True)
    
    # Detalles de la acción (JSON)
    detalles: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Información de la petición
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    request_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    
    # Relación con usuario
    usuario: Mapped[Optional["Usuario"]] = relationship(
        "Usuario",
        back_populates="auditoria_logs",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<AuditoriaLog {self.accion} - {self.entidad} {self.entidad_id}>"
    
    @property
    def descripcion(self) -> str:
        """Retorna una descripción legible de la acción."""
        usuario_str = self.usuario.username if self.usuario else "Sistema"
        return f"{usuario_str} realizó {self.accion.value} en {self.entidad} {self.entidad_id}"
