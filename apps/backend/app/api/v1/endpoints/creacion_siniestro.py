"""
Endpoint para el flujo CREACION_SINIESTRO.

POST /incapacidades/{incapacidad_id}/creacion-siniestro
  — Solo ADMINISTRADOR.
  — Recibe los datos del siniestro, lo crea en BD, vincula a la incapacidad
    y la retorna directamente a EN_AUDITORIA en la misma transacción.
"""
from datetime import date
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
from app.utils.enums import RolUsuario, TipoSiniestro

router = APIRouter()


class CreacionSiniestroRequest(BaseModel):
    fecha_siniestro: date = Field(
        ...,
        description="Fecha en que ocurrió el accidente o evento",
    )
    tipo_siniestro: TipoSiniestro = Field(
        ...,
        description="Tipo de siniestro: ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL o ACCIDENTE_TRAYECTO",
        examples=[TipoSiniestro.ACCIDENTE_TRABAJO],
    )
    descripcion: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Descripción detallada del siniestro (mínimo 10 caracteres)",
    )
    observacion: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Observación obligatoria para el historial de estado",
    )


@router.post(
    "/{incapacidad_id}/creacion-siniestro",
    response_model=IncapacidadInDB,
    status_code=status.HTTP_200_OK,
    summary="Crear siniestro y retornar incapacidad a EN_AUDITORIA",
    description=(
        "Solo ADMINISTRADOR. "
        "Crea el siniestro a partir de los datos del formulario, lo vincula a la "
        "incapacidad ARL (que debe estar en CREACION_SINIESTRO) y la retorna directamente "
        "a EN_AUDITORIA en la misma transacción. Si la creación del siniestro falla, "
        "el estado de la incapacidad no cambia."
    ),
)
async def crear_siniestro(
    incapacidad_id: UUID,
    body: CreacionSiniestroRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IncapacidadInDB:
    """
    Crea un siniestro y transiciona la incapacidad de CREACION_SINIESTRO a EN_AUDITORIA.

    Flujo:
    1. Valida que el usuario sea ADMINISTRADOR.
    2. Valida que la incapacidad sea ARL y esté en CREACION_SINIESTRO.
    3. Crea el siniestro en BD con empleado_id/empresa_id de la incapacidad.
    4. Vincula siniestro_id en la incapacidad y cambia estado a EN_AUDITORIA.
    5. Retorna la incapacidad actualizada.
    """
    if current_user.rol != RolUsuario.ADMIN:
        raise ForbiddenException(
            "Solo el ADMINISTRADOR puede crear siniestros desde esta bandeja"
        )

    return await incapacidad_service.iniciar_creacion_siniestro(
        db=db,
        incapacidad_id=incapacidad_id,
        fecha_siniestro=body.fecha_siniestro,
        tipo_siniestro=body.tipo_siniestro,
        descripcion=body.descripcion,
        usuario_id=current_user.id,
        observacion=body.observacion,
    )
