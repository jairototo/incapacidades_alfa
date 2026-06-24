"""
API endpoints para Liquidación de Incapacidades.

Todos los endpoints requieren autenticación JWT y rol
AUDITOR, APROBADOR o ADMIN.

Endpoints:
  GET  /incapacidades/{id}/liquidacion           — recuperar
  POST /incapacidades/{id}/liquidacion           — crear/actualizar
  POST /incapacidades/{id}/liquidacion/calcular-ibl  — stub IBL
  POST /incapacidades/{id}/liquidacion/devolver  — devolver a EN_AUDITORIA
  POST /incapacidades/{id}/liquidacion/completar — pasar a PAGADA/PAGADA_PARCIAL
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import PermissionChecker, Permissions, get_current_user
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.incapacidad import IncapacidadInDB
from app.schemas.liquidacion import (
    BreakdownResponse,
    IblStubResponse,
    LiquidacionDevolver,
    LiquidacionGuardar,
    LiquidacionResponse,
)
from app.services.liquidacion_service import liquidacion_service

router = APIRouter()

# Permisos de sólo lectura: AUDITOR, APROBADOR, ADMIN y READONLY (ver_incapacidad)
_LIQUIDACION_READ_PERMISSIONS = [Permissions.INCAPACIDAD_READ]

# Permisos de mutación: AUDITOR, APROBADOR y ADMIN (aprobar_incapacidad).
# READONLY no tiene este permiso, por lo que queda excluido de los endpoints
# de escritura (guardar, devolver, completar).
_LIQUIDACION_WRITE_PERMISSIONS = [Permissions.INCAPACIDAD_APPROVE]


# ---------------------------------------------------------------------------
# GET /incapacidades/{id}/liquidacion
# ---------------------------------------------------------------------------

@router.get(
    "/{incapacidad_id}/liquidacion",
    response_model=LiquidacionResponse,
    summary="Obtener liquidación de una incapacidad",
    tags=["liquidacion"],
    dependencies=[Depends(PermissionChecker(_LIQUIDACION_READ_PERMISSIONS))],
)
async def get_liquidacion(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> LiquidacionResponse:
    """
    Recupera la liquidación guardada para una incapacidad.

    Requiere que la incapacidad esté en estado LIQUIDACION o LIQUIDACION_PARCIAL
    y que se haya guardado una liquidación previamente.

    **Permisos**: AUDITOR, APROBADOR, ADMIN
    """
    liquidacion = await liquidacion_service.get_liquidacion(db, incapacidad_id)
    return LiquidacionResponse.model_validate(liquidacion)


# ---------------------------------------------------------------------------
# POST /incapacidades/{id}/liquidacion
# ---------------------------------------------------------------------------

@router.post(
    "/{incapacidad_id}/liquidacion",
    response_model=LiquidacionResponse,
    status_code=status.HTTP_200_OK,
    summary="Guardar liquidación (crear o actualizar)",
    tags=["liquidacion"],
    dependencies=[Depends(PermissionChecker(_LIQUIDACION_WRITE_PERMISSIONS))],
)
async def guardar_liquidacion(
    incapacidad_id: UUID,
    data: LiquidacionGuardar,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> LiquidacionResponse:
    """
    Crea o actualiza la liquidación de una incapacidad.

    La incapacidad debe estar en estado **LIQUIDACION** o **LIQUIDACION_PARCIAL**.

    Si ya existe una liquidación para la incapacidad, la sobrescribe con los
    nuevos datos.

    **Notas**:
    - El IBL (ibl) es un valor manual hasta que esté disponible la integración
      con Imaginex.
    - Los valores de desglose son opcionales — la fórmula exacta está pendiente
      de confirmación (C1 — Helen).

    **Permisos**: AUDITOR, APROBADOR, ADMIN
    """
    liquidacion = await liquidacion_service.guardar_liquidacion(
        db=db,
        incapacidad_id=incapacidad_id,
        data=data,
        liquidador_id=current_user.id,
    )
    return LiquidacionResponse.model_validate(liquidacion)


# ---------------------------------------------------------------------------
# POST /incapacidades/{id}/liquidacion/calcular-ibl
# ---------------------------------------------------------------------------

@router.post(
    "/{incapacidad_id}/liquidacion/calcular-ibl",
    response_model=IblStubResponse,
    summary="[STUB] Calcular IBL desde Imaginex",
    tags=["liquidacion"],
    dependencies=[Depends(PermissionChecker(_LIQUIDACION_READ_PERMISSIONS))],
)
async def calcular_ibl(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> IblStubResponse:
    """
    **Stub** — La integración con Imaginex para calcular el IBL está
    pendiente de especificación.

    Siempre retorna `ibl=null` con una nota informativa. El liquidador
    debe ingresar el IBL manualmente al guardar la liquidación.

    **Permisos**: AUDITOR, APROBADOR, ADMIN
    """
    result = await liquidacion_service.calcular_ibl_stub(db, incapacidad_id)
    return IblStubResponse(**result)


# ---------------------------------------------------------------------------
# GET /incapacidades/{id}/liquidacion/calcular-breakdown
# ---------------------------------------------------------------------------

@router.get(
    "/{incapacidad_id}/liquidacion/calcular-breakdown",
    response_model=BreakdownResponse,
    summary="Calcular desglose de liquidación (sin guardar)",
    tags=["liquidacion"],
    dependencies=[Depends(PermissionChecker(_LIQUIDACION_READ_PERMISSIONS))],
)
async def calcular_breakdown(
    incapacidad_id: UUID,
    ibl: Optional[Decimal] = Query(None, description="Ingreso Base de Liquidación"),
    dias: int = Query(..., ge=1, description="Días autorizados"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> BreakdownResponse:
    """
    Calcula el desglose de la liquidación **sin guardar** en base de datos.

    **Placeholder** — Todos los valores de desglose retornan `null` hasta
    que se confirmen los porcentajes con Helen (C1).

    Útil para que el liquidador vea una vista previa antes de guardar.

    **Permisos**: AUDITOR, APROBADOR, ADMIN
    """
    result = await liquidacion_service.calcular_breakdown(
        db=db,
        incapacidad_id=incapacidad_id,
        ibl=ibl,
        dias=dias,
    )
    return BreakdownResponse(**result)


# ---------------------------------------------------------------------------
# POST /incapacidades/{id}/liquidacion/devolver
# ---------------------------------------------------------------------------

@router.post(
    "/{incapacidad_id}/liquidacion/devolver",
    response_model=IncapacidadInDB,
    summary="Devolver incapacidad a EN_AUDITORIA",
    tags=["liquidacion"],
    dependencies=[Depends(PermissionChecker(_LIQUIDACION_WRITE_PERMISSIONS))],
)
async def devolver_a_auditoria(
    incapacidad_id: UUID,
    payload: LiquidacionDevolver,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> IncapacidadInDB:
    """
    Devuelve una incapacidad desde **LIQUIDACION** o **LIQUIDACION_PARCIAL**
    de regreso a **EN_AUDITORIA**.

    Útil cuando el liquidador detecta un error en los datos aprobados y necesita
    que el auditor los revise nuevamente.

    **Validaciones**:
    - La incapacidad debe estar en LIQUIDACION o LIQUIDACION_PARCIAL
    - La observación es obligatoria

    **Permisos**: AUDITOR, APROBADOR, ADMIN
    """
    incapacidad = await liquidacion_service.devolver_a_auditoria(
        db=db,
        incapacidad_id=incapacidad_id,
        observacion=payload.observacion,
        liquidador_id=current_user.id,
    )
    return IncapacidadInDB.model_validate(incapacidad)


# ---------------------------------------------------------------------------
# POST /incapacidades/{id}/liquidacion/completar
# ---------------------------------------------------------------------------

@router.post(
    "/{incapacidad_id}/liquidacion/completar",
    response_model=IncapacidadInDB,
    summary="Completar liquidación (→ PAGADA / PAGADA_PARCIAL)",
    tags=["liquidacion"],
    dependencies=[Depends(PermissionChecker(_LIQUIDACION_WRITE_PERMISSIONS))],
)
async def completar_liquidacion(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> IncapacidadInDB:
    """
    Completa la liquidación y transiciona la incapacidad al estado final de pago.

    - **LIQUIDACION** → **PAGADA**
    - **LIQUIDACION_PARCIAL** → **PAGADA_PARCIAL**

    **Validaciones**:
    - La incapacidad debe estar en LIQUIDACION o LIQUIDACION_PARCIAL
    - Debe existir una liquidación guardada para la incapacidad

    **Permisos**: AUDITOR, APROBADOR, ADMIN
    """
    incapacidad = await liquidacion_service.completar_liquidacion(
        db=db,
        incapacidad_id=incapacidad_id,
        liquidador_id=current_user.id,
    )
    return IncapacidadInDB.model_validate(incapacidad)
