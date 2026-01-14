"""
Tests unitarios para AuthService.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.services.auth_service import AuthService
from app.models.usuario import Usuario
from app.models.refresh_token import RefreshToken
from app.core.config import settings
from app.core.exceptions import AuthenticationException, NotFoundException, ForbiddenException
from app.utils.enums import RolUsuario, EstadoUsuario


@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession, test_usuario: Usuario):
    """Test login exitoso con credenciales válidas."""
    # Arrange
    auth_service = AuthService(db_session)
    
    # Configurar mock para retornar el usuario
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_usuario
        mock_execute.return_value = mock_result
        
        with patch.object(auth_service, '_create_user_tokens', new_callable=AsyncMock) as mock_tokens:
            access_token = "test_access_token"
            refresh_token = "test_refresh_token"
            mock_tokens.return_value = (access_token, refresh_token)
            
            # Act
            result = await auth_service.login(
                username=test_usuario.username,
                password="Test123!",
                user_agent="pytest",
                ip_address="127.0.0.1"
            )
    
    # Assert
    assert result.access_token == access_token
    assert result.refresh_token == refresh_token
    assert result.user.id == test_usuario.id
    assert result.user.username == test_usuario.username


@pytest.mark.asyncio
async def test_login_invalid_credentials(db_session: AsyncSession):
    """Test login con credenciales inválidas."""
    # Arrange
    auth_service = AuthService(db_session)
    
    # Configurar mock para retornar None (usuario no encontrado)
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_execute.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            await auth_service.login(
                username="nonexistent",
                password="wrongpassword",
                user_agent="pytest",
                ip_address="127.0.0.1"
            )
        
        assert "Credenciales inválidas" in str(exc_info.value)


@pytest.mark.asyncio
async def test_login_user_inactive(db_session: AsyncSession, test_usuario: Usuario):
    """Test login con usuario inactivo."""
    # Arrange
    auth_service = AuthService(db_session)
    test_usuario.estado = EstadoUsuario.INACTIVO
    
    # Configurar mock
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_usuario
        mock_execute.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(ForbiddenException) as exc_info:
            await auth_service.login(
                username=test_usuario.username,
                password="Test123!",
                user_agent="pytest",
                ip_address="127.0.0.1"
            )
        
        assert "inactivo" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_login_max_failed_attempts(db_session: AsyncSession, test_usuario: Usuario):
    """Test bloqueo de cuenta después de 5 intentos fallidos."""
    # Arrange
    auth_service = AuthService(db_session)
    test_usuario.intentos_fallidos = 4  # Próximo intento será el 5to
    test_usuario.ultima_fecha_bloqueo = None
    
    # Configurar mock para password incorrecto
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_usuario
        mock_execute.return_value = mock_result
        
        # Mock commit para que persista cambios
        db_session.commit = AsyncMock()
        
        with patch('app.core.security.pwd_context.verify', return_value=False):
            # Act & Assert
            with pytest.raises(AuthenticationException) as exc_info:
                await auth_service.login(
                    username=test_usuario.username,
                    password="wrongpassword",
                    user_agent="pytest",
                    ip_address="127.0.0.1"
                )
            
            assert "credenciales" in str(exc_info.value).lower()
            assert test_usuario.intentos_fallidos == 5
            # Verificar que se llamó commit (para guardar el bloqueo)
            db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_refresh_access_token_success(db_session: AsyncSession, test_usuario: Usuario):
    """Test renovación exitosa de access token."""
    # Arrange
    auth_service = AuthService(db_session)
    
    # Crear un refresh token JWT válido
    token_data = {
        "sub": str(test_usuario.id),
        "type": "refresh",
        "token_version": test_usuario.token_version,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
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
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False,
        token_version=test_usuario.token_version
    )
    
    # Configurar mocks
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        # Primer execute: obtener refresh token
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = db_refresh_token
        
        # Segundo execute: obtener usuario
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = test_usuario
        
        mock_execute.side_effect = [mock_result1, mock_result2]
        
        # Act
        result = await auth_service.refresh_access_token(refresh_token)
    
    # Assert
    assert result.access_token is not None
    assert result.refresh_token == refresh_token
    assert result.token_type == "bearer"
    
    # Verificar que el nuevo access token sea válido
    decoded = jwt.decode(result.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == str(test_usuario.id)
    assert decoded["type"] == "access"


@pytest.mark.asyncio
async def test_refresh_access_token_revoked(db_session: AsyncSession, test_usuario: Usuario):
    """Test refresh token revocado."""
    # Arrange
    auth_service = AuthService(db_session)
    
    # Crear un refresh token JWT válido
    token_data = {
        "sub": str(test_usuario.id),
        "type": "refresh",
        "token_version": test_usuario.token_version,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    refresh_token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Crear hash del token
    import hashlib
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    # Mock del refresh token revocado
    db_refresh_token = RefreshToken(
        id=uuid4(),
        usuario_id=test_usuario.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=True,  # Token revocado
        token_version=test_usuario.token_version
    )
    
    # Configurar mock
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_refresh_token
        mock_execute.return_value = mock_result
        
        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            await auth_service.refresh_access_token(refresh_token)
        
        assert "token" in str(exc_info.value).lower() and "inválido" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_refresh_access_token_version_mismatch(db_session: AsyncSession, test_usuario: Usuario):
    """Test refresh token con version obsoleta."""
    # Arrange
    auth_service = AuthService(db_session)
    test_usuario.token_version = 2  # Usuario incrementó versión
    
    # Crear un refresh token JWT con versión antigua
    token_data = {
        "sub": str(test_usuario.id),
        "type": "refresh",
        "token_version": 1,  # Versión antigua
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
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
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False,
        token_version=1  # Versión antigua
    )
    
    # Configurar mocks
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        # Primer execute: obtener refresh token
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = db_refresh_token
        
        # Segundo execute: obtener usuario
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = test_usuario
        
        mock_execute.side_effect = [mock_result1, mock_result2]
        
        # Act & Assert
        with pytest.raises(AuthenticationException) as exc_info:
            await auth_service.refresh_access_token(refresh_token)
        
        assert "invalidado" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_logout_success(db_session: AsyncSession, test_usuario: Usuario):
    """Test logout exitoso revocando refresh token."""
    # Arrange
    auth_service = AuthService(db_session)
    
    # Crear un refresh token JWT válido
    token_data = {
        "sub": str(test_usuario.id),
        "type": "refresh",
        "token_version": test_usuario.token_version,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
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
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        revoked=False,
        token_version=test_usuario.token_version
    )
    
    # Configurar mock
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_refresh_token
        mock_execute.return_value = mock_result
        
        # Mock commit
        db_session.commit = AsyncMock()
        
        # Act
        await auth_service.logout(refresh_token)
    
    # Assert
    assert db_refresh_token.revoked is True
    assert db_refresh_token.revoked_at is not None
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_logout_all_sessions(db_session: AsyncSession, test_usuario: Usuario):
    """Test cerrar todas las sesiones incrementando token_version."""
    # Arrange
    auth_service = AuthService(db_session)
    initial_version = test_usuario.token_version
    
    # Configurar mock
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_usuario
        mock_execute.return_value = mock_result
        
        # Mock commit
        db_session.commit = AsyncMock()
        
        # Act
        await auth_service.logout_all_sessions(test_usuario.id)
    
    # Assert
    assert test_usuario.token_version == initial_version + 1
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_change_password_success(db_session: AsyncSession, test_usuario: Usuario):
    """Test cambio de contraseña exitoso."""
    # Arrange
    auth_service = AuthService(db_session)
    initial_version = test_usuario.token_version
    new_password = "NewPassword456!"
    
    # Configurar mocks
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_usuario
        mock_execute.return_value = mock_result
        
        with patch('app.core.security.pwd_context.verify', return_value=True):
            with patch('app.core.security.pwd_context.hash', return_value="new_hashed_password"):
                # Mock commit
                db_session.commit = AsyncMock()
                
                # Act
                await auth_service.change_password(
                    user_id=test_usuario.id,
                    current_password="Test123!",
                    new_password=new_password
                )
    
    # Assert
    assert test_usuario.password_hash == "new_hashed_password"
    assert test_usuario.token_version == initial_version + 1
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_change_password_invalid_current(db_session: AsyncSession, test_usuario: Usuario):
    """Test cambio de contraseña con contraseña actual incorrecta."""
    # Arrange
    auth_service = AuthService(db_session)
    
    # Configurar mocks
    with patch.object(db_session, 'execute', new_callable=AsyncMock) as mock_execute:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_usuario
        mock_execute.return_value = mock_result
        
        with patch('app.core.security.pwd_context.verify', return_value=False):
            # Act & Assert
            with pytest.raises(AuthenticationException) as exc_info:
                await auth_service.change_password(
                    user_id=test_usuario.id,
                    current_password="WrongPassword",
                    new_password="NewPassword456!"
                )
            
            assert "contraseña actual" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_hash_token():
    """Test hash de tokens con SHA256."""
    # Arrange
    token = "test_token_123"
    
    # Act
    hashed = AuthService._hash_token(token)
    
    # Assert
    import hashlib
    expected = hashlib.sha256(token.encode()).hexdigest()
    assert hashed == expected
    assert len(hashed) == 64  # SHA256 produce 64 caracteres hex
