"""
Schemas de Pydantic para Empresa.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmpresaBase(BaseModel):
    """Schema base para Empresa."""
    nit: str = Field(..., min_length=1, max_length=20, description="NIT de la empresa")
    razon_social: str = Field(..., min_length=1, max_length=200, description="Razón social")
    estado: str = Field(default="ACTIVA", description="Estado de la empresa")
    email_contacto: Optional[EmailStr] = Field(None, description="Email de contacto")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    direccion: Optional[str] = Field(None, max_length=200, description="Dirección")
    ciudad: Optional[str] = Field(None, max_length=100, description="Ciudad")
    departamento: Optional[str] = Field(None, max_length=100, description="Departamento")
    tipo_empresa: Optional[str] = Field(None, max_length=50, description="Tipo de empresa")
    nro_contrato: Optional[str] = Field(None, max_length=100, description="Número de contrato")


class EmpresaCreate(EmpresaBase):
    """Schema para crear una empresa."""
    email_contacto: EmailStr = Field(..., description="Email de contacto de la empresa; también será el login del usuario-empresa generado")
    sync_source: Optional[str] = Field(None, description="Fuente de sincronización")
    external_id: Optional[str] = Field(None, max_length=100, description="ID externo")


class EmpresaUpdate(BaseModel):
    """Schema para actualizar una empresa."""
    razon_social: Optional[str] = Field(None, min_length=1, max_length=200)
    estado: Optional[str] = None
    email_contacto: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = Field(None, max_length=200)
    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    tipo_empresa: Optional[str] = Field(None, max_length=50)
    nro_contrato: Optional[str] = Field(None, max_length=100)


class EmpresaResponse(EmpresaBase):
    """Schema para respuesta de empresa."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    sync_source: Optional[str] = None
    external_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class EmpresaListItem(BaseModel):
    """Schema para item en listado de empresas."""
    id: UUID
    nit: str
    razon_social: str
    estado: str
    ciudad: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsuarioGenerado(BaseModel):
    """Credenciales generadas al crear/regenerar el usuario-empresa. Se devuelven una sola vez."""
    username: str
    password: str


class EmpresaCreateResponse(EmpresaResponse):
    """Respuesta de creación de empresa, incluye las credenciales generadas una única vez."""
    usuario_generado: UsuarioGenerado
