"""
Endpoints públicos para radicación de pre-incapacidades.
Portal externo — sin autenticación JWT.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.usuario import Usuario
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


# ── Internal endpoints (require JWT authentication) ────────────────────────────

from app.schemas.pre_incapacidad import (  # noqa: E402 (already imported above, extended here)
    PreIncapacidadListItem,
    PreIncapacidadUpdate,
    DevolucionRequest,
    DevolucionResponse,
    PromocionResponse,
)
from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository


@router.get(
    "/",
    response_model=list[PreIncapacidadListItem],
    summary="[Interno] Listar pre-incapacidades",
    description="Lista pre-incapacidades para la bandeja interna. Requiere autenticación.",
)
async def listar_pre_incapacidades(
    estado: Optional[str] = Query(None, description="PENDIENTE | RECHAZADA | ERROR | DEVUELTA"),
    search: Optional[str] = Query(None, description="Buscar por documento o nombres del empleado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[PreIncapacidadListItem]:
    """Lista pre-incapacidades de la bandeja interna con conteo de issues."""
    from app.models.pre_incapacidad import PreIncapacidad
    from app.models.validation_inconsistencia import ValidationInconsistencia
    from sqlalchemy import select

    query = select(PreIncapacidad)

    if estado:
        query = query.where(PreIncapacidad.estado == estado)
    else:
        query = query.where(
            PreIncapacidad.estado.in_(["PENDIENTE", "RECHAZADA", "ERROR"])
        )

    if search:
        query = query.where(
            (PreIncapacidad.empleado_nombres.ilike(f"%{search}%")) |
            (PreIncapacidad.empleado_numero_documento.ilike(f"%{search}%")) |
            (PreIncapacidad.empresa_nombre.ilike(f"%{search}%"))
        )

    query = query.order_by(PreIncapacidad.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    pre_incapacidades = result.scalars().all()

    items = []
    for pre_inc in pre_incapacidades:
        count_query = select(
            ValidationInconsistencia.severidad,
            func.count(ValidationInconsistencia.id).label("cnt")
        ).where(
            ValidationInconsistencia.pre_incapacidad_id == pre_inc.id
        ).group_by(ValidationInconsistencia.severidad)

        count_result = await db.execute(count_query)
        counts = {row.severidad: row.cnt for row in count_result}

        items.append(PreIncapacidadListItem(
            id=pre_inc.id,
            numero_radicacion=pre_inc.numero_radicacion,
            estado=pre_inc.estado,
            tipo=pre_inc.tipo,
            empleado_nombres=pre_inc.empleado_nombres,
            empleado_numero_documento=pre_inc.empleado_numero_documento,
            empresa_nit=pre_inc.empresa_nit,
            empresa_nombre=pre_inc.empresa_nombre,
            fecha_inicio=pre_inc.fecha_inicio,
            fecha_fin=pre_inc.fecha_fin,
            dias_totales=pre_inc.dias_totales,
            total_errores=counts.get("ERROR", 0),
            total_warnings=counts.get("WARNING", 0),
            created_at=pre_inc.created_at,
        ))

    return items


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


@router.patch(
    "/{pre_incapacidad_id}",
    response_model=PreIncapacidadResponse,
    summary="[Interno] Corregir datos de pre-incapacidad",
    description="Permite al usuario interno corregir campos de la pre-incapacidad antes de promover.",
)
async def actualizar_pre_incapacidad(
    pre_incapacidad_id: UUID,
    data: PreIncapacidadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PreIncapacidadResponse:
    service = PreIncapacidadService(db)
    pre_inc = await service.repo.get_by_id(db, pre_incapacidad_id)
    if not pre_inc:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Pre-incapacidad {pre_incapacidad_id} no encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pre_inc, field, value)

    if "fecha_inicio" in update_data or "fecha_fin" in update_data:
        pre_inc.dias_totales = (pre_inc.fecha_fin - pre_inc.fecha_inicio).days + 1

    db.add(pre_inc)
    await db.commit()
    await db.refresh(pre_inc)
    return PreIncapacidadResponse.model_validate(pre_inc)


@router.post(
    "/{pre_incapacidad_id}/devolver",
    response_model=DevolucionResponse,
    summary="[Interno] Devolver pre-incapacidad al solicitante",
    description=(
        "Cambia el estado a DEVUELTA, guarda el motivo, y envía una carta formal "
        "por email al solicitante. Requiere autenticación."
    ),
)
async def devolver_pre_incapacidad(
    pre_incapacidad_id: UUID,
    data: DevolucionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> DevolucionResponse:
    service = PreIncapacidadService(db)
    repo = service.repo

    pre_inc = await repo.get_by_id(db, pre_incapacidad_id)
    if not pre_inc:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Pre-incapacidad {pre_incapacidad_id} no encontrada")

    pre_inc.estado = "DEVUELTA"
    pre_inc.motivo_devolucion = data.motivo
    db.add(pre_inc)
    await db.commit()
    await db.refresh(pre_inc)

    email_sent = False
    try:
        from app.tasks.email_tasks import send_devolucion_pre_incapacidad_email_task
        send_devolucion_pre_incapacidad_email_task.delay(
            correo_solicitante=pre_inc.solicitante_correo,
            solicitante_nombre=pre_inc.solicitante_nombres,
            numero_radicacion=str(pre_inc.numero_radicacion),
            empleado_nombre=pre_inc.empleado_nombres,
            empleado_documento=pre_inc.empleado_numero_documento,
            empresa_nombre=pre_inc.empresa_nombre or "Independiente",
            fecha_inicio=str(pre_inc.fecha_inicio),
            dias_totales=pre_inc.dias_totales,
            motivo=data.motivo,
            usuario_nombre=f"{current_user.nombres} {current_user.apellidos}",
        )
        email_sent = True
    except Exception as e:
        import logging
        logging.error(f"Failed to enqueue devolucion email for {pre_incapacidad_id}: {e}")

    return DevolucionResponse(
        id=pre_inc.id,
        estado=pre_inc.estado,
        motivo_devolucion=pre_inc.motivo_devolucion,
        email_enviado=email_sent,
    )


@router.post(
    "/{pre_incapacidad_id}/promover",
    response_model=PromocionResponse,
    summary="[Interno] Promover manualmente a incapacidad",
    description=(
        "Limpia validaciones previas, re-valida con la data actual, y crea la Incapacidad "
        "si no quedan ERRORs. Requiere autenticación."
    ),
)
async def promover_pre_incapacidad(
    pre_incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PromocionResponse:
    from app.services.pre_incapacidad_promotion_service import PromotePreIncapacidadService

    service = PromotePreIncapacidadService(db)
    result = await service.promote_pre_incapacidad(pre_incapacidad_id)

    return PromocionResponse(
        success=result.success,
        pre_incapacidad_id=result.pre_incapacidad_id,
        incapacidad_id=result.incapacidad_id,
        errors=result.validation_summary.errors,
        warnings=result.validation_summary.warnings,
        message="Incapacidad creada exitosamente" if result.success else result.error_message or "Validación fallida",
    )
