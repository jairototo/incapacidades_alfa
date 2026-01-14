"""
Modelo base para todas las entidades.
"""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB


class Base(DeclarativeBase):
    """Base class para todos los modelos."""
    pass


class BaseModel(Base):
    """
    Modelo base con campos comunes para todas las entidades.
    """
    __abstract__ = True
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Metadata adicional en JSON
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        default=dict
    )
    
    def dict(self):
        """Convertir a diccionario."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
