"""
Tests de integración para API de autenticación.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.core.config import settings
from app.models.usuario import Usuario
from app.models.refresh_token import RefreshToken
from app.utils.enums import RolUsuario, EstadoUsuario


@pytest.mark.asyncio
async def test_login_endpoint(client: AsyncClient, test_usuario: Usuario, db_session: AsyncSession):
    """Test POST /api/v1/auth/login con credenciales válidas."""
    # Arrange
    # El test_usuario ya está en la DB gracias al fixture
    login_data = {
        "username": test_usuario.username,
        "password": "Test123!"  # Contraseña conocida del fixture
    }
    
    # Act
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["username"] == test_usuario.username


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, db_session: AsyncSession):
    """Test POST /api/v1/auth/login con credenciales inválidas."""
    # Arrange
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    
    # Act
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    # Assert
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_endpoint(client: AsyncClient, test_usuario: Usuario, db_session: AsyncSession):
    """Test POST /api/v1/auth/refresh con refresh token válido."""
    # Arrange
    # Crear un refresh token JWT válido
    token_data = {
        "sub": str(test_usuario.id),
        "type": "refresh",
        "token_version": test_usuario.token_version,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    refresh_token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Crear hash del token
    import hashlib
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    # Mock del refresh token en DB
    db_refresh_token = RefreshToken(
        id=uuid4(),
        usuario_id=test_usuario.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
        token_version=test_usuario.token_version
    )
    
    # Mock de la base de datos
    with patch('app.api.v1.endpoints.auth.get_db') as mock_get_db:
        mock_get_db.return_value = db_session
        
        with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
            # Primer execute: obtener refresh token
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = db_refresh_token
            
            # Segundo execute: obtener usuario
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = test_usuario
            
            mock_execute.side_effect = [mock_result1, mock_result2]
            
            # Act
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token


@pytest.mark.asyncio
async def test_logout_endpoint(
    client: AsyncClient,
    test_usuario: Usuario,
    db_session: AsyncSession
):
    """Test POST /api/v1/auth/logout con refresh token válido."""
    # Arrange
    # Crear access token para autenticación
    access_token_data = {
        "sub": str(test_usuario.id),
        "type": "access",
        "username": test_usuario.username,
        "rol": test_usuario.rol.value,
        "token_version": test_usuario.token_version,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    access_token = jwt.encode(access_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Crear refresh token
    refresh_token_data = {
        "sub": str(test_usuario.id),
        "type": "refresh",
        "token_version": test_usuario.token_version,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    refresh_token = jwt.encode(refresh_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Crear hash del token
    import hashlib
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    # Mock del refresh token en DB
    db_refresh_token = RefreshToken(
        id=uuid4(),
        usuario_id=test_usuario.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
        token_version=test_usuario.token_version
    )
    
    # Mock de la base de datos
    with patch('app.api.v1.endpoints.auth.get_db') as mock_get_db:
        mock_get_db.return_value = db_session
        
        with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
            # Primer execute: obtener usuario (para get_current_user)
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = test_usuario
            
            # Segundo execute: obtener refresh token
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = db_refresh_token
            
            mock_execute.side_effect = [mock_result1, mock_result2]
            
            # Mock commit
            db_session.commit = AsyncMock()
            
            # Act
            response = await client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": refresh_token},
                headers={"Authorization": f"Bearer {access_token}"}
            )
    
    # Assert
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_change_password_endpoint(
    client: AsyncClient,
    test_usuario: Usuario,
    db_session: AsyncSession
):
    """Test POST /api/v1/auth/change-password."""
    # Arrange
    # Crear access token para autenticación
    access_token_data = {
        "sub": str(test_usuario.id),
        "type": "access",
        "username": test_usuario.username,
        "rol": test_usuario.rol.value,
        "token_version": test_usuario.token_version,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    access_token = jwt.encode(access_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    password_data = {
        "current_password": "Test123!",
        "new_password": "NewPassword456!"
    }
    
    # Mock de la base de datos
    with patch('app.api.v1.endpoints.auth.get_db') as mock_get_db:
        mock_get_db.return_value = db_session
        
        with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
            # Primer execute: obtener usuario (para get_current_user)
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = test_usuario
            
            # Segundo execute: obtener usuario para cambiar password
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = test_usuario
            
            mock_execute.side_effect = [mock_result1, mock_result2]
            
            with patch('app.core.security.pwd_context.verify', return_value=True):
                with patch('app.core.security.pwd_context.hash', return_value="new_hashed"):
                    # Mock commit
                    db_session.commit = AsyncMock()
                    
                    # Act
                    response = await client.post(
                        "/api/v1/auth/change-password",
                        json=password_data,
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
    
    # Assert
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_current_user_profile(
    client: AsyncClient,
    test_usuario: Usuario,
    db_session: AsyncSession
):
    """Test GET /api/v1/auth/me."""
    # Arrange
    # Crear access token para autenticación
    access_token_data = {
        "sub": str(test_usuario.id),
        "type": "access",
        "username": test_usuario.username,
        "rol": test_usuario.rol.value,
        "token_version": test_usuario.token_version,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    access_token = jwt.encode(access_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Mock de la base de datos
    with patch('app.api.v1.endpoints.auth.get_db') as mock_get_db:
        mock_get_db.return_value = db_session
        
        with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
            # Obtener usuario
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = test_usuario
            mock_execute.return_value = mock_result
            
            # Act
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_usuario.id)
    assert data["username"] == test_usuario.username
    assert data["email"] == test_usuario.email


@pytest.mark.asyncio
async def test_logout_all_sessions_endpoint(
    client: AsyncClient,
    test_usuario: Usuario,
    db_session: AsyncSession
):
    """Test POST /api/v1/auth/logout-all."""
    # Arrange
    # Crear access token para autenticación
    access_token_data = {
        "sub": str(test_usuario.id),
        "type": "access",
        "username": test_usuario.username,
        "rol": test_usuario.rol.value,
        "token_version": test_usuario.token_version,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    access_token = jwt.encode(access_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Mock de la base de datos
    with patch('app.api.v1.endpoints.auth.get_db') as mock_get_db:
        mock_get_db.return_value = db_session
        
        with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
            # Primer execute: obtener usuario (para get_current_user)
            mock_result1 = MagicMock()
            mock_result1.scalar_one_or_none.return_value = test_usuario
            
            # Segundo execute: obtener usuario para logout_all
            mock_result2 = MagicMock()
            mock_result2.scalar_one_or_none.return_value = test_usuario
            
            mock_execute.side_effect = [mock_result1, mock_result2]
            
            # Mock commit
            db_session.commit = AsyncMock()
            
            # Act
            response = await client.post(
                "/api/v1/auth/logout-all",
                headers={"Authorization": f"Bearer {access_token}"}
            )
    
    # Assert
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test acceso a endpoint protegido sin token."""
    # Act
    response = await client.get("/api/v1/auth/me")
    
    # Assert
    assert response.status_code == 401
