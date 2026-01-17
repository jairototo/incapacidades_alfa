"""
Endpoints API para Solicitantes.
"""

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.services.solicitante_service import solicitante_service
from app.schemas.solicitante import (
    SolicitanteCreate,
    SolicitanteResponse,
    SolicitanteUpdate
)

router = APIRouter()


@router.post(
    "/",
    response_model=SolicitanteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear solicitante",
    description="Crear un nuevo solicitante. El correo debe ser único."
)
async def create_solicitante(
    solicitante: SolicitanteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Crear nuevo solicitante."""
    return await solicitante_service.create_solicitante(db, solicitante)


@router.get(
    "/search",
    response_model=List[SolicitanteResponse],
    summary="Buscar solicitantes",
    description="Buscar solicitantes por correo electrónico (búsqueda parcial)."
)
async def search_solicitantes(
    correo: str = Query(
        ...,
        min_length=3,
        description="Correo o parte del correo para buscar",
        example="juan@example.com"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Número máximo de resultados"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Buscar solicitantes por correo.
    
    Permite búsqueda parcial (LIKE) en el campo correo.
    Requiere mínimo 3 caracteres.
    """
    return await solicitante_service.search_by_correo(db, correo, limit)


@router.get(
    "/",
    response_model=List[SolicitanteResponse],
    summary="Listar solicitantes",
    description="Obtener lista paginada de todos los solicitantes."
)
async def list_solicitantes(
    skip: int = Query(
        0,
        ge=0,
        description="Número de registros a saltar"
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Número máximo de resultados"
    ),
    db: AsyncSession = Depends(get_db)
):
    """Listar solicitantes con paginación."""
    return await solicitante_service.list_solicitantes(db, skip, limit)


@router.get(
    "/{solicitante_id}",
    response_model=SolicitanteResponse,
    summary="Obtener solicitante",
    description="Obtener un solicitante específico por su ID."
)
async def get_solicitante(
    solicitante_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Obtener solicitante por ID."""
    solicitante = await solicitante_service.get_solicitante(db, solicitante_id)
    
    if not solicitante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitante {solicitante_id} no encontrado"
        )
    
    return solicitante


@router.put(
    "/{solicitante_id}",
    response_model=SolicitanteResponse,
    summary="Actualizar solicitante",
    description="Actualizar datos de un solicitante existente."
)
async def update_solicitante(
    solicitante_id: UUID,
    data: SolicitanteUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Actualizar solicitante."""
    updated = await solicitante_service.update_solicitante(db, solicitante_id, data)
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitante {solicitante_id} no encontrado"
        )
    
    return updated


@router.delete(
    "/{solicitante_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar solicitante",
    description="Eliminar un solicitante."
)
async def delete_solicitante(
    solicitante_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Eliminar solicitante."""
    await solicitante_service.delete_solicitante(db, solicitante_id)
