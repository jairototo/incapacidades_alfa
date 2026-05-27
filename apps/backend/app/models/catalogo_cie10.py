"""
Modelo para Catálogo CIE-10 (Clasificación Internacional de Enfermedades).

Este catálogo contiene los códigos diagnósticos médicos estandarizados
utilizados internacionalmente.
"""

from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from apps.backend.app.models.base import Base


class CatalogoCIE10(Base):
    """
    Catálogo de códigos CIE-10.
    
    Attributes:
        codigo: Código CIE-10 (ej: "A00.0", "J00")
        descripcion: Descripción completa del diagnóstico
    """
    
    __tablename__ = "catalogo_cie10"
    
    codigo: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        comment="Código CIE-10"
    )
    
    descripcion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Descripción del diagnóstico"
    )
    
    # Índice para búsqueda full-text en PostgreSQL
    __table_args__ = (
        Index(
            'idx_cie10_descripcion_fts',
            'descripcion',
            postgresql_using='gin',
            postgresql_ops={'descripcion': 'gin_trgm_ops'}
        ),
        Index(
            'idx_cie10_codigo_pattern',
            'codigo',
            postgresql_using='gin',
            postgresql_ops={'codigo': 'gin_trgm_ops'}
        ),
    )
    
    def __repr__(self) -> str:
        return f"<CatalogoCIE10(codigo='{self.codigo}', descripcion='{self.descripcion[:50]}...')>"
