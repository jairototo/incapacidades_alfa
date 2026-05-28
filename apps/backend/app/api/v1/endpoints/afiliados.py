"""
Endpoints REST API para gestión de Afiliados.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.afiliado import (
    AfiliadoCreate,
    AfiliadoUpdate,
    AfiliadoResponse,
    AfiliadoListItem
)
from app.services.afiliado_service import afiliado_service
from app.core.logging import logger

router = APIRouter()


@router.post(
    "/",
    response_model=AfiliadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear afiliado",
    description="Crear un nuevo afiliado con validación de póliza y documento únicos"
)
async def create_afiliado(
    afiliado_in: AfiliadoCreate,
    db: AsyncSession = Depends(get_db)
) -> AfiliadoResponse:
    """
    Crear un nuevo afiliado.
    
    Validaciones:
    - Número de póliza único
    - Documento único
    - Fechas de póliza coherentes
    
    Args:
        afiliado_in: Datos del afiliado a crear
        db: Sesión de base de datos
        
    Returns:
        Afiliado creado con todos sus datos
        
    Raises:
        409: Si el número de póliza o documento ya existe
        422: Si las validaciones de negocio fallan
    """
    logger.info(f"Solicitud de creación de afiliado: póliza {afiliado_in.numero_poliza}")
    
    afiliado = await afiliado_service.create_afiliado(db, afiliado_in)
    
    return afiliado


@router.get(
    "/",
    response_model=List[AfiliadoListItem],
    summary="Listar afiliados",
    description="Obtener listado de afiliados con filtros opcionales y paginación"
)
async def list_afiliados(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    numero_poliza: Optional[str] = Query(None, description="Filtrar por número de póliza"),
    tipo_poliza: Optional[str] = Query(None, description="Filtrar por tipo de póliza"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    tipo_documento: Optional[str] = Query(None, description="Filtrar por tipo de documento"),
    numero_documento: Optional[str] = Query(None, description="Filtrar por número de documento"),
    search: Optional[str] = Query(None, description="Buscar en nombres y apellidos"),
    db: AsyncSession = Depends(get_db)
) -> List[AfiliadoListItem]:
    """
    Listar afiliados con filtros opcionales.
    
    Soporta paginación y múltiples filtros:
    - Por número de póliza
    - Por tipo de póliza (INDIVIDUAL, FAMILIAR, COLECTIVA)
    - Por estado (ACTIVO, INACTIVO, SUSPENDIDO)
    - Por documento
    - Búsqueda por texto en nombres/apellidos
    
    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        numero_poliza: Filtrar por número de póliza exacto
        tipo_poliza: Filtrar por tipo de póliza
        estado: Filtrar por estado
        tipo_documento: Filtrar por tipo de documento
        numero_documento: Filtrar por número de documento
        search: Texto a buscar en nombres y apellidos
        db: Sesión de base de datos
        
    Returns:
        Lista de afiliados que cumplen los filtros
    """
    logger.debug(f"Listado de afiliados - skip: {skip}, limit: {limit}")
    
    afiliados = await afiliado_service.list_afiliados(
        db,
        skip=skip,
        limit=limit,
        numero_poliza=numero_poliza,
        tipo_poliza=tipo_poliza,
        estado=estado,
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
        search=search
    )
    
    return afiliados


@router.get(
    "/{afiliado_id}",
    response_model=AfiliadoResponse,
    summary="Obtener afiliado",
    description="Obtener un afiliado por su ID"
)
async def get_afiliado(
    afiliado_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> AfiliadoResponse:
    """
    Obtener un afiliado específico por ID.
    
    Args:
        afiliado_id: UUID del afiliado
        db: Sesión de base de datos
        
    Returns:
        Datos completos del afiliado
        
    Raises:
        404: Si el afiliado no existe
    """
    logger.debug(f"Obtener afiliado: {afiliado_id}")
    
    afiliado = await afiliado_service.get_afiliado(db, afiliado_id)
    
    return afiliado


@router.put(
    "/{afiliado_id}",
    response_model=AfiliadoResponse,
    summary="Actualizar afiliado",
    description="Actualizar datos de un afiliado existente"
)
async def update_afiliado(
    afiliado_id: UUID,
    afiliado_in: AfiliadoUpdate,
    db: AsyncSession = Depends(get_db)
) -> AfiliadoResponse:
    """
    Actualizar un afiliado existente.
    
    Permite actualización parcial de campos. Valida:
    - Coherencia de fechas de póliza
    - Transiciones de estado válidas
    
    Args:
        afiliado_id: UUID del afiliado
        afiliado_in: Datos a actualizar
        db: Sesión de base de datos
        
    Returns:
        Afiliado actualizado
        
    Raises:
        404: Si el afiliado no existe
        422: Si las validaciones fallan
    """
    logger.info(f"Actualización de afiliado: {afiliado_id}")
    
    afiliado = await afiliado_service.update_afiliado(db, afiliado_id, afiliado_in)
    
    return afiliado


@router.delete(
    "/{afiliado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar afiliado",
    description="Eliminar (desactivar) un afiliado"
)
async def delete_afiliado(
    afiliado_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Eliminar un afiliado (soft delete).
    
    En realidad cambia el estado del afiliado a INACTIVO
    para mantener el historial de incapacidades.
    
    Args:
        afiliado_id: UUID del afiliado
        db: Sesión de base de datos
        
    Raises:
        404: Si el afiliado no existe
    """
    logger.info(f"Eliminación de afiliado: {afiliado_id}")
    
    await afiliado_service.delete_afiliado(db, afiliado_id)


