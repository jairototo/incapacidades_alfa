"""
Servicio de autenticación.
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from app.core.exceptions import (
    UnauthorizedException,
    NotFoundException,
    BadRequestException,
    ForbiddenException
)
from app.models.usuario import Usuario
from app.models.refresh_token import RefreshToken
from app.schemas.auth import (
    TokenResponse,
    UserProfileResponse,
    LoginResponse
)


class AuthService:
    """Servicio para autenticación y gestión de tokens."""
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio.
        
        Args:
            db: Sesión de base de datos
        """
        self.db = db
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hashea un token para almacenamiento seguro.
        
        Args:
            token: Token en texto plano
            
        Returns:
            Token hasheado con SHA256
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def login(
        self,
        username: str,
        password: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> LoginResponse:
        """
        Autentica un usuario y genera tokens.
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            user_agent: User agent del cliente
            ip_address: Dirección IP del cliente
            
        Returns:
            Respuesta de login con tokens y perfil de usuario
            
        Raises:
            UnauthorizedException: Si las credenciales son inválidas
        """
        # Buscar usuario
        query = select(Usuario).where(Usuario.email == username)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"Intento de login fallido: usuario '{username}' no encontrado")
            raise UnauthorizedException("Credenciales inválidas")
        
        # Verificar contraseña
        if not verify_password(password, user.password_hash):
            # Incrementar intentos fallidos
            user.increment_failed_attempts()
            await self.db.commit()
            
            logger.warning(
                f"Intento de login fallido para usuario '{username}' "
                f"(intentos: {user.intentos_fallidos})"
            )
            raise UnauthorizedException("Credenciales inválidas")
        
        # Verificar que el usuario esté activo
        if not user.is_active:
            logger.warning(f"Intento de login de usuario inactivo: '{username}'")
            raise ForbiddenException("Usuario inactivo o bloqueado")
        
        # Resetear intentos fallidos
        user.reset_failed_attempts()
        
        # Generar tokens
        access_token, refresh_token_str = await self._create_user_tokens(
            user=user,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        await self.db.commit()
        
        logger.info(f"Login exitoso para usuario: '{username}'")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserProfileResponse.model_validate(user)
        )
    
    async def _create_user_tokens(
        self,
        user: Usuario,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Crea access y refresh tokens para un usuario.
        
        Args:
            user: Usuario
            user_agent: User agent del cliente
            ip_address: Dirección IP del cliente
            
        Returns:
            Tupla (access_token, refresh_token)
        """
        # Crear access token
        access_token_data = {
            "sub": str(user.id),
            "username": user.username,
            "rol": user.rol,
            "token_version": user.token_version
        }
        access_token = create_access_token(access_token_data)
        
        # Crear refresh token
        refresh_token_data = {
            "sub": str(user.id),
            "token_version": user.token_version
        }
        refresh_token_str = create_refresh_token(refresh_token_data)
        
        # Almacenar refresh token hasheado en BD
        token_hash = self._hash_token(refresh_token_str)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        refresh_token_db = RefreshToken(
            usuario_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            token_version=user.token_version
        )
        
        self.db.add(refresh_token_db)
        
        # Limpiar tokens expirados del usuario
        await self._cleanup_expired_tokens(user.id)
        
        return access_token, refresh_token_str
    
    async def refresh_access_token(
        self,
        refresh_token_str: str
    ) -> TokenResponse:
        """
        Renueva el access token usando un refresh token.
        
        Args:
            refresh_token_str: Refresh token
            
        Returns:
            Nueva respuesta de token
            
        Raises:
            UnauthorizedException: Si el refresh token es inválido
        """
        from jose import jwt, JWTError
        
        # Decodificar refresh token
        try:
            payload = jwt.decode(
                refresh_token_str,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            user_id: str = payload.get("sub")
            token_version: int = payload.get("token_version")
            
            if user_id is None:
                raise UnauthorizedException("Token inválido")
        except JWTError:
            raise UnauthorizedException("Token inválido o expirado")
        
        # Buscar refresh token en BD
        token_hash = self._hash_token(refresh_token_str)
        query = select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False
            )
        )
        result = await self.db.execute(query)
        refresh_token_db = result.scalar_one_or_none()
        
        if not refresh_token_db or not refresh_token_db.is_valid:
            logger.warning(f"Intento de refresh con token inválido para usuario: {user_id}")
            raise UnauthorizedException("Token inválido o expirado")
        
        # Verificar versión del token
        if refresh_token_db.token_version != token_version:
            logger.warning(
                f"Token version mismatch para usuario {user_id}: "
                f"token={token_version}, db={refresh_token_db.token_version}"
            )
            raise UnauthorizedException("Token inválido")
        
        # Buscar usuario
        query = select(Usuario).where(Usuario.id == UUID(user_id))
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise UnauthorizedException("Usuario no encontrado o inactivo")
        
        # Verificar versión del usuario
        if user.token_version != token_version:
            logger.warning(
                f"User token version mismatch para usuario {user_id}: "
                f"user={user.token_version}, token={token_version}"
            )
            raise UnauthorizedException("Token invalidado")
        
        # Crear nuevo access token
        access_token_data = {
            "sub": str(user.id),
            "username": user.username,
            "rol": user.rol,
            "token_version": user.token_version
        }
        access_token = create_access_token(access_token_data)
        
        logger.info(f"Access token renovado para usuario: {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,  # Reusar el mismo refresh token
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def logout(
        self,
        refresh_token_str: str
    ) -> None:
        """
        Cierra sesión revocando el refresh token.
        
        Args:
            refresh_token_str: Refresh token a revocar
        """
        token_hash = self._hash_token(refresh_token_str)
        
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(query)
        refresh_token_db = result.scalar_one_or_none()
        
        if refresh_token_db:
            refresh_token_db.revoke()
            await self.db.commit()
            logger.info(f"Logout exitoso para usuario: {refresh_token_db.usuario_id}")
    
    async def logout_all_sessions(
        self,
        user_id: UUID
    ) -> None:
        """
        Cierra todas las sesiones de un usuario incrementando token_version.
        
        Args:
            user_id: ID del usuario
        """
        query = select(Usuario).where(Usuario.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.token_version += 1
            await self.db.commit()
            logger.info(f"Todas las sesiones cerradas para usuario: {user.username}")
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> None:
        """
        Cambia la contraseña de un usuario.
        
        Args:
            user_id: ID del usuario
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Raises:
            UnauthorizedException: Si la contraseña actual es incorrecta
            NotFoundException: Si el usuario no existe
        """
        query = select(Usuario).where(Usuario.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException("Usuario no encontrado")
        
        # Verificar contraseña actual
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedException("Contraseña actual incorrecta")
        
        # Actualizar contraseña
        user.password_hash = get_password_hash(new_password)
        user.must_change_password = False
        
        # Incrementar token_version para invalidar todos los tokens existentes
        user.token_version += 1
        
        await self.db.commit()
        
        logger.info(f"Contraseña cambiada para usuario: {user.username}")
    
    async def _cleanup_expired_tokens(
        self,
        user_id: UUID,
        keep_last_n: int = 5
    ) -> None:
        """
        Limpia tokens expirados y mantiene solo los últimos N tokens válidos.
        
        Args:
            user_id: ID del usuario
            keep_last_n: Número de tokens a mantener
        """
        # Eliminar tokens expirados
        query = select(RefreshToken).where(
            and_(
                RefreshToken.usuario_id == user_id,
                RefreshToken.expires_at < datetime.utcnow()
            )
        )
        result = await self.db.execute(query)
        expired_tokens = result.scalars().all()
        
        for token in expired_tokens:
            await self.db.delete(token)
        
        # Mantener solo los últimos N tokens válidos
        query = (
            select(RefreshToken)
            .where(
                and_(
                    RefreshToken.usuario_id == user_id,
                    RefreshToken.revoked == False,
                    RefreshToken.expires_at >= datetime.utcnow()
                )
            )
            .order_by(RefreshToken.created_at.desc())
        )
        result = await self.db.execute(query)
        valid_tokens = result.scalars().all()
        
        if len(valid_tokens) > keep_last_n:
            for token in valid_tokens[keep_last_n:]:
                token.revoke()
