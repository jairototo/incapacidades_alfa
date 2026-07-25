"""
Service para lógica de negocio de Usuario con gestión de roles y seguridad.
"""
import re
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
    ConflictException
)
from app.core.security import pwd_context
from app.db.repositories.usuario_repository import usuario_repository
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.utils.enums import RolUsuario, EstadoUsuario


class UsuarioService:
    """Service para operaciones de negocio de Usuario."""

    # Configuración de bloqueo
    MAX_FAILED_ATTEMPTS = 5
    BLOCK_DURATION_MINUTES = 30

    def __init__(self):
        """Inicializa el service con el repository."""
        self.repository = usuario_repository

    def _validate_username(self, username: str) -> None:
        """
        Valida el formato del username.
        
        Args:
            username: Username a validar
            
        Raises:
            BadRequestException: Si el formato es inválido
        """
        # Solo alfanuméricos, guión bajo y punto, 3-50 caracteres
        if not re.match(r'^[a-zA-Z0-9_.]{3,50}$', username):
            raise BadRequestException(
                "Username debe tener entre 3-50 caracteres y solo contener letras, números, guión bajo o punto"
            )

    def _validate_password_strength(self, password: str) -> None:
        """
        Valida la fortaleza de la contraseña.
        
        Args:
            password: Contraseña a validar
            
        Raises:
            BadRequestException: Si la contraseña no es suficientemente fuerte
        """
        if len(password) < 8:
            raise BadRequestException("La contraseña debe tener al menos 8 caracteres")
        
        if not re.search(r'[A-Z]', password):
            raise BadRequestException("La contraseña debe contener al menos una letra mayúscula")
        
        if not re.search(r'[a-z]', password):
            raise BadRequestException("La contraseña debe contener al menos una letra minúscula")
        
        if not re.search(r'[0-9]', password):
            raise BadRequestException("La contraseña debe contener al menos un número")

    def _generate_temp_password(self) -> str:
        """
        Genera una contraseña temporal segura.
        
        Returns:
            Contraseña temporal
        """
        # Generar contraseña de 12 caracteres con mayúsculas, minúsculas y números
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Asegurar que tenga al menos una mayúscula, minúscula y número
        password = list(password)
        password[0] = secrets.choice(string.ascii_uppercase)
        password[1] = secrets.choice(string.ascii_lowercase)
        password[2] = secrets.choice(string.digits)
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)

    async def create_usuario(
        self,
        db: AsyncSession,
        usuario_data: UsuarioCreate,
        created_by_rol: Optional[RolUsuario] = None
    ) -> Usuario:
        """
        Crea un nuevo usuario con validaciones.
        
        Args:
            db: Sesión de base de datos
            usuario_data: Datos del usuario
            created_by_rol: Rol del usuario que crea (para validar permisos)
            
        Returns:
            Usuario creado
            
        Raises:
            ForbiddenException: Si no tiene permisos
            ConflictException: Si username o email ya existen
            BadRequestException: Si las validaciones fallan
        """
        # Validar permisos (solo ADMIN puede crear usuarios)
        if created_by_rol and created_by_rol != RolUsuario.ADMIN:
            raise ForbiddenException("Solo los ADMIN pueden crear usuarios")
        
        # Validar formato de username
        self._validate_username(usuario_data.username)
        
        # Validar fortaleza de contraseña
        self._validate_password_strength(usuario_data.password)
        
        # Validar rol válido
        try:
            RolUsuario(usuario_data.rol)
        except ValueError:
            raise BadRequestException(f"Rol inválido: {usuario_data.rol}")
        
        # Validar unicidad de username
        existing = await self.repository.get_by_username(db, usuario_data.username)
        if existing:
            raise ConflictException(f"El username '{usuario_data.username}' ya está en uso")
        
        # Validar unicidad de email
        existing = await self.repository.get_by_email(db, usuario_data.email)
        if existing:
            raise ConflictException(f"El email '{usuario_data.email}' ya está registrado")
        
        # Hashear contraseña
        password_hash = pwd_context.hash(usuario_data.password)
        
        # Crear usuario
        usuario_dict = usuario_data.model_dump(exclude={'password'})
        usuario_dict['password_hash'] = password_hash
        usuario_dict['estado'] = EstadoUsuario.ACTIVO
        usuario_dict['intentos_fallidos'] = 0
        usuario_dict['token_version'] = 0
        
        usuario = await self.repository.create(db, usuario_dict)
        
        return usuario

    async def update_usuario(
        self,
        db: AsyncSession,
        usuario_id: UUID,
        update_data: UsuarioUpdate,
        updated_by_rol: Optional[RolUsuario] = None
    ) -> Usuario:
        """
        Actualiza un usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario a actualizar
            update_data: Datos a actualizar
            updated_by_rol: Rol del usuario que actualiza
            
        Returns:
            Usuario actualizado
            
        Raises:
            NotFoundException: Si el usuario no existe
            ForbiddenException: Si no tiene permisos
            ConflictException: Si email ya existe
        """
        # Obtener usuario
        usuario = await self.repository.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundException(f"Usuario {usuario_id} no encontrado")
        
        # Validar permisos
        if updated_by_rol and updated_by_rol != RolUsuario.ADMIN:
            raise ForbiddenException("Solo los ADMIN pueden actualizar usuarios")
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Si se actualiza email, validar unicidad
        if 'email' in update_dict and update_dict['email'] != usuario.email:
            existing = await self.repository.get_by_email(db, update_dict['email'])
            if existing:
                raise ConflictException(f"El email '{update_dict['email']}' ya está registrado")
        
        # Si se actualiza rol, validar que sea válido
        if 'rol' in update_dict:
            try:
                RolUsuario(update_dict['rol'])
            except ValueError:
                raise BadRequestException(f"Rol inválido: {update_dict['rol']}")
        
        return await self.repository.update(db, id=usuario_id, obj_in=update_dict)

    async def change_password(
        self,
        db: AsyncSession,
        usuario_id: UUID,
        current_password: str,
        new_password: str
    ) -> Usuario:
        """
        Cambia la contraseña de un usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            Usuario actualizado
            
        Raises:
            NotFoundException: Si el usuario no existe
            BadRequestException: Si la contraseña actual es incorrecta o la nueva es débil
        """
        # Obtener usuario
        usuario = await self.repository.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundException(f"Usuario {usuario_id} no encontrado")
        
        # Verificar contraseña actual
        if not pwd_context.verify(current_password, usuario.password_hash):
            raise BadRequestException("La contraseña actual es incorrecta")
        
        # Validar fortaleza de nueva contraseña
        self._validate_password_strength(new_password)
        
        # Hashear nueva contraseña
        new_password_hash = pwd_context.hash(new_password)
        
        # Actualizar
        update_dict = {
            'password_hash': new_password_hash,
            'must_change_password': False
        }
        
        return await self.repository.update(db, id=usuario_id, obj_in=update_dict)

    async def reset_password(
        self,
        db: AsyncSession,
        usuario_id: UUID,
        admin_rol: RolUsuario,
        new_password: Optional[str] = None
    ) -> tuple[Usuario, str]:
        """
        Resetea la contraseña de un usuario (solo ADMIN).
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            admin_rol: Rol del administrador
            new_password: Nueva contraseña (si no se proporciona, se genera una temporal)
            
        Returns:
            Tupla con (Usuario actualizado, contraseña temporal)
            
        Raises:
            NotFoundException: Si el usuario no existe
            ForbiddenException: Si no es ADMIN
        """
        # Validar permisos
        if admin_rol != RolUsuario.ADMIN:
            raise ForbiddenException("Solo los ADMIN pueden resetear contraseñas")
        
        # Obtener usuario
        usuario = await self.repository.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundException(f"Usuario {usuario_id} no encontrado")
        
        # Generar o usar contraseña proporcionada
        temp_password = new_password or self._generate_temp_password()
        
        # Validar si se proporcionó contraseña
        if new_password:
            self._validate_password_strength(new_password)
        
        # Hashear contraseña
        new_password_hash = pwd_context.hash(temp_password)
        
        # Actualizar
        update_dict = {
            'password_hash': new_password_hash,
            'must_change_password': True,
            'intentos_fallidos': 0,
            'bloqueado_hasta': None,
            'estado': EstadoUsuario.ACTIVO
        }
        
        usuario = await self.repository.update(db, id=usuario_id, obj_in=update_dict)
        
        # Invalidar todos los tokens existentes
        await self.repository.increment_token_version(db, usuario_id)
        
        return usuario, temp_password

    async def activate_usuario(
        self,
        db: AsyncSession,
        usuario_id: UUID,
        admin_rol: RolUsuario
    ) -> Usuario:
        """
        Activa un usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            admin_rol: Rol del administrador
            
        Returns:
            Usuario actualizado
            
        Raises:
            NotFoundException: Si el usuario no existe
            ForbiddenException: Si no es ADMIN
        """
        if admin_rol != RolUsuario.ADMIN:
            raise ForbiddenException("Solo los ADMIN pueden activar usuarios")
        
        usuario = await self.repository.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundException(f"Usuario {usuario_id} no encontrado")
        
        update_dict = {
            'estado': EstadoUsuario.ACTIVO,
            'intentos_fallidos': 0,
            'bloqueado_hasta': None
        }
        
        return await self.repository.update(db, id=usuario_id, obj_in=update_dict)

    async def deactivate_usuario(
        self,
        db: AsyncSession,
        usuario_id: UUID,
        admin_rol: RolUsuario
    ) -> Usuario:
        """
        Desactiva un usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            admin_rol: Rol del administrador
            
        Returns:
            Usuario actualizado
            
        Raises:
            NotFoundException: Si el usuario no existe
            ForbiddenException: Si no es ADMIN
        """
        if admin_rol != RolUsuario.ADMIN:
            raise ForbiddenException("Solo los ADMIN pueden desactivar usuarios")
        
        usuario = await self.repository.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundException(f"Usuario {usuario_id} no encontrado")
        
        update_dict = {'estado': EstadoUsuario.INACTIVO}
        
        # Invalidar todos los tokens
        await self.repository.increment_token_version(db, usuario_id)
        
        return await self.repository.update(db, id=usuario_id, obj_in=update_dict)

    async def reporte_auditores(
        self,
        db: AsyncSession,
        admin_rol: RolUsuario,
    ) -> List[Usuario]:
        """
        Lista todos los usuarios AUDITOR con su sucursal y carga activa actual.

        Requiere rol ADMIN.
        """
        if admin_rol != RolUsuario.ADMIN:
            raise ForbiddenException("Solo los ADMIN pueden ver el reporte de auditores")

        return await self.repository.list_by_rol(db, RolUsuario.AUDITOR, skip=0, limit=1000)

    async def assign_rol(
        self,
        db: AsyncSession,
        usuario_id: UUID,
        new_rol: RolUsuario,
        admin_id: UUID,
        admin_rol: RolUsuario
    ) -> Usuario:
        """
        Asigna un nuevo rol a un usuario.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            new_rol: Nuevo rol a asignar
            admin_id: ID del administrador que asigna
            admin_rol: Rol del administrador
            
        Returns:
            Usuario actualizado
            
        Raises:
            NotFoundException: Si el usuario no existe
            ForbiddenException: Si no es ADMIN o intenta modificar su propio rol
            BadRequestException: Si el rol es inválido
        """
        if admin_rol != RolUsuario.ADMIN:
            raise ForbiddenException("Solo los ADMIN pueden asignar roles")
        
        # No permitir que un admin cambie su propio rol
        if usuario_id == admin_id:
            raise ForbiddenException("No puedes modificar tu propio rol")
        
        usuario = await self.repository.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundException(f"Usuario {usuario_id} no encontrado")
        
        # Validar rol
        try:
            RolUsuario(new_rol)
        except ValueError:
            raise BadRequestException(f"Rol inválido: {new_rol}")
        
        update_dict = {'rol': new_rol}
        
        # Invalidar tokens si cambia de rol
        await self.repository.increment_token_version(db, usuario_id)
        
        return await self.repository.update(db, id=usuario_id, obj_in=update_dict)

    async def handle_failed_login(
        self,
        db: AsyncSession,
        usuario: Usuario
    ) -> None:
        """
        Maneja un intento fallido de login.
        
        Args:
            db: Sesión de base de datos
            usuario: Usuario que falló el login
        """
        await self.repository.increment_failed_attempts(db, usuario.id)
        
        if usuario.intentos_fallidos + 1 >= self.MAX_FAILED_ATTEMPTS:
            bloqueado_hasta = datetime.utcnow() + timedelta(minutes=self.BLOCK_DURATION_MINUTES)
            await self.repository.block_user(db, usuario.id, bloqueado_hasta)

    async def handle_successful_login(
        self,
        db: AsyncSession,
        usuario: Usuario
    ) -> Usuario:
        """
        Maneja un login exitoso.
        
        Args:
            db: Sesión de base de datos
            usuario: Usuario que hizo login
            
        Returns:
            Usuario actualizado
        """
        # Resetear intentos fallidos
        await self.repository.reset_failed_attempts(db, usuario.id)
        
        # Actualizar último acceso
        await self.repository.update_last_access(db, usuario.id)
        
        # Refrescar y retornar
        await db.refresh(usuario)
        return usuario

    async def get_usuario(
        self,
        db: AsyncSession,
        usuario_id: UUID
    ) -> Usuario:
        """
        Obtiene un usuario por ID.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            
        Returns:
            Usuario
            
        Raises:
            NotFoundException: Si no existe
        """
        usuario = await self.repository.get_by_id(db, usuario_id)
        if not usuario:
            raise NotFoundException(f"Usuario {usuario_id} no encontrado")
        
        return usuario

    async def list_usuarios(
        self,
        db: AsyncSession,
        rol: Optional[RolUsuario] = None,
        estado: Optional[EstadoUsuario] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Usuario]:
        """
        Lista usuarios con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            rol: Filtrar por rol
            estado: Filtrar por estado
            search: Término de búsqueda
            skip: Registros a saltar
            limit: Límite de registros
            
        Returns:
            Lista de usuarios
        """
        if search:
            return await self.repository.search_usuarios(db, search, skip, limit)
        elif rol:
            return await self.repository.list_by_rol(db, rol, skip, limit)
        elif estado:
            return await self.repository.list_by_estado(db, estado, skip, limit)
        else:
            return await self.repository.list_all(db, skip, limit)


# Singleton
usuario_service = UsuarioService()
