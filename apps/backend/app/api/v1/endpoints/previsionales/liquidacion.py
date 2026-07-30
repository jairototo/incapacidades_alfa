"""
API endpoints para liquidación y respuesta AFP de Lotes Previsionales
(Task 4.3).

Archivo separado de `endpoints/previsionales/lotes.py` a propósito (mismo
prefijo `/previsionales/lotes`, un segundo router montado ahí -- ver
`app/api/v1/router.py`): estos dos endpoints delegan íntegramente en
servicios ya construidos y revisados en Task 3.4
(`liquidacion_service.liquidacion_previsional_service` y
`respuesta_afp.generar_respuesta`), sin lógica de negocio propia -- mismo
principio de capas finas que el resto del módulo.

Endpoints:
  POST /previsionales/lotes/{lote_id}/liquidar         — re-liquidar un lote
  GET  /previsionales/lotes/{lote_id}/respuesta.xlsx    — exportar el excel de respuesta al fondo

Permisos: PREVISIONAL_LIQUIDATE (POST /liquidar), PREVISIONAL_EXPORT
(GET /respuesta.xlsx -- mismo permiso que Task 4.1 usa para GET /arpis.xlsx,
"export" cubre cualquier ruta que genere un documento saliente).
"""
from __future__ import annotations

import io
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.security import PermissionChecker, Permissions, get_current_user
from app.db.repositories.previsionales import lote_previsional_repository
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.previsionales.liquidacion import LiquidarLoteResponse
from app.services.previsionales.liquidacion_service import liquidacion_previsional_service
from app.services.previsionales.respuesta_afp import generar_respuesta

router = APIRouter()

_LOTE_LIQUIDATE_PERMISSIONS = [Permissions.PREVISIONAL_LIQUIDATE]
_LOTE_EXPORT_PERMISSIONS = [Permissions.PREVISIONAL_EXPORT]

_CONTENT_TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ---------------------------------------------------------------------------
# POST /previsionales/lotes/{lote_id}/liquidar
# ---------------------------------------------------------------------------

@router.post(
    "/{lote_id}/liquidar",
    response_model=LiquidarLoteResponse,
    summary="Re-liquidar todas las incapacidades no duplicadas de un lote",
    dependencies=[Depends(PermissionChecker(_LOTE_LIQUIDATE_PERMISSIONS))],
)
async def liquidar_lote(
    lote_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> LiquidarLoteResponse:
    """
    Delega íntegramente en
    `liquidacion_previsional_service.liquidar_lote` (Task 3.4): recalcula
    `valor_auditado`/`diferencia_valor_afp` de cada incapacidad NO duplicada
    interna del lote usando los periodos ya persistidos y el SMLMV vigente.
    Idempotente -- re-ejecutable sin efectos acumulativos.

    `liquidar_lote` en sí mismo no distingue "lote inexistente" de "lote sin
    incapacidades" (ambos devuelven 0 filas liquidadas), así que el 404 se
    resuelve aquí con un `get_by_id` explícito antes de delegar -- mismo
    patrón que `actualizar_lote` en `lotes.py`.

    NO aplica el recorte de ventana por `dia_181_alfa`/`fecha_crie_alfa`
    (`max(día_181, fecha_CRIE)`) -- esa es una decisión de negocio
    deliberadamente pendiente, documentada en el docstring de
    `liquidacion_service.py`; este endpoint no la resuelve ni la referencia
    más allá de esta nota.

    **Permisos**: PREVISIONAL_LIQUIDATE (AUDITOR_PREVISIONALES, ADMIN)
    """
    lote = await lote_previsional_repository.get_by_id(db, lote_id)
    if lote is None:
        raise NotFoundException(f"Lote previsional {lote_id} no encontrado")

    liquidadas = await liquidacion_previsional_service.liquidar_lote(db, lote_id)
    return LiquidarLoteResponse(liquidadas=liquidadas)


# ---------------------------------------------------------------------------
# GET /previsionales/lotes/{lote_id}/respuesta.xlsx
# ---------------------------------------------------------------------------

@router.get(
    "/{lote_id}/respuesta.xlsx",
    summary="Exportar el excel de respuesta al fondo (AFP) de un lote",
    dependencies=[Depends(PermissionChecker(_LOTE_EXPORT_PERMISSIONS))],
)
async def exportar_respuesta(
    lote_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> StreamingResponse:
    """
    Delega íntegramente en `respuesta_afp.generar_respuesta` (Task 3.4): re-
    abre el excel ORIGINAL archivado del lote y le agrega solo las columnas
    AVAL/OBSERVACION, sin reconstruir el libro (ver el docstring de ese
    módulo para el detalle del emparejamiento fila-a-fila).

    A diferencia de `liquidar_lote`, no se agrega aquí un `get_by_id` previo:
    `generar_respuesta` YA levanta `NotFoundException` (lote inexistente o
    archivo original ya no existe en storage) y `BadRequestException` (lote
    sin archivo original archivado, o archivo archivado que no es un excel
    válido) -- duplicar esa validación aquí repetiría la misma query sin
    agregar ninguna garantía nueva.

    **Permisos**: PREVISIONAL_EXPORT (AUDITOR_PREVISIONALES, AUDITOR_JURIDICO, ADMIN)
    """
    content = await generar_respuesta(db, lote_id)

    return StreamingResponse(
        io.BytesIO(content),
        media_type=_CONTENT_TYPE_XLSX,
        headers={"Content-Disposition": f"attachment; filename=respuesta_lote_{lote_id}.xlsx"},
    )
