"""
API endpoints para gestión de Empleados.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.db.session import get_db
from apps.backend.app.schemas.empleado import (
    EmpleadoCreate,
    EmpleadoUpdate,
    EmpleadoResponse,
    EmpleadoListItem
)
from apps.backend.app.services.empleado_service import empleado_service
from apps.backend.app.utils.enums import EstadoEmpleado

router = APIRouter()


@router.post(
    "/",
    response_model=EmpleadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empleado",
    description="Crea un nuevo empleado con validaciones de negocio"
)
async def create_empleado(
    empleado_data: EmpleadoCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuevo empleado.
    
    Validaciones:
    - La empresa debe existir y estar activa
    - No puede existir otro empleado con el mismo documento en la empresa
    - fecha_ingreso debe ser <= hoy
    - fecha_retiro debe ser > fecha_ingreso (si se proporciona)
    - Empleado debe tener al menos 14 años a la fecha de ingreso
    """
    return await empleado_service.create_empleado(db, empleado_data)


@router.get(
    "/",
    response_model=List[EmpleadoListItem],
    summary="Listar empleados",
    description="Lista empleados con filtros opcionales"
)
async def list_empleados(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    estado: Optional[EstadoEmpleado] = Query(None, description="Filtrar por estado"),
    documento: Optional[str] = Query(None, description="Filtrar por documento"),
    search: Optional[str] = Query(
        None,
        description="Búsqueda en nombres, apellidos, documento o email"
    ),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista empleados con filtros opcionales.
    
    Filtros disponibles:
    - empresa_id: ID de la empresa
    - estado: ACTIVO, INACTIVO, RETIRADO
    - documento: Búsqueda parcial en número de documento
    - search: Búsqueda en nombres, apellidos, documento o email
    """
    return await empleado_service.list_empleados(
        db,
        empresa_id=empresa_id,
        estado=estado,
        documento=documento,
        search=search,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{empleado_id}",
    response_model=EmpleadoResponse,
    summary="Obtener empleado",
    description="Obtiene un empleado por su ID"
)
async def get_empleado(
    empleado_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un empleado específico por ID.
    
    Retorna toda la información del empleado incluyendo:
    - Datos personales
    - Información laboral
    - Información bancaria
    - Estado y timestamps
    """
    return await empleado_service.get_empleado(db, empleado_id)


@router.put(
    "/{empleado_id}",
    response_model=EmpleadoResponse,
    summary="Actualizar empleado",
    description="Actualiza los datos de un empleado"
)
async def update_empleado(
    empleado_id: UUID,
    empleado_data: EmpleadoUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza los datos de un empleado.
    
    Validaciones:
    - No se puede cambiar la empresa del empleado
    - Las fechas deben ser coherentes (retiro > ingreso, etc.)
    - Actualiza el campo updated_at automáticamente
    
    Nota: Solo se actualizan los campos proporcionados (PATCH semántico)
    """
    return await empleado_service.update_empleado(db, empleado_id, empleado_data)


@router.delete(
    "/{empleado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar empleado",
    description="Elimina un empleado (soft delete)"
)
async def delete_empleado(
    empleado_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un empleado (soft delete).
    
    Validaciones:
    - El empleado no debe tener incapacidades activas
    - Si tiene incapacidades finalizadas, se mantienen en el histórico
    
    Nota: Es un soft delete, el registro permanece en la base de datos
    pero marcado como eliminado.
    """
    await empleado_service.delete_empleado(db, empleado_id)
    return None


@router.post(
    "/{empleado_id}/activate",
    response_model=EmpleadoResponse,
    summary="Activar empleado",
    description="Cambia el estado del empleado a ACTIVO"
)
async def activate_empleado(
    empleado_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Activa un empleado (cambia estado a ACTIVO).
    
    Validaciones:
    - El empleado debe existir
    - No se puede activar un empleado que ya está activo
    """
    return await empleado_service.activate_empleado(db, empleado_id)


@router.post(
    "/{empleado_id}/deactivate",
    response_model=EmpleadoResponse,
    summary="Desactivar empleado",
    description="Cambia el estado del empleado a INACTIVO"
)
async def deactivate_empleado(
    empleado_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Desactiva un empleado (cambia estado a INACTIVO).
    
    Validaciones:
    - El empleado debe existir
    - No se puede desactivar un empleado que ya está inactivo
    - No se puede desactivar si tiene incapacidades activas
    
    Use este endpoint en lugar de DELETE cuando quiera mantener
    el empleado en el sistema pero inactivarlo temporalmente.
    """
    return await empleado_service.deactivate_empleado(db, empleado_id)


@router.get(
    "/{empleado_id}/incapacidades",
    response_model=List[dict],
    summary="Obtener incapacidades del empleado",
    description="Lista todas las incapacidades asociadas al empleado"
)
async def get_incapacidades_empleado(
    empleado_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene todas las incapacidades del empleado.
    
    Retorna una lista con:
    - Incapacidades activas y finalizadas
    - Información del tipo (ARL/SALUD)
    - Estado actual de cada incapacidad
    - Fechas y valores
    
    Nota: Por ahora retorna lista vacía hasta que se implemente
    el módulo de incapacidades.
    """
    return await empleado_service.get_incapacidades_empleado(db, empleado_id)