@router.post(
    "/{afiliado_id}/activate",
    response_model=AfiliadoResponse,
    summary="Activar afiliado",
    description="Activar un afiliado inactivo"
)
async def activate_afiliado(
    afiliado_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> AfiliadoResponse:
    """
    Activar un afiliado.
    
    Valida que la póliza esté vigente antes de activar.
    
    Args:
        afiliado_id: UUID del afiliado
        db: Sesión de base de datos
        
    Returns:
        Afiliado activado
        
    Raises:
        404: Si el afiliado no existe
        422: Si la póliza no está vigente
    """
    logger.info(f"Activación de afiliado: {afiliado_id}")
    
    afiliado = await afiliado_service.activate_afiliado(db, afiliado_id)
    
    return afiliado


@router.post(
    "/{afiliado_id}/deactivate",
    response_model=AfiliadoResponse,
    summary="Desactivar afiliado",
    description="Desactivar un afiliado activo"
)
async def deactivate_afiliado(
    afiliado_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> AfiliadoResponse:
    """
    Desactivar un afiliado.
    
    Args:
        afiliado_id: UUID del afiliado
        db: Sesión de base de datos
        
    Returns:
        Afiliado desactivado
        
    Raises:
        404: Si el afiliado no existe
    """
    logger.info(f"Desactivación de afiliado: {afiliado_id}")
    
    afiliado = await afiliado_service.deactivate_afiliado(db, afiliado_id)
    
    return afiliado


@router.get(
    "/{afiliado_id}/incapacidades",
    response_model=List[dict],  # TODO: Usar schema de Incapacidad cuando esté disponible
    summary="Obtener incapacidades del afiliado",
    description="Listar todas las incapacidades de un afiliado"
)
async def get_afiliado_incapacidades(
    afiliado_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """
    Obtener incapacidades de un afiliado.
    
    Args:
        afiliado_id: UUID del afiliado
        skip: Registros a saltar
        limit: Máximo de registros
        db: Sesión de base de datos
        
    Returns:
        Lista de incapacidades del afiliado
        
    Raises:
        404: Si el afiliado no existe
    """
    logger.debug(f"Obtener incapacidades de afiliado: {afiliado_id}")
    
    # Verificar que el afiliado existe
    afiliado = await afiliado_service.get_afiliado(db, afiliado_id)
    
    # TODO: Implementar cuando exista IncapacidadService
    # Por ahora retornar las incapacidades desde la relación del modelo
    incapacidades = afiliado.incapacidades[skip:skip+limit]
    
    return [
        {
            "id": str(inc.id),
            "numero": inc.numero,
            "tipo": inc.tipo,
            "estado": inc.estado,
            "fecha_inicio": inc.fecha_inicio.isoformat(),
            "fecha_fin": inc.fecha_fin.isoformat() if inc.fecha_fin else None,
            "dias_incapacidad": inc.dias_incapacidad,
        }
        for inc in incapacidades
    ]
