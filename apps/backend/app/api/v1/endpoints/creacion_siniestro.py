"""
Endpoint para el flujo CREACION_SINIESTRO.

POST /incapacidades/{incapacidad_id}/creacion-siniestro
  — Solo ADMINISTRADOR.
  — Guarda numero_siniestro, cambia estado a CREACION_SINIESTRO y encola
    la tarea Celery que vincula el siniestro externo.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.incapacidad import IncapacidadInDB
from app.services.incapacidad_service import incapacidad_service
from app.tasks.siniestro_tasks import vincular_siniestro_externo_task
from app.utils.enums import RolUsuario

router = APIRouter()


class CreacionSiniestroRequest(BaseModel):
    numero_siniestro: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Número del siniestro en el sistema externo (RRHH/ARL)",
        examples=["SINX-2026-001"],
    )
    observacion: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Observación obligatoria para el historial de estado",
        examples=["Vinculando siniestro externo SINX-2026-001"],
    )


@router.post(
    "/{incapacidad_id}/creacion-siniestro",
    response_model=IncapacidadInDB,
    status_code=status.HTTP_200_OK,
    summary="Iniciar vinculación de siniestro externo",
    description=(
        "Solo ADMINISTRADOR. "
        "Cambia la incapacidad ARL a estado CREACION_SINIESTRO y encola la tarea "
        "Celery que consulta el sistema externo, crea el siniestro local y retorna "
        "la incapacidad a EN_AUDITORIA automáticamente."
    ),
)
async def iniciar_creacion_siniestro(
    incapacidad_id: UUID,
    body: CreacionSiniestroRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IncapacidadInDB:
    """
    Inicia la vinculación de un siniestro externo con una incapacidad ARL.

    Flujo:
    1. Valida que el usuario sea ADMINISTRADOR.
    2. Valida que la incapacidad sea ARL y esté en EN_AUDITORIA.
    3. Guarda numero_siniestro y cambia estado a CREACION_SINIESTRO.
    4. Encola tarea Celery `vincular_siniestro_externo_task`.
    5. Retorna la incapacidad actualizada.
    """
    if current_user.rol != RolUsuario.ADMIN:
        raise ForbiddenException(
            "Solo usuarios con rol ADMINISTRADOR pueden vincular siniestros externos"
        )

    inc = await incapacidad_service.iniciar_creacion_siniestro(
        db=db,
        incapacidad_id=incapacidad_id,
        numero_siniestro_externo=body.numero_siniestro,
        usuario_id=current_user.id,
        observacion=body.observacion,
    )

    # Encolar tarea Celery (no bloqueante)
    vincular_siniestro_externo_task.delay(str(incapacidad_id), body.numero_siniestro)

    return inc
