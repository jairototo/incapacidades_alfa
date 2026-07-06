"""
Endpoint para solicitar creación de siniestro desde la auditoría.

POST /incapacidades/{incapacidad_id}/auditar-creacion-siniestro
  — AUDITOR o ADMINISTRADOR.
  — Transición única: EN_AUDITORIA → CREACION_SINIESTRO.
  — No crea ni vincula siniestros; solo cambia el estado para que el
    ADMINISTRADOR complete la creación desde la bandeja correspondiente.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, Permissions, PermissionChecker
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.incapacidad import IncapacidadInDB
from app.services.incapacidad_service import incapacidad_service

router = APIRouter()


class AuditarCreacionSiniestroRequest(BaseModel):
    observacion: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Observación obligatoria para el historial de estado",
        examples=["No se encontraron siniestros candidatos para este empleado"],
    )


@router.post(
    "/{incapacidad_id}/auditar-creacion-siniestro",
    response_model=IncapacidadInDB,
    status_code=status.HTTP_200_OK,
    summary="Solicitar creación de siniestro (AUDITOR)",
    description=(
        "AUDITOR o ADMINISTRADOR. "
        "Transiciona la incapacidad ARL de EN_AUDITORIA a CREACION_SINIESTRO "
        "para que el ADMINISTRADOR pueda completar la creación del siniestro "
        "desde la bandeja correspondiente."
    ),
    dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_AUDIT]))],
)
async def auditar_solicitar_creacion_siniestro(
    incapacidad_id: UUID,
    body: AuditarCreacionSiniestroRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IncapacidadInDB:
    await incapacidad_service.solicitar_creacion_siniestro(
        db=db,
        incapacidad_id=incapacidad_id,
        observacion=body.observacion,
        usuario_id=current_user.id,
    )
    return await incapacidad_service.get_incapacidad(db, incapacidad_id)
