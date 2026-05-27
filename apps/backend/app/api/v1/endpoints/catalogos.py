"""
Endpoints API para Catálogos CIE-10.
"""

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from apps.backend.app.db.session import get_db
from apps.backend.app.services.catalogo_service import catalogo_service
from apps.backend.app.schemas.catalogo import CIE10Response

router = APIRouter()


@router.get(
    "/cie10",
    response_model=List[CIE10Response],
    summary="Buscar códigos CIE-10",
    description="Buscar códigos CIE-10 por código o descripción (búsqueda parcial, case-insensitive)."
)
async def search_cie10(
    q: str = Query(
        ...,
        min_length=2,
        description="Término de búsqueda (mínimo 2 caracteres)",
        example="A01"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Número máximo de resultados"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Buscar códigos CIE-10.
    
    Busca en código y descripción de forma case-insensitive.
    Requiere mínimo 2 caracteres.
    """
    return await catalogo_service.search_cie10(db, q, limit)


@router.get(
    "/cie10/{codigo}",
    response_model=CIE10Response,
    summary="Obtener código CIE-10",
    description="Obtener un código CIE-10 específico por su código exacto."
)
async def get_cie10_by_codigo(
    codigo: str,
    db: AsyncSession = Depends(get_db)
):
    """Obtener código CIE-10 por código exacto."""
    # Normalizar a mayúsculas
    codigo_upper = codigo.upper()
    
    cie10 = await catalogo_service.get_cie10_by_codigo(db, codigo_upper)
    
    if not cie10:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código CIE-10 '{codigo}' no encontrado"
        )
    
    return cie10


@router.get(
    "/cie10/all/list",
    response_model=List[CIE10Response],
    summary="Listar todos los códigos CIE-10",
    description="Obtener lista paginada de todos los códigos CIE-10."
)
async def list_all_cie10(
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Número máximo de resultados"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Número de registros a saltar"
    ),
    db: AsyncSession = Depends(get_db)
):
    """Listar todos los códigos CIE-10 con paginación."""
    return await catalogo_service.get_all(db, limit, offset)


@router.get(
    "/cie10/stats/count",
    summary="Estadísticas de códigos CIE-10",
    description="Obtener estadísticas del catálogo CIE-10."
)
async def get_cie10_stats(
    db: AsyncSession = Depends(get_db)
):
    """Obtener estadísticas del catálogo CIE-10."""
    total = await catalogo_service.count(db)
    
    return {
        "total_codigos": total,
        "version": "CIE-10"
    }
