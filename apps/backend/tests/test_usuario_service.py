"""
Tests unitarios para UsuarioService.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession 

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
    ConflictException
)
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.services.usuario_service import usuario_service
from app.utils.enums import RolUsuario, EstadoUsuario


@pytest.fixture
def mock_usuario():
    """Mock de un usuario."""
    return Usuario(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$hashed_password",
        nombre_completo="Test User",
        rol=RolUsuario.EMPLEADO,
        estado=EstadoUsuario.ACTIVO,
        intentos_fallidos=0,
        token_version=0,
        must_change_password=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_admin():
    """Mock de un administrador."""
    return Usuario(
        id=uuid4(),
        username="admin",
        email="admin@example.com",
        password_hash="$2b$12$hashed_admin_password",
        nombre_completo="Admin User",
        rol=RolUsuario.ADMIN,
        estado=EstadoUsuario.ACTIVO,
        intentos_fallidos=0,
        token_version=0,
        must_change_password=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestUsuarioService:
    """Tests para UsuarioService."""
    
    @pytest.mark.asyncio
    async def test_create_usuario_success(self, db_session: AsyncSession):
        """Test crear usuario exitosamente."""
        usuario_data = UsuarioCreate(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123",
            nombre_completo="New User",
            rol=RolUsuario.AUDITOR
        )
        
        with patch.object(usuario_service.repository, 'get_by_username', new_callable=AsyncMock) as mock_get_username, \
             patch.object(usuario_service.repository, 'get_by_email', new_callable=AsyncMock) as mock_get_email, \
             patch.object(usuario_service.repository, 'create', new_callable=AsyncMock) as mock_create:
            
            mock_get_username.return_value = None
            mock_get_email.return_value = None
            mock_create.return_value = Usuario(
                id=uuid4(),
                username="newuser",
                email="newuser@example.com",
                password_hash="hashed",
                nombre_completo="New User",
                rol=RolUsuario.AUDITOR,
                estado=EstadoUsuario.ACTIVO,
                intentos_fallidos=0,
                token_version=0
            )
            
            usuario = await usuario_service.create_usuario(
                db=db_session,
                usuario_data=usuario_data,
                created_by_rol=RolUsuario.ADMIN
            )
            
            assert usuario.username == "newuser"
            assert usuario.email == "newuser@example.com"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_usuario_non_admin_forbidden(self, db_session: AsyncSession):
        """Test que no-admin no puede crear usuarios."""
        usuario_data = UsuarioCreate(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123",
            nombre_completo="New User",
            rol=RolUsuario.AUDITOR
        )
        
        with pytest.raises(ForbiddenException):
            await usuario_service.create_usuario(
                db=db_session,
                usuario_data=usuario_data,
                created_by_rol=RolUsuario.EMPLEADO
            )
    
    @pytest.mark.asyncio
    async def test_create_usuario_duplicate_username(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test error al crear usuario con username duplicado."""
        usuario_data = UsuarioCreate(
            username="testuser",
            email="newemail@example.com",
            password="SecurePass123",
            nombre_completo="Test",
            rol=RolUsuario.EMPLEADO
        )
        
        with patch.object(usuario_service.repository, 'get_by_username', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_usuario
            
            with pytest.raises(ConflictException, match="username.*ya está en uso"):
                await usuario_service.create_usuario(
                    db=db_session,
                    usuario_data=usuario_data,
                    created_by_rol=RolUsuario.ADMIN
                )
    
    @pytest.mark.asyncio
    async def test_create_usuario_duplicate_email(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test error al crear usuario con email duplicado."""
        usuario_data = UsuarioCreate(
            username="newuser",
            email="test@example.com",
            password="SecurePass123",
            nombre_completo="Test",
            rol=RolUsuario.EMPLEADO
        )
        
        with patch.object(usuario_service.repository, 'get_by_username', new_callable=AsyncMock) as mock_get_username, \
             patch.object(usuario_service.repository, 'get_by_email', new_callable=AsyncMock) as mock_get_email:
            
            mock_get_username.return_value = None
            mock_get_email.return_value = mock_usuario
            
            with pytest.raises(ConflictException, match="email.*ya está registrado"):
                await usuario_service.create_usuario(
                    db=db_session,
                    usuario_data=usuario_data,
                    created_by_rol=RolUsuario.ADMIN
                )
    
    @pytest.mark.asyncio
    async def test_create_usuario_weak_password(self, db_session: AsyncSession):
        """Test error con contraseña débil."""
        # La validación de longitud mínima la hace Pydantic en el schema
        with pytest.raises(ValidationError):
            usuario_data = UsuarioCreate(
                username="newuser",
                email="newuser@example.com",
                password="weak",  # Sin mayúsculas, sin números
                nombre_completo="Test",
                rol=RolUsuario.EMPLEADO
            )
    
    @pytest.mark.asyncio
    async def test_create_usuario_invalid_username(self, db_session: AsyncSession):
        """Test error con username inválido."""
        # La validación de longitud mínima la hace Pydantic en el schema
        with pytest.raises(ValidationError):
            usuario_data = UsuarioCreate(
                username="ab",  # Muy corto
                email="test@example.com",
                password="SecurePass123",
                nombre_completo="Test",
                rol=RolUsuario.EMPLEADO
            )
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test cambiar contraseña exitosamente."""
        with patch.object(usuario_service.repository, 'get_by_id', new_callable=AsyncMock) as mock_get, \
             patch.object(usuario_service.repository, 'update', new_callable=AsyncMock) as mock_update, \
             patch('app.core.security.pwd_context.verify') as mock_verify, \
             patch('app.core.security.pwd_context.hash') as mock_hash:
            
            mock_get.return_value = mock_usuario
            mock_verify.return_value = True
            mock_hash.return_value = "new_hashed_password"
            mock_update.return_value = mock_usuario
            
            result = await usuario_service.change_password(
                db=db_session,
                usuario_id=mock_usuario.id,
                current_password="OldPass123",
                new_password="NewSecurePass456"
            )
            
            assert result == mock_usuario
            mock_verify.assert_called_once()
            mock_hash.assert_called_once_with("NewSecurePass456")
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test error al cambiar contraseña con contraseña actual incorrecta."""
        with patch.object(usuario_service.repository, 'get_by_id', new_callable=AsyncMock) as mock_get, \
             patch('app.core.security.pwd_context.verify') as mock_verify:
            
            mock_get.return_value = mock_usuario
            mock_verify.return_value = False
            
            with pytest.raises(BadRequestException, match="contraseña actual es incorrecta"):
                await usuario_service.change_password(
                    db=db_session,
                    usuario_id=mock_usuario.id,
                    current_password="WrongPassword",
                    new_password="NewSecurePass456"
                )
    
    @pytest.mark.asyncio
    async def test_reset_password_by_admin(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test resetear contraseña por admin."""
        with patch.object(usuario_service.repository, 'get_by_id', new_callable=AsyncMock) as mock_get, \
             patch.object(usuario_service.repository, 'update', new_callable=AsyncMock) as mock_update, \
             patch.object(usuario_service.repository, 'increment_token_version', new_callable=AsyncMock) as mock_increment, \
             patch('app.core.security.pwd_context.hash') as mock_hash:
            
            mock_get.return_value = mock_usuario
            mock_update.return_value = mock_usuario
            mock_hash.return_value = "temp_hashed_password"
            
            usuario, temp_password = await usuario_service.reset_password(
                db=db_session,
                usuario_id=mock_usuario.id,
                admin_rol=RolUsuario.ADMIN
            )
            
            assert usuario == mock_usuario
            assert len(temp_password) == 12
            mock_increment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reset_password_non_admin_forbidden(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test que no-admin no puede resetear contraseñas."""
        with pytest.raises(ForbiddenException):
            await usuario_service.reset_password(
                db=db_session,
                usuario_id=mock_usuario.id,
                admin_rol=RolUsuario.EMPLEADO
            )
    
    @pytest.mark.asyncio
    async def test_activate_usuario(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test activar usuario."""
        mock_usuario.estado = EstadoUsuario.INACTIVO
        
        with patch.object(usuario_service.repository, 'get_by_id', new_callable=AsyncMock) as mock_get, \
             patch.object(usuario_service.repository, 'update', new_callable=AsyncMock) as mock_update:
            
            mock_get.return_value = mock_usuario
            mock_update.return_value = mock_usuario
            
            result = await usuario_service.activate_usuario(
                db=db_session,
                usuario_id=mock_usuario.id,
                admin_rol=RolUsuario.ADMIN
            )
            
            assert result == mock_usuario
            mock_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_usuario(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test desactivar usuario."""
        with patch.object(usuario_service.repository, 'get_by_id', new_callable=AsyncMock) as mock_get, \
             patch.object(usuario_service.repository, 'update', new_callable=AsyncMock) as mock_update, \
             patch.object(usuario_service.repository, 'increment_token_version', new_callable=AsyncMock) as mock_increment:
            
            mock_get.return_value = mock_usuario
            mock_update.return_value = mock_usuario
            
            result = await usuario_service.deactivate_usuario(
                db=db_session,
                usuario_id=mock_usuario.id,
                admin_rol=RolUsuario.ADMIN
            )
            
            assert result == mock_usuario
            mock_increment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_rol_success(self, db_session: AsyncSession, mock_usuario: Usuario, mock_admin: Usuario):
        """Test asignar rol exitosamente."""
        with patch.object(usuario_service.repository, 'get_by_id', new_callable=AsyncMock) as mock_get, \
             patch.object(usuario_service.repository, 'update', new_callable=AsyncMock) as mock_update, \
             patch.object(usuario_service.repository, 'increment_token_version', new_callable=AsyncMock) as mock_increment:
            
            mock_get.return_value = mock_usuario
            mock_update.return_value = mock_usuario
            
            result = await usuario_service.assign_rol(
                db=db_session,
                usuario_id=mock_usuario.id,
                new_rol=RolUsuario.AUDITOR,
                admin_id=mock_admin.id,
                admin_rol=RolUsuario.ADMIN
            )
            
            assert result == mock_usuario
            mock_increment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_rol_to_self_forbidden(self, db_session: AsyncSession, mock_admin: Usuario):
        """Test que admin no puede cambiar su propio rol."""
        with pytest.raises(ForbiddenException, match="No puedes modificar tu propio rol"):
            await usuario_service.assign_rol(
                db=db_session,
                usuario_id=mock_admin.id,
                new_rol=RolUsuario.EMPLEADO,
                admin_id=mock_admin.id,
                admin_rol=RolUsuario.ADMIN
            )
    
    @pytest.mark.asyncio
    async def test_handle_failed_login(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test manejar login fallido."""
        with patch.object(usuario_service.repository, 'increment_failed_attempts', new_callable=AsyncMock) as mock_increment:
            await usuario_service.handle_failed_login(db=db_session, usuario=mock_usuario)
            mock_increment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_failed_login_blocks_after_max_attempts(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test que se bloquea el usuario después de MAX_FAILED_ATTEMPTS."""
        mock_usuario.intentos_fallidos = 4  # Uno antes del límite
        
        with patch.object(usuario_service.repository, 'increment_failed_attempts', new_callable=AsyncMock) as mock_increment, \
             patch.object(usuario_service.repository, 'block_user', new_callable=AsyncMock) as mock_block:
            
            await usuario_service.handle_failed_login(db=db_session, usuario=mock_usuario)
            
            mock_increment.assert_called_once()
            mock_block.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_successful_login(self, db_session: AsyncSession, mock_usuario: Usuario):
        """Test manejar login exitoso."""
        with patch.object(usuario_service.repository, 'reset_failed_attempts', new_callable=AsyncMock) as mock_reset, \
             patch.object(usuario_service.repository, 'update_last_access', new_callable=AsyncMock) as mock_update_access:
            
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session.refresh = AsyncMock()
            
            result = await usuario_service.handle_successful_login(db=mock_session, usuario=mock_usuario)

            mock_reset.assert_called_once()
            mock_update_access.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_usuarios_combines_rol_and_estado_filters(self, db_session: AsyncSession):
        """
        Regression test (Finding 3, final review): list_usuarios(rol=AUDITOR, estado=ACTIVO)
        debe aplicar AMBOS filtros con AND, no solo el primero de un chain if/elif.

        Antes del fix, pasar rol Y estado solo aplicaba el filtro de rol
        (elif estado nunca se evaluaba), por lo que un auditor INACTIVO
        aparecía igual en la lista de "Auditor asignado" de la bandeja.
        """
        activo = await usuario_service.repository.create(db_session, {
            "username": "auditor.activo.filtro",
            "email": "auditor.activo.filtro@example.com",
            "password_hash": "hashed",
            "nombre_completo": "Auditor Activo Filtro",
            "rol": RolUsuario.AUDITOR,
            "estado": EstadoUsuario.ACTIVO,
            "intentos_fallidos": 0,
            "token_version": 0,
        })
        inactivo = await usuario_service.repository.create(db_session, {
            "username": "auditor.inactivo.filtro",
            "email": "auditor.inactivo.filtro@example.com",
            "password_hash": "hashed",
            "nombre_completo": "Auditor Inactivo Filtro",
            "rol": RolUsuario.AUDITOR,
            "estado": EstadoUsuario.INACTIVO,
            "intentos_fallidos": 0,
            "token_version": 0,
        })

        resultados = await usuario_service.list_usuarios(
            db_session, rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO
        )

        ids = {u.id for u in resultados}
        assert activo.id in ids
        assert inactivo.id not in ids
