"""
Seguridad: JWT, hashing de passwords, RBAC.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.db.session import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar contraseña.
    
    Bcrypt tiene un límite de 72 bytes para las contraseñas.
    Si la contraseña es más larga, se trunca automáticamente.
    """
    # Truncar a 72 bytes (límite de bcrypt)
    # logger.info(f"Verificando contraseña{pwd_context.hash(plain_password)}")
    # logger.info(f"Hashed password: {hashed_password}")
    # if len(plain_password.encode('utf-8')) > 72:
    #     logger.warning("La contraseña excede los 72 bytes y será truncada para verificación.")
    #     plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError as e:
        logger.error(f"Error verificando contraseña: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Generar hash de contraseña.
    
    Bcrypt tiene un límite de 72 bytes para las contraseñas.
    Si la contraseña es más larga, se trunca automáticamente.
    """
    # Truncar a 72 bytes (límite de bcrypt)
    # if len(password.encode('utf-8')) > 72:
    #     logger.warning("La contraseña excede los 72 bytes y será truncada para hashing.")
    #     password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Crear JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Crear JWT refresh token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decodificar y validar JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise UnauthorizedException("Token inválido o expirado")


# RBAC - Role Based Access Control
class Permissions:
    """Permisos del sistema."""
    # Documentos
    DOCUMENTO_CREATE = "documento_create"
    DOCUMENTO_READ = "documento_read"
    DOCUMENTO_UPDATE = "documento_update"
    DOCUMENTO_DELETE = "documento_delete"
    
    # Incapacidades
    INCAPACIDAD_CREATE = "crear_incapacidad"
    INCAPACIDAD_READ = "ver_incapacidad"
    INCAPACIDAD_UPDATE = "editar_incapacidad"
    INCAPACIDAD_DELETE = "eliminar_incapacidad"
    INCAPACIDAD_AUDIT = "auditar_incapacidad"
    INCAPACIDAD_APPROVE = "aprobar_incapacidad"
    INCAPACIDAD_REJECT = "rechazar_incapacidad"
    
    # Empresas
    EMPRESA_CREATE = "crear_empresa"
    EMPRESA_READ = "ver_empresa"
    EMPRESA_UPDATE = "editar_empresa"
    EMPRESA_DELETE = "eliminar_empresa"
    
    # Empleados
    EMPLEADO_CREATE = "crear_empleado"
    EMPLEADO_READ = "ver_empleado"
    EMPLEADO_UPDATE = "editar_empleado"
    EMPLEADO_DELETE = "eliminar_empleado"
    
    # Órdenes de Pago
    ORDEN_PAGO_CREATE = "generar_orden_pago"
    ORDEN_PAGO_READ = "ver_orden_pago"
    ORDEN_PAGO_APPROVE = "aprobar_orden_pago"
    ORDEN_PAGO_PAY = "registrar_pago"
    
    # Usuarios
    USUARIO_CREATE = "crear_usuario"
    USUARIO_READ = "ver_usuario"
    USUARIO_UPDATE = "editar_usuario"
    USUARIO_DELETE = "eliminar_usuario"
    
    # Reportes y Configuración
    REPORTES_VIEW = "ver_reportes"
    EXPORT_DATA = "exportar_datos"
    CONFIGURE_SYSTEM = "configurar_sistema"


# Dependencies para FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> "Usuario":
    """
    Obtiene el usuario actual desde el token JWT.
    
    Args:
        db: Sesión de base de datos
        token: Token JWT
        
    Returns:
        Usuario autenticado
        
    Raises:
        UnauthorizedException: Si el token es inválido o el usuario no existe
    """
    from sqlalchemy import select
    from app.models.usuario import Usuario
    
    payload = decode_token(token)
    user_id: str = payload.get("sub")
    token_version: int = payload.get("token_version", 0)
    
    if user_id is None:
        raise UnauthorizedException("Token inválido")
    
    try:
        result = await db.execute(select(Usuario).where(Usuario.id == user_id))
        user = result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error al obtener usuario: {e}")
        raise UnauthorizedException("Error al validar token")
    
    if user is None:
        raise UnauthorizedException("Usuario no encontrado")
    
    if not user.is_active:
        raise UnauthorizedException("Usuario inactivo o bloqueado")
    
    # Verificar versión del token
    if user.token_version != token_version:
        raise UnauthorizedException("Token invalidado")
    
    return user


async def require_empresa(current_user: "Usuario" = Depends(get_current_user)) -> "Usuario":
    """Permite solo usuarios EMPRESA vinculados a una empresa."""
    from app.core.exceptions import ForbiddenException
    from app.utils.enums import RolUsuario
    if current_user.rol != RolUsuario.EMPRESA or current_user.empresa_id is None:
        raise ForbiddenException("Acceso exclusivo para usuarios de empresa vinculados a una compañía")
    return current_user


class PermissionChecker:
    """Verificador de permisos basado en roles."""
    
    PERMISSIONS = {
        "ADMIN": [
            "crear_empresa", "editar_empresa", "eliminar_empresa", "ver_empresa",
            "crear_empleado", "editar_empleado", "eliminar_empleado", "ver_empleado",
            "crear_incapacidad", "editar_incapacidad", "eliminar_incapacidad", "ver_incapacidad",
            "auditar_incapacidad", "aprobar_incapacidad", "rechazar_incapacidad",
            "generar_orden_pago", "aprobar_orden_pago", "registrar_pago", "ver_orden_pago",
            "crear_usuario", "editar_usuario", "eliminar_usuario", "ver_usuario",
            "documento_create", "documento_read", "documento_update", "documento_delete",
            "ver_reportes", "exportar_datos", "configurar_sistema"
        ],
        "AUDITOR": [
            "ver_empresa", "ver_empleado",
            "ver_incapacidad", "auditar_incapacidad",
            "aprobar_incapacidad", "rechazar_incapacidad",
            "generar_orden_pago", "ver_orden_pago",
            "documento_read", "documento_create",
            "ver_reportes"
        ],
        "APROBADOR": [
            "ver_incapacidad", "aprobar_orden_pago", "ver_orden_pago",
            "registrar_pago", "documento_read",
            "ver_reportes"
        ],
        "LIQUIDADOR": [
            "ver_empresa", "ver_empleado",
            "ver_reportes"
        ],
        "EMPRESA": [
            "ver_empleado_propio", "crear_empleado_propio",
            "editar_empleado_propio",
            "crear_incapacidad_propia", "ver_incapacidad_propia",
            "documento_create", "documento_read",
            "adjuntar_documentos_propio", "responder_observaciones_propia"
        ],
        "EMPLEADO": [
            "ver_incapacidad_propia", "crear_incapacidad_propia",
            "documento_create", "documento_read",
            "adjuntar_documentos_propio"
        ],
        "READONLY": [
            "ver_empresa", "ver_empleado", "ver_incapacidad",
            "ver_orden_pago", "documento_read",
            "ver_reportes"
        ]
    }
    
    def __init__(self, required_permissions: list[str]):
        """
        Inicializa el checker con los permisos requeridos.
        
        Args:
            required_permissions: Lista de permisos requeridos
        """
        self.required_permissions = required_permissions
    
    async def __call__(self, current_user=Depends(get_current_user)) -> bool:
        """
        Verifica si el usuario tiene los permisos requeridos.
        
        FastAPI inyecta automáticamente current_user usando la dependencia get_current_user.
        
        Args:
            current_user: Usuario actual (inyectado automáticamente)
            
        Returns:
            True si tiene permisos
            
        Raises:
            ForbiddenException: Si no tiene permisos
        """
        from app.core.exceptions import ForbiddenException
        
        user_permissions = self.get_permissions(current_user.rol)
        
        for permission in self.required_permissions:
            if permission not in user_permissions:
                raise ForbiddenException(
                    f"Permiso requerido: {permission}"
                )
        
        return True
    
    @classmethod
    def has_permission(cls, rol: str, permiso: str) -> bool:
        """Verificar si un rol tiene un permiso específico."""
        return permiso in cls.PERMISSIONS.get(rol, [])
    
    @classmethod
    def get_permissions(cls, rol: str) -> list:
        """Obtener todos los permisos de un rol."""
        return cls.PERMISSIONS.get(rol, [])

