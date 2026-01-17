"""
Schemas Pydantic para Catálogo CIE-10.
"""

from pydantic import BaseModel, Field


class CIE10Response(BaseModel):
    """Schema de respuesta para un código CIE-10."""
    
    codigo: str = Field(..., description="Código CIE-10", example="A00.0")
    descripcion: str = Field(..., description="Descripción del diagnóstico")
    
    model_config = {"from_attributes": True}


class CIE10Create(BaseModel):
    """Schema para crear un código CIE-10 (solo admin)."""
    
    codigo: str = Field(..., min_length=1, max_length=10, description="Código CIE-10")
    descripcion: str = Field(..., min_length=1, description="Descripción del diagnóstico")
