"""
Schemas de Pydantic para Empleado.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmpleadoBase(BaseModel):
    """Schema base para Empleado."""
    empresa_id: UUID = Field(..., description="ID de la empresa")
    numero_documento: str = Field(..., min_length=1, max_length=20, description="Número de documento")
    tipo_documento: str = Field(..., description="Tipo de documento (CC, CE, TI, etc.)")
    nombres: str = Field(..., min_length=1, max_length=100, description="Nombres")
    apellidos: str = Field(..., min_length=1, max_length=100, description="Apellidos")
    email: Optional[EmailStr] = Field(None, description="Email del empleado")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono")
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    genero: Optional[str] = Field(None, max_length=1, description="Género (M/F/O)")
    cargo: Optional[str] = Field(None, max_length=100, description="Cargo")
    area: Optional[str] = Field(None, max_length=100, description="Área de trabajo")
    fecha_ingreso: Optional[date] = Field(None, description="Fecha de ingreso")
    salario_base: Optional[Decimal] = Field(None, ge=0, description="Salario base")


class EmpleadoCreate(EmpleadoBase):
    """Schema para crear un empleado."""
    fecha_retiro: Optional[date] = Field(None, description="Fecha de retiro")
    cuenta_bancaria: Optional[str] = Field(None, max_length=50)
    banco: Optional[str] = Field(None, max_length=100)
    tipo_cuenta: Optional[str] = Field(None, description="Tipo de cuenta bancaria")
    estado: str = Field(default="ACTIVO", description="Estado del empleado")
    sync_source: Optional[str] = Field(None, description="Fuente de sincronización")
    external_id: Optional[str] = Field(None, max_length=100, description="ID externo")


class EmpleadoUpdate(BaseModel):
    """Schema para actualizar un empleado."""
    nombres: Optional[str] = Field(None, min_length=1, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = Field(None, max_length=1)
    cargo: Optional[str] = Field(None, max_length=100)
    area: Optional[str] = Field(None, max_length=100)
    fecha_ingreso: Optional[date] = None
    fecha_retiro: Optional[date] = None
    salario_base: Optional[Decimal] = Field(None, ge=0)
    cuenta_bancaria: Optional[str] = Field(None, max_length=50)
    banco: Optional[str] = Field(None, max_length=100)
    tipo_cuenta: Optional[str] = None
    estado: Optional[str] = None


class EmpleadoResponse(EmpleadoBase):
    """Schema para respuesta de empleado."""
    id: UUID
    fecha_retiro: Optional[date] = None
    cuenta_bancaria: Optional[str] = None
    banco: Optional[str] = None
    tipo_cuenta: Optional[str] = None
    estado: str
    created_at: datetime
    updated_at: datetime
    sync_source: Optional[str] = None
    external_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class EmpleadoListItem(BaseModel):
    """Schema para item en listado de empleados."""
    id: UUID
    numero_documento: str
    tipo_documento: str
    nombres: str
    apellidos: str
    cargo: Optional[str] = None
    estado: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
