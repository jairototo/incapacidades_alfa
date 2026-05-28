"""
Endpoints de autenticación.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.auth import (
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    UserProfileResponse,
    LoginResponse
)
from app.services.auth_service import AuthService


router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description="Autenticar usuario y obtener tokens"
)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica un usuario y retorna access y refresh tokens.
    
    - **username**: Nombre de usuario
    - **password**: Contraseña
    
    Returns:
        Tokens JWT y perfil de usuario
    """
    auth_service = AuthService(db)
    
    # Obtener información del cliente
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    
    return await auth_service.login(
        username=form_data.username,
        password=form_data.password,
        user_agent=user_agent,
        ip_address=ip_address
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Cerrar sesión revocando el refresh token"
)
async def logout(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cierra la sesión del usuario revocando el refresh token.
    
    - **refresh_token**: Refresh token a revocar
    
    Returns:
        Sin contenido (204)
    """
    auth_service = AuthService(db)
    await auth_service.logout(refresh_data.refresh_token)
    return None


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh token",
    description="Renovar access token usando refresh token"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Renueva el access token usando un refresh token válido.
    
    - **refresh_token**: Refresh token
    
    Returns:
        Nuevo access token
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(refresh_data.refresh_token)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cambiar contraseña",
    description="Cambiar la contraseña del usuario actual"
)
async def change_password(
    password_data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cambia la contraseña del usuario actual.
    
    - **current_password**: Contraseña actual
    - **new_password**: Nueva contraseña
    
    Returns:
        Sin contenido (204)
    """
    auth_service = AuthService(db)
    await auth_service.change_password(
        user_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    return None


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Perfil actual",
    description="Obtener perfil del usuario autenticado"
)
async def get_current_user_profile(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el perfil del usuario autenticado.
    
    Returns:
        Perfil del usuario
    """
    return UserProfileResponse.model_validate(current_user)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar todas las sesiones",
    description="Cerrar todas las sesiones del usuario (invalida todos los tokens)"
)
async def logout_all_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cierra todas las sesiones del usuario incrementando token_version.
    
    Returns:
        Sin contenido (204)
    """
    auth_service = AuthService(db)
    await auth_service.logout_all_sessions(current_user.id)
    return None
