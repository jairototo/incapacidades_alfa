"""
Endpoints REST API para gestión de Empresas.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.empresa import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResponse,
    EmpresaListItem
)
from app.services.empresa_service import empresa_service
from app.services.empleado_service import empleado_service
from app.schemas.empleado import EmpleadoListItem
from app.core.security import get_current_user, PermissionChecker, Permissions
from app.core.exceptions import ForbiddenException
from app.models.usuario import Usuario
from app.utils.enums import RolUsuario, EstadoEmpleado
from app.core.logging import logger

router = APIRouter()


@router.post(
    "/",
    response_model=EmpresaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empresa",
    description="Crear una nueva empresa con validación de NIT y razón social únicos",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_CREATE]))],
)
async def create_empresa(
    empresa_in: EmpresaCreate,
    db: AsyncSession = Depends(get_db)
) -> EmpresaResponse:
    """
    Crear una nueva empresa.
    
    Validaciones:
    - NIT único
    - Razón social única
    - Formato de NIT válido
    - Tipo de empresa válido
    
    Args:
        empresa_in: Datos de la empresa a crear
        db: Sesión de base de datos
        
    Returns:
        Empresa creada con todos sus datos
        
    Raises:
        409: Si el NIT o razón social ya existe
        422: Si las validaciones de negocio fallan
    """
    logger.info(f"Solicitud de creación de empresa: NIT {empresa_in.nit}")
    
    empresa = await empresa_service.create_empresa(db, empresa_in)
    
    return empresa


@router.get(
    "/",
    response_model=List[EmpresaListItem],
    summary="Listar empresas",
    description="Obtener listado de empresas con filtros opcionales y paginación",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_READ]))],
)
async def list_empresas(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    nit: Optional[str] = Query(None, description="Filtrar por NIT (búsqueda parcial)"),
    tipo_empresa: Optional[str] = Query(None, description="Filtrar por tipo de empresa"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    departamento: Optional[str] = Query(None, description="Filtrar por departamento"),
    search: Optional[str] = Query(None, description="Buscar en NIT o razón social"),
    db: AsyncSession = Depends(get_db)
) -> List[EmpresaListItem]:
    """
    Listar empresas con filtros opcionales.
    
    Soporta paginación y múltiples filtros:
    - Por NIT (búsqueda parcial)
    - Por tipo de empresa
    - Por estado (ACTIVA, INACTIVA, SUSPENDIDA)
    - Por ubicación (ciudad, departamento)
    - Búsqueda por texto en NIT o razón social
    
    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        nit: Filtrar por NIT (búsqueda parcial)
        tipo_empresa: Filtrar por tipo de empresa
        estado: Filtrar por estado
        ciudad: Filtrar por ciudad
        departamento: Filtrar por departamento
        search: Texto a buscar en NIT o razón social
        db: Sesión de base de datos
        
    Returns:
        Lista de empresas que cumplen los filtros
    """
    logger.debug(f"Listado de empresas - skip: {skip}, limit: {limit}")
    
    empresas = await empresa_service.list_empresas(
        db,
        skip=skip,
        limit=limit,
        nit=nit,
        tipo_empresa=tipo_empresa,
        estado=estado,
        ciudad=ciudad,
        departamento=departamento,
        search=search
    )
    
    return empresas


@router.get(
    "/{empresa_id}",
    response_model=EmpresaResponse,
    summary="Obtener empresa",
    description="Obtener una empresa por su ID",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_READ]))],
)
async def get_empresa(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> EmpresaResponse:
    """
    Obtener una empresa específica por ID.
    
    Args:
        empresa_id: UUID de la empresa
        db: Sesión de base de datos
        
    Returns:
        Datos completos de la empresa
        
    Raises:
        404: Si la empresa no existe
    """
    logger.debug(f"Obtener empresa: {empresa_id}")
    
    empresa = await empresa_service.get_empresa(db, empresa_id)
    
    return empresa


@router.put(
    "/{empresa_id}",
    response_model=EmpresaResponse,
    summary="Actualizar empresa",
    description="Actualizar datos de una empresa existente",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_UPDATE]))],
)
async def update_empresa(
    empresa_id: UUID,
    empresa_in: EmpresaUpdate,
    db: AsyncSession = Depends(get_db)
) -> EmpresaResponse:
    """
    Actualizar una empresa existente.
    
    Permite actualización parcial de campos. Valida:
    - Razón social única si se actualiza
    - Tipo de empresa válido
    - Transiciones de estado válidas
    
    Args:
        empresa_id: UUID de la empresa
        empresa_in: Datos a actualizar
        db: Sesión de base de datos
        
    Returns:
        Empresa actualizada
        
    Raises:
        404: Si la empresa no existe
        409: Si razón social ya existe
        422: Si las validaciones fallan
    """
    logger.info(f"Actualización de empresa: {empresa_id}")
    
    empresa = await empresa_service.update_empresa(db, empresa_id, empresa_in)
    
    return empresa


@router.delete(
    "/{empresa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar empresa",
    description="Eliminar (desactivar) una empresa",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_DELETE]))],
)
async def delete_empresa(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Eliminar una empresa (soft delete).
    
    En realidad cambia el estado de la empresa a INACTIVA
    para mantener el historial de empleados e incapacidades.
    
    Valida que no tenga empleados activos antes de desactivar.
    
    Args:
        empresa_id: UUID de la empresa
        db: Sesión de base de datos
        
    Raises:
        404: Si la empresa no existe
        422: Si tiene empleados activos
    """
    logger.info(f"Eliminación de empresa: {empresa_id}")
    
    await empresa_service.delete_empresa(db, empresa_id)


