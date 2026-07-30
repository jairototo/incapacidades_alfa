"""
API endpoints para Parámetros SMLMV Previsionales (Task 4.1).

Endpoint:
  GET /previsionales/parametros/smlmv

Permisos: PREVISIONAL_READ.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import PermissionChecker, Permissions, get_current_user
from app.db.repositories.smlmv_parametros_repository import smlmv_parametros_repository
from app.db.session import get_db
from app.models.previsionales.smlmv_parametros import SmlmvParametros
from app.models.usuario import Usuario
from app.schemas.previsionales.parametros import SmlmvParametrosResponse

router = APIRouter()

_PARAMETROS_READ_PERMISSIONS = [Permissions.PREVISIONAL_READ]


@router.get(
    "/smlmv",
    response_model=list[SmlmvParametrosResponse],
    summary="Listar los parámetros SMLMV configurados por año",
    dependencies=[Depends(PermissionChecker(_PARAMETROS_READ_PERMISSIONS))],
)
async def listar_smlmv(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[SmlmvParametrosResponse]:
    """
    Lista los `SmlmvParametros` configurados, ordenados por año ascendente.

    `smlmv_parametros_repository` (Task 0.2) solo trae `get_by_ano` -- para
    el listado se reutiliza `BaseRepository.get_multi` (CRUD ya heredado)
    en vez de agregar un método de repositorio nuevo, siguiendo la guía
    explícita del brief de esta tarea de revisar qué "listar todos" ya
    existe antes de inventar uno.

    **Permisos**: PREVISIONAL_READ (AUDITOR_PREVISIONALES, AUDITOR_JURIDICO, ADMIN)
    """
    parametros = await smlmv_parametros_repository.get_multi(
        db, skip=0, limit=1000, order_by=[SmlmvParametros.ano.asc()]
    )
    return [SmlmvParametrosResponse.model_validate(p) for p in parametros]
