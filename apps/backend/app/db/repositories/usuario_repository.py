"""
Repository para operaciones de base de datos de Usuario.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.usuario import Usuario
from app.utils.enums import RolUsuario, EstadoUsuario


class UsuarioRepository(BaseRepository[Usuario]):
    """Repository para Usuario con operaciones específicas."""

    def __init__(self):
        """Inicializa el repository con el modelo Usuario."""
        super().__init__(Usuario)

    async def get_by_username(
        self,
        db: AsyncSession,
        username: str
    ) -> Optional[Usuario]:
        """
        Obtiene un usuario por su nombre de usuario.
        
        Args:
            db: Sesión de base de datos
            username: Nombre de usuario
            
        Returns:
            Usuario si existe, None si no
        """
        query = select(Usuario).where(Usuario.username == username)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> Optional[Usuario]:
        """
        Obtiene un usuario por su email.
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            
        Returns:
            Usuario si existe, None si no
        """
        query = select(Usuario).where(Usuario.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_rol(
        self,
        db: AsyncSession,
        rol: RolUsuario,
        skip: int = 0,
        limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene usuarios por rol.
        
        Args:
            db: Sesión de base de datos
            rol: Rol a filtrar
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de usuarios con el rol especificado
        """
        query = select(Usuario).where(
            Usuario.rol == rol
        ).order_by(
            Usuario.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def list_active(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene solo usuarios activos.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de usuarios activos
        """
        query = select(Usuario).where(
            Usuario.estado == EstadoUsuario.ACTIVO
        ).order_by(
            Usuario.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def increment_failed_attempts(
        self,
        db: AsyncSession,
        usuario_id: UUID
    ) -> Usuario:
        """
        Incrementa el contador de intentos fallidos.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            
        Returns:
            Usuario actualizado
        """
        usuario = await self.get_by_id(db, usuario_id)
        if usuario:
            usuario.intentos_fallidos += 1
            await db.commit()
            await db.refresh(usuario)
        return usuario

    async def reset_failed_attempts(
        self,
        db: AsyncSession,
        usuario_id: UUID
    ) -> Usuario:
        """
        Resetea el contador de intentos fallidos.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            
        Returns:
            Usuario actualizado
        """
        usuario = await self.get_by_id(db, usuario_id)
        if usuario:
            usuario.intentos_fallidos = 0
            usuario.bloqueado_hasta = None
            await db.commit()
            await db.refresh(usuario)
        return usuario

    async def block_user(
        self,
        db: AsyncSession,
        usuario_id: UUID,
        bloqueado_hasta: datetime
    ) -> Usuario:
        """
        Bloquea un usuario hasta una fecha específica.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            bloqueado_hasta: Fecha hasta la cual estará bloqueado
            
        Returns:
            Usuario actualizado
        """
        usuario = await self.get_by_id(db, usuario_id)
        if usuario:
            usuario.bloqueado_hasta = bloqueado_hasta
            usuario.estado = EstadoUsuario.BLOQUEADO
            await db.commit()
            await db.refresh(usuario)
        return usuario

    async def update_last_access(
        self,
        db: AsyncSession,
        usuario_id: UUID
    ) -> Usuario:
        """
        Actualiza la fecha de último acceso.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            
        Returns:
            Usuario actualizado
        """
        usuario = await self.get_by_id(db, usuario_id)
        if usuario:
            usuario.ultimo_acceso = datetime.utcnow()
            await db.commit()
            await db.refresh(usuario)
        return usuario

    async def increment_token_version(
        self,
        db: AsyncSession,
        usuario_id: UUID
    ) -> Usuario:
        """
        Incrementa la versión del token para invalidar todos los tokens existentes.
        
        Args:
            db: Sesión de base de datos
            usuario_id: ID del usuario
            
        Returns:
            Usuario actualizado
        """
        usuario = await self.get_by_id(db, usuario_id)
        if usuario:
            usuario.token_version += 1
            await db.commit()
            await db.refresh(usuario)
        return usuario

    async def list_by_estado(
        self,
        db: AsyncSession,
        estado: EstadoUsuario,
        skip: int = 0,
        limit: int = 100
    ) -> List[Usuario]:
        """
        Obtiene usuarios por estado.
        
        Args:
            db: Sesión de base de datos
            estado: Estado a filtrar
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de usuarios con el estado especificado
        """
        query = select(Usuario).where(
            Usuario.estado == estado
        ).order_by(
            Usuario.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def search_usuarios(
        self,
        db: AsyncSession,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Usuario]:
        """
        Busca usuarios por nombre, username o email.
        
        Args:
            db: Sesión de base de datos
            search_term: Término de búsqueda
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de usuarios que coinciden con la búsqueda
        """
        search_pattern = f"%{search_term}%"
        query = select(Usuario).where(
            (Usuario.username.ilike(search_pattern)) |
            (Usuario.email.ilike(search_pattern)) |
            (Usuario.nombre_completo.ilike(search_pattern))
        ).order_by(
            Usuario.created_at.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())


# Singleton
usuario_repository = UsuarioRepository()
