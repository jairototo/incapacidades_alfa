"""
Endpoints públicos para radicación de pre-incapacidades.
Portal externo — sin autenticación JWT.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.pre_incapacidad import (
    PreIncapacidadCreate,
    PreDocumentoResponse,
    PreIncapacidadRadicadaResponse,
    PreIncapacidadResponse,
)
from app.services.pre_incapacidad_service import (
    PreIncapacidadService,
    TIPOS_DOCUMENTO_VALIDOS,
)

router = APIRouter()


@router.post(
    "/radicar",
    response_model=PreIncapacidadRadicadaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Radicar pre-incapacidad ARL",
    description=(
        "Recibe los datos planos de una radicación de incapacidad ARL desde el portal "
        "externo. No valida existencia en BD de empresa ni empleado. Genera un número "
        "de radicación secuencial y persiste el registro como PENDIENTE para su "
        "procesamiento posterior por un job programado."
    ),
)
async def radicar_pre_incapacidad(
    data: PreIncapacidadCreate,
    db: AsyncSession = Depends(get_db),
) -> PreIncapacidadRadicadaResponse:
    """
    Radica una pre-incapacidad ARL desde el portal externo.

    - Sin empresa: se asume trabajador independiente.
    - Todos los campos de texto se capturan tal como los ingresa el usuario.
    - La incapacidad real se creará en un job posterior de procesamiento.
    - Enqeueues async promotion task after creation (fire-and-forget).
    - IMPORTANTE: Documentos son críticos - si fallan, esta radicación debería fallar también.
    """
    service = PreIncapacidadService(db)
    pre_inc = await service.radicar(data)

    # Commit transaction explicitly to ensure pre-incapacidad is visible to other sessions
    await db.commit()

    # Enqueue promotion task (fire-and-forget)
    try:
        from app.tasks.incapacidad_tasks import promote_pre_incapacidad_task
        promote_pre_incapacidad_task.delay(str(pre_inc.id))
    except Exception as e:
        # Log but don't fail the endpoint if task enqueueing fails
        import logging
        logging.error(f"Failed to enqueue promotion task for {pre_inc.id}: {e}")

    return PreIncapacidadRadicadaResponse(
        id=pre_inc.id,
        numero_radicacion=pre_inc.numero_radicacion,
        estado=pre_inc.estado,
    )


@router.post(
    "/{pre_incapacidad_id}/documentos",
    response_model=PreDocumentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir documento a pre-incapacidad",
    description=(
        "Sube un archivo asociado a una pre-incapacidad. "
        "Si la subida falla parcialmente, el registro queda con estado=ERROR "
        "para ser reintentado por el job de procesamiento. "
        "Tipos válidos: INCAPACIDAD_MEDICA | HISTORIA_CLINICA | SOPORTE_ADICIONAL"
    ),
)
async def subir_documento_pre_incapacidad(
    pre_incapacidad_id: UUID,
    tipo_documento: str = Form(
        ...,
        description=f"Tipo de documento: {' | '.join(TIPOS_DOCUMENTO_VALIDOS)}",
    ),
    file: UploadFile = File(..., description="Archivo a subir (PDF, JPG, PNG, DOC, DOCX — máx 10 MB)"),
    db: AsyncSession = Depends(get_db),
) -> PreDocumentoResponse:
    """
    Sube un documento a una pre-incapacidad existente.

    El registro se crea en BD independientemente de si el storage tuvo éxito,
    garantizando trazabilidad completa de todos los intentos.
    """
    service = PreIncapacidadService(db)
    pre_doc = await service.subir_documento(
        pre_incapacidad_id=pre_incapacidad_id,
        file_data=file.file,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        tipo_documento=tipo_documento,
    )
    # Commit transaction explicitly to ensure pre_documento is visible to other sessions
    await db.commit()
    return PreDocumentoResponse.model_validate(pre_doc)


@router.get(
    "/{pre_incapacidad_id}",
    response_model=PreIncapacidadResponse,
    summary="Consultar pre-incapacidad",
    description="Consulta el estado de una pre-incapacidad por su ID.",
)
async def get_pre_incapacidad(
    pre_incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PreIncapacidadResponse:
    service = PreIncapacidadService(db)
    pre_inc = await service.get_by_id(pre_incapacidad_id)
    return PreIncapacidadResponse.model_validate(pre_inc)
