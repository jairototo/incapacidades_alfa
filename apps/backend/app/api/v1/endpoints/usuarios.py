"""
Endpoints REST para gestión de usuarios.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, PermissionChecker, Permissions
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    UsuarioListItem,
    UsuarioChangePassword,
    UsuarioResetPassword
)
from app.services.usuario_service import usuario_service
from app.utils.enums import RolUsuario, EstadoUsuario

router = APIRouter()


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    description="Crea un nuevo usuario (solo ADMIN)"
)
async def create_usuario(
    usuario_data: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo usuario.
    
    Requiere rol ADMIN.
    """
    usuario = await usuario_service.create_usuario(
        db=db,
        usuario_data=usuario_data,
        created_by_rol=current_user.rol
    )
    
    return usuario


@router.get(
    "/",
    response_model=List[UsuarioListItem],
    summary="Listar usuarios",
    description="Lista usuarios con filtros opcionales"
)
async def list_usuarios(
    rol: Optional[RolUsuario] = Query(None, description="Filtrar por rol"),
    estado: Optional[EstadoUsuario] = Query(None, description="Filtrar por estado"),
    search: Optional[str] = Query(None, description="Buscar por username, email o nombre"),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista usuarios con paginación y filtros.
    
    Filtros disponibles:
    - rol: RolUsuario (ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY)
    - estado: EstadoUsuario (ACTIVO, INACTIVO, BLOQUEADO)
    - search: Búsqueda por username, email o nombre completo
    """
    usuarios = await usuario_service.list_usuarios(
        db=db,
        rol=rol,
        estado=estado,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return usuarios


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Usuario actual",
    description="Obtiene información del usuario autenticado"
)
async def get_current_usuario_info(
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna información del usuario actualmente autenticado.
    """
    return current_user


@router.get(
    "/reporte-auditores",
    response_model=List[UsuarioListItem],
    summary="Reporte de carga de auditores",
    description="Cantidad de incapacidades actualmente asignadas a cada auditor (solo ADMIN)"
)
async def reporte_auditores(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna todos los usuarios AUDITOR con su sucursal e incapacidades_asignadas_activas.

    Requiere rol ADMIN.
    """
    return await usuario_service.reporte_auditores(db, admin_rol=current_user.rol)


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Obtener usuario",
    description="Obtiene un usuario por ID"
)
async def get_usuario(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un usuario específico por ID.
    """
    usuario = await usuario_service.get_usuario(db, usuario_id)
    
    return usuario


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Actualizar usuario",
    description="Actualiza un usuario (solo ADMIN)"
)
async def update_usuario(
    usuario_id: UUID,
    update_data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un usuario existente.
    
    Requiere rol ADMIN.
    """
    usuario = await usuario_service.update_usuario(
        db=db,
        usuario_id=usuario_id,
        update_data=update_data,
        updated_by_rol=current_user.rol
    )
    
    return usuario


@router.post(
    "/{usuario_id}/cambiar-password",
    response_model=UsuarioResponse,
    summary="Cambiar contraseña",
    description="Permite al usuario cambiar su propia contraseña"
)
async def change_password(
    usuario_id: UUID,
    password_data: UsuarioChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cambia la contraseña del usuario.
    
    El usuario solo puede cambiar su propia contraseña.
    """
    # Validar que el usuario solo pueda cambiar su propia contraseña
    # o que sea un ADMIN
    if current_user.id != usuario_id and current_user.rol != RolUsuario.ADMIN:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("Solo puedes cambiar tu propia contraseña")
    
    usuario = await usuario_service.change_password(
        db=db,
        usuario_id=usuario_id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    return usuario


@router.post(
    "/{usuario_id}/reset-password",
    response_model=dict,
    summary="Resetear contraseña",
    description="Genera una contraseña temporal para el usuario (solo ADMIN)"
)
async def reset_password(
    usuario_id: UUID,
    password_data: Optional[UsuarioResetPassword] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Resetea la contraseña de un usuario.
    
    Requiere rol ADMIN.
    
    Si no se proporciona nueva contraseña, se genera una temporal automáticamente.
    """
    new_password = password_data.new_password if password_data else None
    
    usuario, temp_password = await usuario_service.reset_password(
        db=db,
        usuario_id=usuario_id,
        admin_rol=current_user.rol,
        new_password=new_password
    )
    
    return {
        "message": "Contraseña reseteada exitosamente",
        "usuario_id": str(usuario.id),
        "username": usuario.username,
        "temp_password": temp_password,
        "must_change_password": True
    }


@router.post(
    "/{usuario_id}/activar",
    response_model=UsuarioResponse,
    summary="Activar usuario",
    description="Activa un usuario (solo ADMIN)"
)
async def activate_usuario(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Activa un usuario previamente desactivado o bloqueado.
    
    Requiere rol ADMIN.
    """
    usuario = await usuario_service.activate_usuario(
        db=db,
        usuario_id=usuario_id,
        admin_rol=current_user.rol
    )
    
    return usuario


@router.post(
    "/{usuario_id}/desactivar",
    response_model=UsuarioResponse,
    summary="Desactivar usuario",
    description="Desactiva un usuario (solo ADMIN)"
)
async def deactivate_usuario(
    usuario_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Desactiva un usuario.
    
    Requiere rol ADMIN.
    
    Esto invalidará todos sus tokens activos.
    """
    usuario = await usuario_service.deactivate_usuario(
        db=db,
        usuario_id=usuario_id,
        admin_rol=current_user.rol
    )
    
    return usuario


@router.post(
    "/{usuario_id}/asignar-rol",
    response_model=UsuarioResponse,
    summary="Asignar rol",
    description="Asigna un nuevo rol a un usuario (solo ADMIN)"
)
async def assign_rol(
    usuario_id: UUID,
    new_rol: RolUsuario,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Asigna un nuevo rol a un usuario.
    
    Requiere rol ADMIN.
    
    No se permite cambiar el propio rol.
    Esto invalidará todos los tokens del usuario.
    """
    usuario = await usuario_service.assign_rol(
        db=db,
        usuario_id=usuario_id,
        new_rol=new_rol,
        admin_id=current_user.id,
        admin_rol=current_user.rol
    )
    
    return usuario
