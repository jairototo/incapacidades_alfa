"""
Schemas de Pydantic para Afiliado.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AfiliadoBase(BaseModel):
    """Schema base para Afiliado."""
    numero_poliza: str = Field(..., min_length=1, max_length=50, description="Número de póliza")
    tipo_poliza: str = Field(..., description="Tipo de póliza (INDIVIDUAL, FAMILIAR, COLECTIVA)")
    tipo_documento: str = Field(..., description="Tipo de documento (CC, CE, TI, etc.)")
    numero_documento: str = Field(..., min_length=1, max_length=20, description="Número de documento")
    nombres: str = Field(..., min_length=1, max_length=100, description="Nombres")
    apellidos: str = Field(..., min_length=1, max_length=100, description="Apellidos")
    email: Optional[EmailStr] = Field(None, description="Email del afiliado")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono")
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    genero: Optional[str] = Field(None, max_length=1, description="Género (M/F/O)")
    direccion: Optional[str] = Field(None, max_length=200, description="Dirección")
    ciudad: Optional[str] = Field(None, max_length=100, description="Ciudad")
    departamento: Optional[str] = Field(None, max_length=100, description="Departamento")


class AfiliadoCreate(AfiliadoBase):
    """Schema para crear un afiliado."""
    fecha_inicio_poliza: date = Field(..., description="Fecha de inicio de vigencia de la póliza")
    fecha_fin_poliza: Optional[date] = Field(None, description="Fecha de fin de vigencia")
    cuenta_bancaria: Optional[str] = Field(None, max_length=50)
    banco: Optional[str] = Field(None, max_length=100)
    tipo_cuenta: Optional[str] = Field(None, description="Tipo de cuenta bancaria")
    estado: str = Field(default="ACTIVO", description="Estado del afiliado")
    sync_source: Optional[str] = Field(None, description="Fuente de sincronización")
    external_id: Optional[str] = Field(None, max_length=100, description="ID externo")


class AfiliadoUpdate(BaseModel):
    """Schema para actualizar un afiliado."""
    tipo_poliza: Optional[str] = None
    nombres: Optional[str] = Field(None, min_length=1, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = Field(None, max_length=1)
    direccion: Optional[str] = Field(None, max_length=200)
    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    fecha_inicio_poliza: Optional[date] = None
    fecha_fin_poliza: Optional[date] = None
    cuenta_bancaria: Optional[str] = Field(None, max_length=50)
    banco: Optional[str] = Field(None, max_length=100)
    tipo_cuenta: Optional[str] = None
    estado: Optional[str] = None


class AfiliadoResponse(AfiliadoBase):
    """Schema para respuesta de afiliado."""
    id: UUID
    fecha_inicio_poliza: date
    fecha_fin_poliza: Optional[date] = None
    cuenta_bancaria: Optional[str] = None
    banco: Optional[str] = None
    tipo_cuenta: Optional[str] = None
    estado: str
    created_at: datetime
    updated_at: datetime
    sync_source: Optional[str] = None
    external_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AfiliadoListItem(BaseModel):
    """Schema para item en listado de afiliados."""
    id: UUID
    numero_poliza: str
    tipo_poliza: str
    numero_documento: str
    tipo_documento: str
    nombres: str
    apellidos: str
    estado: str
    fecha_inicio_poliza: date
    fecha_fin_poliza: Optional[date] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
