"""
Schemas Pydantic para Solicitante.
"""

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from uuid import UUID
from datetime import datetime
import re


class SolicitanteBase(BaseModel):
    """Schema base para Solicitante."""
    
    correo: EmailStr
    nombres: str
    apellidos: str
    telefono: str | None = None
    
    @field_validator('nombres', 'apellidos')
    @classmethod
    def validate_nombres(cls, v: str) -> str:
        """Validar que nombres y apellidos solo contengan letras y espacios."""
        if not v or not v.strip():
            raise ValueError('El campo no puede estar vacío')
        
        # Permitir letras (incluyendo acentos y ñ), espacios, guiones y apóstrofes
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-]{2,100}$', v):
            raise ValueError('Solo se permiten letras, espacios, guiones y apóstrofes (2-100 caracteres)')
        
        return v.strip()
    
    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v: str | None) -> str | None:
        """Validar formato de teléfono."""
        if v is None or v.strip() == '':
            return None
        
        # Remover espacios y guiones para validación
        telefono_clean = v.replace(' ', '').replace('-', '')
        
        # Validar que solo contenga dígitos y tenga entre 7 y 20 caracteres
        if not re.match(r'^\d{7,20}$', telefono_clean):
            raise ValueError('El teléfono debe contener entre 7 y 20 dígitos')
        
        return telefono_clean


class SolicitanteCreate(SolicitanteBase):
    """Schema para crear un Solicitante."""
    pass


class SolicitanteUpdate(BaseModel):
    """Schema para actualizar un Solicitante."""
    
    correo: EmailStr | None = None
    nombres: str | None = None
    apellidos: str | None = None
    telefono: str | None = None
    
    @field_validator('nombres', 'apellidos')
    @classmethod
    def validate_nombres(cls, v: str | None) -> str | None:
        """Validar que nombres y apellidos solo contengan letras y espacios."""
        if v is None:
            return None
        
        if not v.strip():
            raise ValueError('El campo no puede estar vacío')
        
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-]{2,100}$', v):
            raise ValueError('Solo se permiten letras, espacios, guiones y apóstrofes (2-100 caracteres)')
        
        return v.strip()
    
    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v: str | None) -> str | None:
        """Validar formato de teléfono."""
        if v is None or v.strip() == '':
            return None
        
        telefono_clean = v.replace(' ', '').replace('-', '')
        
        if not re.match(r'^\d{7,20}$', telefono_clean):
            raise ValueError('El teléfono debe contener entre 7 y 20 dígitos')
        
        return telefono_clean


class SolicitanteResponse(SolicitanteBase):
    """Schema para respuesta de Solicitante."""
    
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
