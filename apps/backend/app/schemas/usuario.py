"""
Schemas de Pydantic para Usuario.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.utils.enums import SucursalSiniestro


class UsuarioBase(BaseModel):
    """Schema base para Usuario."""
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    nombre_completo: str = Field(..., min_length=1, max_length=200, description="Nombre completo")
    rol: str = Field(..., description="Rol del usuario")
    sucursal: Optional[SucursalSiniestro] = Field(None, description="Sucursal (solo aplica a rol=AUDITOR)")


class UsuarioCreate(UsuarioBase):
    """Schema para crear un usuario."""
    password: str = Field(..., min_length=8, description="Contraseña (mínimo 8 caracteres)")
    estado: str = Field(default="ACTIVO", description="Estado del usuario")
    empleado_id: Optional[UUID] = Field(None, description="ID del empleado asociado")
    empresa_id: Optional[UUID] = Field(None, description="ID de la empresa asociada")
    must_change_password: bool = Field(default=True, description="Debe cambiar contraseña en primer acceso")


class UsuarioUpdate(BaseModel):
    """Schema para actualizar un usuario."""
    email: Optional[EmailStr] = None
    nombre_completo: Optional[str] = Field(None, min_length=1, max_length=200)
    rol: Optional[str] = None
    estado: Optional[str] = None
    empleado_id: Optional[UUID] = None
    empresa_id: Optional[UUID] = None
    sucursal: Optional[SucursalSiniestro] = None


class UsuarioChangePassword(BaseModel):
    """Schema para cambiar contraseña."""
    current_password: str = Field(..., description="Contraseña actual")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña (mínimo 8 caracteres)")
    confirm_password: str = Field(..., description="Confirmación de nueva contraseña")


class UsuarioResetPassword(BaseModel):
    """Schema para resetear contraseña (admin)."""
    new_password: str = Field(..., min_length=8, description="Nueva contraseña (mínimo 8 caracteres)")
    must_change_password: bool = Field(default=True, description="Debe cambiar contraseña en próximo acceso")


class UsuarioResponse(UsuarioBase):
    """Schema para respuesta de usuario."""
    id: UUID
    estado: str
    empleado_id: Optional[UUID] = None
    empresa_id: Optional[UUID] = None
    ultimo_acceso: Optional[datetime] = None
    intentos_fallidos: int
    bloqueado_hasta: Optional[datetime] = None
    must_change_password: bool
    created_at: datetime
    updated_at: datetime
    incapacidades_asignadas_activas: int

    model_config = ConfigDict(from_attributes=True)


class UsuarioListItem(BaseModel):
    """Schema para item en listado de usuarios."""
    id: UUID
    username: str
    email: str
    nombre_completo: str
    rol: str
    estado: str
    ultimo_acceso: Optional[datetime] = None
    created_at: datetime
    sucursal: Optional[SucursalSiniestro] = None
    incapacidades_asignadas_activas: int

    model_config = ConfigDict(from_attributes=True)


class UsuarioLogin(BaseModel):
    """Schema para login."""
    username: str = Field(..., description="Nombre de usuario o email")
    password: str = Field(..., description="Contraseña")


class UsuarioLoginResponse(BaseModel):
    """Schema para respuesta de login."""
    access_token: str
    token_type: str = "bearer"
    user: UsuarioResponse
