"""
Tests de integración para API de autenticación (simplificados).
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from apps.backend.app.core.config import settings
from apps.backend.app.models.usuario import Usuario
from apps.backend.app.models.refresh_token import RefreshToken
from apps.backend.app.utils.enums import RolUsuario, EstadoUsuario


@pytest.mark.asyncio
async def test_login_endpoint(client: AsyncClient, test_usuario: Usuario):
    """Test POST /api/v1/auth/login."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_usuario.username, "password": "Test123!"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == test_usuario.username


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test POST /api/v1/auth/login con credenciales inválidas."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_endpoint(client: AsyncClient, test_usuario: Usuario, db_session: AsyncSession):
    """Test POST /api/v1/auth/refresh."""
    # Primero hacer login para obtener un refresh token válido
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_usuario.username, "password": "Test123!"}
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Ahora refrescar el token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient, test_usuario: Usuario):
    """Test GET /api/v1/auth/me."""
    # Login primero
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_usuario.username, "password": "Test123!"}
    )
    access_token = login_response.json()["access_token"]
    
    # Obtener perfil
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_usuario.username


@pytest.mark.asyncio
async def test_change_password_endpoint(client: AsyncClient, test_usuario: Usuario):
    """Test POST /api/v1/auth/change-password."""
    # Login primero
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_usuario.username, "password": "Test123!"}
    )
    access_token = login_response.json()["access_token"]
    
    # Cambiar contraseña
    response = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Test123!", "new_password": "NewPassword456!"},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient, test_usuario: Usuario):
    """Test POST /api/v1/auth/logout."""
    # Login primero
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_usuario.username, "password": "Test123!"}
    )
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]
    
    # Logout
    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_logout_all_sessions_endpoint(client: AsyncClient, test_usuario: Usuario):
    """Test POST /api/v1/auth/logout-all."""
    # Login primero
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_usuario.username, "password": "Test123!"}
    )
    access_token = login_response.json()["access_token"]
    
    # Logout all
    response = await client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test acceso no autorizado."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
