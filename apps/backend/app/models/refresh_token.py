"""
Modelo SQLAlchemy para RefreshToken.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP

from apps.backend.app.models.base import BaseModel


class RefreshToken(BaseModel):
    """Modelo de RefreshToken para gestión de tokens de refresco."""
    
    __tablename__ = "refresh_token"
    
    # Usuario propietario del token
    usuario_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Token hasheado (nunca almacenar tokens en texto plano)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    
    # Fecha de expiración
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, index=True)
    
    # Información del cliente
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    
    # Estado
    revoked: Mapped[bool] = mapped_column(default=False, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    
    # Token version del usuario (para invalidación masiva)
    token_version: Mapped[int] = mapped_column(default=0, nullable=False)
    
    # Relaciones
    usuario: Mapped["Usuario"] = relationship(
        "Usuario",
        back_populates="refresh_tokens",
        lazy="selectin"
    )
    
    # Índices compuestos
    __table_args__ = (
        Index('ix_refresh_token_usuario_version', 'usuario_id', 'token_version'),
        Index('ix_refresh_token_expires_revoked', 'expires_at', 'revoked'),
    )
    
    def __repr__(self) -> str:
        return f"<RefreshToken {self.id} - User: {self.usuario_id}>"
    
    @property
    def is_valid(self) -> bool:
        """Verifica si el token es válido."""
        if self.revoked:
            return False
        # Usar timezone-aware datetime para comparar
        now = datetime.now(timezone.utc)
        if now > self.expires_at:
            return False
        return True
    
    def revoke(self) -> None:
        """Revoca el token."""
        self.revoked = True
        self.revoked_at = datetime.now(timezone.utc)
