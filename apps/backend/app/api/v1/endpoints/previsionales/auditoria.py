"""
API endpoints para el workflow de auditoría previsional (Task 4.2).

Conecta `AuditoriaPrevisionalService` (Task 3.3) y
`SenalAuditoriaPrevisionalRepository` (Task 2.2/3.3) a HTTP. Todos los
endpoints requieren autenticación JWT y el permiso PREVISIONAL_AUDIT --a
diferencia de Task 4.1 (que separa PREVISIONAL_READ/LOAD/EXPORT), aquí las
4 rutas (lectura y escritura) forman parte del mismo flujo de trabajo del
auditor, así que comparten un único permiso.

Endpoints:
  GET   /previsionales/incapacidades/{id}/senales   — señales AB-AT persistidas
  PATCH /previsionales/incapacidades/{id}            — actualiza dia_181_alfa (único campo soportado)
  POST  /previsionales/incapacidades/{id}/aval       — registra el aval humano (SI/NO)
  POST  /previsionales/incapacidades/{id}/duplicar   — separa una fila AFP en 2+ incapacidades

Permisos: PREVISIONAL_AUDIT (AUDITOR_PREVISIONALES, ADMIN) en las 4 rutas.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.security import PermissionChecker, Permissions, get_current_user
from app.db.repositories.previsionales import (
    incapacidad_previsional_repository,
    senal_auditoria_previsional_repository,
)
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.previsionales.auditoria import (
    AvalRequest,
    DuplicarRequest,
    IncapacidadPrevisionalPatchRequest,
    SenalAuditoriaPrevisionalResponse,
)
from app.schemas.previsionales.lote import IncapacidadPrevisionalResponse
from app.services.previsionales.auditoria_service import auditoria_previsional_service

router = APIRouter()

_AUDIT_PERMISSIONS = [Permissions.PREVISIONAL_AUDIT]


async def _obtener_incapacidad_o_404(db: AsyncSession, incapacidad_id: UUID):
    inc = await incapacidad_previsional_repository.get_by_id(db, incapacidad_id)
    if inc is None:
        raise NotFoundException(f"IncapacidadPrevisional {incapacidad_id} no encontrada")
    return inc


# ---------------------------------------------------------------------------
# GET /previsionales/incapacidades/{incapacidad_id}/senales
# ---------------------------------------------------------------------------


@router.get(
    "/{incapacidad_id}/senales",
    response_model=list[SenalAuditoriaPrevisionalResponse],
    summary="Listar las señales de auditoría (AB-AT) persistidas de una incapacidad",
    dependencies=[Depends(PermissionChecker(_AUDIT_PERMISSIONS))],
)
async def listar_senales(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[SenalAuditoriaPrevisionalResponse]:
    """
    Lista las 19 señales AB-AT ya evaluadas y persistidas para una
    incapacidad (ver `auditoria_service.auditar_incapacidad`/
    `auditar_lote`, que son quienes las escriben). No re-evalúa nada aquí
    -- lectura pura de lo ya persistido.

    **Permisos**: PREVISIONAL_AUDIT (AUDITOR_PREVISIONALES, ADMIN)
    """
    await _obtener_incapacidad_o_404(db, incapacidad_id)
    senales = await senal_auditoria_previsional_repository.get_by_incapacidad(db, incapacidad_id)
    return [SenalAuditoriaPrevisionalResponse.model_validate(s) for s in senales]


# ---------------------------------------------------------------------------
# PATCH /previsionales/incapacidades/{incapacidad_id}
# ---------------------------------------------------------------------------


@router.patch(
    "/{incapacidad_id}",
    response_model=IncapacidadPrevisionalResponse,
    summary="Actualizar el día 181 auditado (Alfa) de una incapacidad",
    dependencies=[Depends(PermissionChecker(_AUDIT_PERMISSIONS))],
)
async def actualizar_incapacidad(
    incapacidad_id: UUID,
    body: IncapacidadPrevisionalPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> IncapacidadPrevisionalResponse:
    """
    Actualiza campos ALFA de auditoría editables por un auditor humano.

    **Único campo soportado: `dia_181_alfa`.** El plan original menciona
    también `fecha_crie_alfa` y `observacion_alfa`, pero ninguno de los dos
    es editable hoy por un gap real de columnas en el modelo (ver docstring
    de `IncapacidadPrevisionalPatchRequest` para el detalle completo):
    `fecha_crie` existe pero se puebla del cruce con SOLICITUDES (no es
    "Alfa"), y `observacion_alfa` no tiene columna dedicada en absoluto.
    Editarlos requiere una migración futura, no se resuelve aquí escribiendo
    en `metadata_` (JSONB) -- estas son decisiones de auditor que deben
    quedar genuinamente consultables/auditables como columna propia.

    Convención de transacción: `update_flushed` (sin commit interno) +
    `db.commit()` explícito en el endpoint -- mismo patrón que
    `vincular_siniestro` en `app/api/v1/endpoints/incapacidades.py`.

    **Permisos**: PREVISIONAL_AUDIT (AUDITOR_PREVISIONALES, ADMIN)
    """
    await _obtener_incapacidad_o_404(db, incapacidad_id)

    actualizada = await incapacidad_previsional_repository.update_flushed(
        db,
        id=incapacidad_id,
        obj_in={"dia_181_alfa": body.dia_181_alfa},
    )
    await db.commit()
    await db.refresh(actualizada)
    return IncapacidadPrevisionalResponse.model_validate(actualizada)


# ---------------------------------------------------------------------------
# POST /previsionales/incapacidades/{incapacidad_id}/aval
# ---------------------------------------------------------------------------


@router.post(
    "/{incapacidad_id}/aval",
    response_model=IncapacidadPrevisionalResponse,
    summary="Registrar el aval de auditoría (decisión humana SI/NO)",
    dependencies=[Depends(PermissionChecker(_AUDIT_PERMISSIONS))],
)
async def registrar_aval(
    incapacidad_id: UUID,
    body: AvalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> IncapacidadPrevisionalResponse:
    """
    Delegado íntegro a `AuditoriaPrevisionalService.registrar_aval` -- la
    regla AC ("el aval jamás se autocalcula") vive ahí, no aquí. Si
    `aval='NO'` sin `motivo`, el servicio levanta `BadRequestException`
    ANTES de tocar la BD, que el exception handler global mapea a 400 (no
    se re-valida ese caso en el endpoint).

    **Permisos**: PREVISIONAL_AUDIT (AUDITOR_PREVISIONALES, ADMIN)
    """
    inc = await auditoria_previsional_service.registrar_aval(
        db,
        incapacidad_id=incapacidad_id,
        aval=body.aval,
        motivo=body.motivo,
        usuario_id=current_user.id,
    )
    return IncapacidadPrevisionalResponse.model_validate(inc)


# ---------------------------------------------------------------------------
# POST /previsionales/incapacidades/{incapacidad_id}/duplicar
# ---------------------------------------------------------------------------


@router.post(
    "/{incapacidad_id}/duplicar",
    response_model=IncapacidadPrevisionalResponse,
    status_code=201,
    summary="Duplicar una incapacidad en un nuevo rango de fechas",
    dependencies=[Depends(PermissionChecker(_AUDIT_PERMISSIONS))],
)
async def duplicar_incapacidad(
    incapacidad_id: UUID,
    body: DuplicarRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> IncapacidadPrevisionalResponse:
    """
    Delegado íntegro a `AuditoriaPrevisionalService.duplicar` -- la AFP
    reportó varias incapacidades reales en una sola fila del excel, y el
    auditor las separa manualmente con fechas propias. La nueva fila queda
    con `es_duplicado_interno=True` apuntando a `incapacidad_id` como
    `incapacidad_origen_id` (ver el servicio para la lista exacta de campos
    copiados/excluidos).

    **Permisos**: PREVISIONAL_AUDIT (AUDITOR_PREVISIONALES, ADMIN)
    """
    nueva = await auditoria_previsional_service.duplicar(
        db,
        incapacidad_id=incapacidad_id,
        fechas={"fecha_inicial": body.fecha_inicial, "fecha_final": body.fecha_final},
        usuario_id=current_user.id,
    )
    return IncapacidadPrevisionalResponse.model_validate(nueva)
