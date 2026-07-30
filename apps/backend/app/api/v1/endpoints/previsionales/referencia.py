"""
API endpoints para Datos de Referencia Previsionales (Task 4.1).

Endpoint:
  POST /previsionales/referencia/importar?tipo={siniestros|solicitudes|ite_historico}

Decisión de forma (el brief de esta tarea deja explícitamente a criterio de
la implementación "3 endpoints separados -- tu decisión"): se eligió UN
único endpoint con un query param `tipo` que despacha al método
correspondiente de `excel_referencia_adapter`
(`importar_siniestros`/`importar_solicitudes`/`importar_ite_historico`), en
vez de 3 rutas distintas. Razones:

1. La tabla de rutas del brief (Phase 4, Task 4.1) enumera literalmente UNA
   sola ruta (`POST /previsionales/referencia/importar`) -- 3 rutas
   distintas habría sido un desvío de ese contrato sin una razón de negocio
   que lo justifique.
2. El query param despacha 1:1 a cada método del adapter (Protocol
   `FuenteReferenciaPrevisional`, Task 3.2) sin agregar lógica de negocio
   nueva -- es un simple `dict[tipo -> callable]`.

Permisos: PREVISIONAL_LOAD.
"""
from __future__ import annotations

from enum import Enum

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import PermissionChecker, Permissions, get_current_user
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.previsionales.referencia import ReferenciaImportarResponse
from app.services.previsionales.referencia_adapter import excel_referencia_adapter

router = APIRouter()

_REFERENCIA_LOAD_PERMISSIONS = [Permissions.PREVISIONAL_LOAD]


class TipoReferencia(str, Enum):
    """Las 3 hojas de referencia que expone `ExcelReferenciaAdapter`."""

    SINIESTROS = "siniestros"
    SOLICITUDES = "solicitudes"
    ITE_HISTORICO = "ite_historico"


@router.post(
    "/importar",
    response_model=ReferenciaImportarResponse,
    summary="Importar una hoja de datos de referencia previsionales",
    dependencies=[Depends(PermissionChecker(_REFERENCIA_LOAD_PERMISSIONS))],
)
async def importar_referencia(
    tipo: TipoReferencia = Query(
        ..., description="Hoja a importar: siniestros|solicitudes|ite_historico"
    ),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> ReferenciaImportarResponse:
    """
    Importa una de las 3 hojas de referencia (SINIESTROS, SOLICITUDES,
    "LISTADO ITE DIA") del excel del asegurador -- puente temporal
    (`ExcelReferenciaAdapter`) mientras no exista la vista SQL real (ver
    docstring de `referencia_adapter.py`). Idempotente por hoja: re-importar
    el mismo archivo no duplica filas (deduplicación a nivel de aplicación
    contra la llave natural de cada tabla, ver docstring del adapter).

    **Permisos**: PREVISIONAL_LOAD (AUDITOR_PREVISIONALES, ADMIN)
    """
    file_bytes = await file.read()

    if tipo is TipoReferencia.SINIESTROS:
        importados = await excel_referencia_adapter.importar_siniestros(db, file_bytes)
    elif tipo is TipoReferencia.SOLICITUDES:
        importados = await excel_referencia_adapter.importar_solicitudes(db, file_bytes)
    else:
        importados = await excel_referencia_adapter.importar_ite_historico(db, file_bytes)

    return ReferenciaImportarResponse(tipo=tipo.value, importados=importados)
