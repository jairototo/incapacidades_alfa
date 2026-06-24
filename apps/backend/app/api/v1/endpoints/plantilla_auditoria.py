"""
Endpoints para Plantilla de Auditoría.

Permite a auditores y administradores crear/actualizar y consultar
la plantilla de texto de una incapacidad específica.

Rutas:
  POST   /incapacidades/{incapacidad_id}/plantilla-auditoria
  GET    /incapacidades/{incapacidad_id}/plantilla-auditoria
  GET    /incapacidades/{incapacidad_id}/plantilla-auditoria/texto-copiable
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.plantilla_auditoria import (
    PlantillaAuditoriaCreate,
    PlantillaAuditoriaResponse,
)
from app.services.plantilla_auditoria_service import plantilla_auditoria_service
from app.utils.enums import RolUsuario

router = APIRouter()

_ALLOWED_ROLES = {RolUsuario.ADMIN, RolUsuario.AUDITOR}


def _check_role(current_user: Usuario) -> None:
    """Verificar que el usuario tenga rol ADMIN o AUDITOR."""
    if current_user.rol not in _ALLOWED_ROLES:
        raise ForbiddenException(
            "Solo usuarios con rol AUDITOR o ADMINISTRADOR pueden gestionar plantillas de auditoría"
        )


@router.post(
    "/{incapacidad_id}/plantilla-auditoria",
    response_model=PlantillaAuditoriaResponse,
    status_code=status.HTTP_200_OK,
    summary="Crear o actualizar plantilla de auditoría",
    description=(
        "Crea o actualiza la plantilla de auditoría de una incapacidad. "
        "Solo accesible por AUDITOR y ADMINISTRADOR. "
        "Si ya existe una plantilla para esa incapacidad, la reemplaza."
    ),
)
async def create_or_update_plantilla(
    incapacidad_id: UUID,
    data: PlantillaAuditoriaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlantillaAuditoriaResponse:
    """Crear o actualizar plantilla de auditoría para una incapacidad."""
    _check_role(current_user)

    plantilla = await plantilla_auditoria_service.create_or_update(
        db=db,
        incapacidad_id=incapacidad_id,
        data=data,
        usuario_id=current_user.id,
    )

    return PlantillaAuditoriaResponse.model_validate(plantilla)


@router.get(
    "/{incapacidad_id}/plantilla-auditoria",
    response_model=PlantillaAuditoriaResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener plantilla de auditoría",
    description=(
        "Retorna la plantilla de auditoría de una incapacidad. "
        "Solo accesible por AUDITOR y ADMINISTRADOR."
    ),
)
async def get_plantilla(
    incapacidad_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlantillaAuditoriaResponse:
    """Obtener la plantilla de auditoría de una incapacidad."""
    _check_role(current_user)

    plantilla = await plantilla_auditoria_service.get_by_incapacidad(
        db=db,
        incapacidad_id=incapacidad_id,
    )

    return PlantillaAuditoriaResponse.model_validate(plantilla)


@router.get(
    "/{incapacidad_id}/plantilla-auditoria/texto-copiable",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Obtener texto copiable de la plantilla",
    description=(
        "Retorna el texto pre-formateado de la plantilla de auditoría, "
        "listo para pegar en Arpis. "
        "Solo accesible por AUDITOR y ADMINISTRADOR."
    ),
)
async def get_texto_copiable(
    incapacidad_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Obtener texto copiable formateado para pegar en Arpis."""
    _check_role(current_user)

    plantilla = await plantilla_auditoria_service.get_by_incapacidad(
        db=db,
        incapacidad_id=incapacidad_id,
    )

    texto = plantilla_auditoria_service.build_texto_copiable(plantilla)
    return {"texto": texto}