@router.post(
    "/{empresa_id}/activate",
    response_model=EmpresaResponse,
    summary="Activar empresa",
    description="Activar una empresa inactiva",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_UPDATE]))],
)
async def activate_empresa(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> EmpresaResponse:
    """
    Activar una empresa.
    
    Args:
        empresa_id: UUID de la empresa
        db: Sesión de base de datos
        
    Returns:
        Empresa activada
        
    Raises:
        404: Si la empresa no existe
    """
    logger.info(f"Activación de empresa: {empresa_id}")
    
    empresa = await empresa_service.activate_empresa(db, empresa_id)
    
    return empresa


@router.post(
    "/{empresa_id}/deactivate",
    response_model=EmpresaResponse,
    summary="Desactivar empresa",
    description="Desactivar una empresa activa",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_UPDATE]))],
)
async def deactivate_empresa(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> EmpresaResponse:
    """
    Desactivar una empresa.
    
    Valida que no tenga empleados activos.
    
    Args:
        empresa_id: UUID de la empresa
        db: Sesión de base de datos
        
    Returns:
        Empresa desactivada
        
    Raises:
        404: Si la empresa no existe
        422: Si tiene empleados activos
    """
    logger.info(f"Desactivación de empresa: {empresa_id}")
    
    empresa = await empresa_service.deactivate_empresa(db, empresa_id)
    
    return empresa


@router.get(
    "/{empresa_id}/empleados",
    response_model=List[EmpleadoListItem],
    summary="Obtener empleados de la empresa",
    description="Listar empleados de una empresa con búsqueda y filtros. "
                "Los usuarios EMPRESA solo pueden consultar su propia empresa.",
)
async def get_empresa_empleados(
    empresa_id: UUID,
    search: Optional[str] = Query(
        None, description="Búsqueda en nombres, apellidos, documento o email"
    ),
    estado: Optional[EstadoEmpleado] = Query(None, description="Filtrar por estado del empleado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> List[EmpleadoListItem]:
    """
    Lista los empleados de una empresa con búsqueda + filtros + paginación.

    Scoping: un usuario con rol EMPRESA solo puede consultar los empleados de su
    propia empresa (403 en caso contrario). Roles internos ADMIN/AUDITOR/LIQUIDADOR
    pueden consultar cualquier empresa. Cualquier otro rol es rechazado.
    """
    if current_user.rol == RolUsuario.EMPRESA:
        if current_user.empresa_id != empresa_id:
            raise ForbiddenException("No puede consultar empleados de otra empresa")
    elif current_user.rol not in (RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR):
        raise ForbiddenException("No tiene permisos para consultar empleados")

    return await empleado_service.list_empleados(
        db,
        empresa_id=empresa_id,
        estado=estado,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{empresa_id}/incapacidades",
    response_model=List[dict],  # TODO: Usar schema de Incapacidad cuando esté disponible
    summary="Obtener incapacidades de la empresa",
    description="Listar todas las incapacidades ARL de una empresa",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_READ]))],
)
async def get_empresa_incapacidades(
    empresa_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    estado: Optional[str] = Query(None, description="Filtrar por estado de incapacidad"),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """
    Obtener incapacidades ARL de una empresa.
    
    Args:
        empresa_id: UUID de la empresa
        skip: Registros a saltar
        limit: Máximo de registros
        estado: Filtrar por estado de incapacidad
        db: Sesión de base de datos
        
    Returns:
        Lista de incapacidades de la empresa
        
    Raises:
        404: Si la empresa no existe
    """
    logger.debug(f"Obtener incapacidades de empresa: {empresa_id}")
    
    # Verificar que la empresa existe
    empresa = await empresa_service.get_empresa(db, empresa_id)
    
    # Filtrar incapacidades por estado si se especifica
    incapacidades = empresa.incapacidades
    if estado:
        incapacidades = [i for i in incapacidades if i.estado == estado]
    
    # Aplicar paginación
    incapacidades = incapacidades[skip:skip+limit]
    
    return [
        {
            "id": str(inc.id),
            "numero": inc.numero,
            "tipo": inc.tipo,
            "estado": inc.estado,
            "fecha_inicio": inc.fecha_inicio.isoformat(),
            "fecha_fin": inc.fecha_fin.isoformat() if inc.fecha_fin else None,
            "dias_incapacidad": inc.dias_incapacidad,
            "empleado_id": str(inc.empleado_id) if inc.empleado_id else None,
        }
        for inc in incapacidades
    ]
