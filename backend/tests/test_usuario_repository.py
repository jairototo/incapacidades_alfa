"""
Tests unitarios para UsuarioRepository.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.usuario_repository import usuario_repository
from app.models.usuario import Usuario
from app.utils.enums import RolUsuario, EstadoUsuario, TipoDocumento


@pytest.fixture
async def test_usuario(db_session: AsyncSession) -> Usuario:
    """Fixture que crea un usuario de prueba."""
    usuario_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "nombre_completo": "Usuario Test",
        "rol": RolUsuario.EMPLEADO,
        "estado": EstadoUsuario.ACTIVO,
        "intentos_fallidos": 0,
        "token_version": 0
    }
    
    usuario = await usuario_repository.create(db_session, usuario_data)
    return usuario


@pytest.fixture
async def test_admin_usuario(db_session: AsyncSession) -> Usuario:
    """Fixture que crea un usuario administrador."""
    usuario_data = {
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": "hashed_admin_password",
        "nombre_completo": "Admin User",
        "rol": RolUsuario.ADMIN,
        "estado": EstadoUsuario.ACTIVO,
        "intentos_fallidos": 0,
        "token_version": 0
    }
    
    usuario = await usuario_repository.create(db_session, usuario_data)
    return usuario


class TestUsuarioRepository:
    """Tests para UsuarioRepository."""
    
    @pytest.mark.asyncio
    async def test_create_usuario(self, db_session: AsyncSession):
        """Test crear usuario."""
        usuario_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password_hash": "hashed_password",
            "nombre_completo": "New User",
            "rol": RolUsuario.AUDITOR,
            "estado": EstadoUsuario.ACTIVO,
            "intentos_fallidos": 0,
            "token_version": 0
        }
        
        usuario = await usuario_repository.create(db_session, usuario_data)
        
        assert usuario.id is not None
        assert usuario.username == "newuser"
        assert usuario.email == "newuser@example.com"
        assert usuario.rol == RolUsuario.AUDITOR
        assert usuario.estado == EstadoUsuario.ACTIVO
    
    @pytest.mark.asyncio
    async def test_get_by_username(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test obtener usuario por username."""
        usuario = await usuario_repository.get_by_username(db_session, "testuser")
        
        assert usuario is not None
        assert usuario.username == "testuser"
        assert usuario.id == test_usuario.id
    
    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, db_session: AsyncSession):
        """Test obtener usuario por username que no existe."""
        usuario = await usuario_repository.get_by_username(db_session, "noexiste")
        
        assert usuario is None
    
    @pytest.mark.asyncio
    async def test_get_by_email(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test obtener usuario por email."""
        usuario = await usuario_repository.get_by_email(db_session, "test@example.com")
        
        assert usuario is not None
        assert usuario.email == "test@example.com"
        assert usuario.id == test_usuario.id
    
    @pytest.mark.asyncio
    async def test_list_by_rol(self, db_session: AsyncSession, test_usuario: Usuario, test_admin_usuario: Usuario):
        """Test listar usuarios por rol."""
        # Listar ADMIN
        admins = await usuario_repository.list_by_rol(db_session, RolUsuario.ADMIN)
        assert len(admins) >= 1
        assert all(u.rol == RolUsuario.ADMIN for u in admins)
        
        # Listar EMPLEADO
        empleados = await usuario_repository.list_by_rol(db_session, RolUsuario.EMPLEADO)
        assert len(empleados) >= 1
        assert all(u.rol == RolUsuario.EMPLEADO for u in empleados)
    
    @pytest.mark.asyncio
    async def test_list_active(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test listar solo usuarios activos."""
        usuarios = await usuario_repository.list_active(db_session)
        
        assert len(usuarios) >= 1
        assert all(u.estado == EstadoUsuario.ACTIVO for u in usuarios)
    
    @pytest.mark.asyncio
    async def test_increment_failed_attempts(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test incrementar intentos fallidos."""
        await usuario_repository.increment_failed_attempts(db_session, test_usuario.id)
        await db_session.refresh(test_usuario)
        
        assert test_usuario.intentos_fallidos == 1
        
        # Incrementar de nuevo
        await usuario_repository.increment_failed_attempts(db_session, test_usuario.id)
        await db_session.refresh(test_usuario)
        
        assert test_usuario.intentos_fallidos == 2
    
    @pytest.mark.asyncio
    async def test_reset_failed_attempts(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test resetear intentos fallidos."""
        # Primero incrementar
        await usuario_repository.increment_failed_attempts(db_session, test_usuario.id)
        await usuario_repository.increment_failed_attempts(db_session, test_usuario.id)
        await db_session.refresh(test_usuario)
        assert test_usuario.intentos_fallidos == 2
        
        # Resetear
        await usuario_repository.reset_failed_attempts(db_session, test_usuario.id)
        await db_session.refresh(test_usuario)
        
        assert test_usuario.intentos_fallidos == 0
        assert test_usuario.bloqueado_hasta is None
    
    @pytest.mark.asyncio
    async def test_block_user(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test bloquear usuario."""
        bloqueado_hasta = datetime.now()  # Usar datetime.now() sin timezone
        
        await usuario_repository.block_user(db_session, test_usuario.id, bloqueado_hasta)
        await db_session.refresh(test_usuario)
        
        assert test_usuario.estado == EstadoUsuario.BLOQUEADO
        assert test_usuario.bloqueado_hasta is not None
    
    @pytest.mark.asyncio
    async def test_update_last_access(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test actualizar último acceso."""
        await usuario_repository.update_last_access(db_session, test_usuario.id)
        await db_session.refresh(test_usuario)
        
        assert test_usuario.ultimo_acceso is not None
    
    @pytest.mark.asyncio
    async def test_increment_token_version(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test incrementar versión de token."""
        version_inicial = test_usuario.token_version
        
        await usuario_repository.increment_token_version(db_session, test_usuario.id)
        await db_session.refresh(test_usuario)
        
        assert test_usuario.token_version == version_inicial + 1
    
    @pytest.mark.asyncio
    async def test_list_by_estado(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test listar por estado."""
        usuarios = await usuario_repository.list_by_estado(db_session, EstadoUsuario.ACTIVO)
        
        assert len(usuarios) >= 1
        assert all(u.estado == EstadoUsuario.ACTIVO for u in usuarios)
    
    @pytest.mark.asyncio
    async def test_search_usuarios(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test búsqueda de usuarios."""
        # Buscar por username
        resultados = await usuario_repository.search_usuarios(db_session, "test")
        assert len(resultados) >= 1
        assert any(u.username == "testuser" for u in resultados)
        
        # Buscar por email
        resultados = await usuario_repository.search_usuarios(db_session, "example.com")
        assert len(resultados) >= 1
        
        # Buscar por nombre
        resultados = await usuario_repository.search_usuarios(db_session, "Usuario")
        assert len(resultados) >= 1
    
    @pytest.mark.asyncio
    async def test_update_usuario(self, db_session: AsyncSession, test_usuario: Usuario):
        """Test actualizar usuario."""
        update_data = {
            "nombre_completo": "Usuario Actualizado",
            "rol": RolUsuario.AUDITOR
        }
        
        usuario = await usuario_repository.update(
            db_session,
            id=test_usuario.id,
            obj_in=update_data
        )
        
        assert usuario.nombre_completo == "Usuario Actualizado"
        assert usuario.rol == RolUsuario.AUDITOR
