"""
Schemas de Pydantic para autenticación.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, EmailStr


class TokenResponse(BaseModel):
    """Schema para respuesta de token."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")


class RefreshTokenRequest(BaseModel):
    """Schema para solicitud de refresh token."""
    refresh_token: str = Field(..., description="Refresh token")


class ChangePasswordRequest(BaseModel):
    """Schema para cambio de contraseña."""
    current_password: str = Field(..., min_length=8, description="Contraseña actual")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")


class UserProfileResponse(BaseModel):
    """Schema para respuesta de perfil de usuario."""
    id: UUID
    username: str
    email: str
    nombre_completo: str
    rol: str
    estado: str
    ultimo_acceso: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Schema para solicitud de login."""
    username: str = Field(..., description="Nombre de usuario")
    password: str = Field(..., description="Contraseña")


class LoginResponse(TokenResponse):
    """Schema para respuesta de login (incluye información del usuario)."""
    user: UserProfileResponse
