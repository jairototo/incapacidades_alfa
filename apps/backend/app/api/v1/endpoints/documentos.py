"""
Endpoints para gestión de documentos.
"""
from typing import List
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.documento import (
    DocumentoResponse,
    DocumentoListItem,
    DocumentoUploadResponse
)
from app.services.documento_service import DocumentoService

logger = logging.getLogger(__name__)


router = APIRouter()


# Dummy function for get_current_user until auth is implemented
async def get_current_user(db: AsyncSession = Depends(get_db)) -> Usuario:
    """Placeholder para get_current_user."""
    from sqlalchemy import select
    result = await db.execute(select(Usuario).limit(1))
    return result.scalar_one()


# Dummy permission checker
class Permissions:
    """Permisos del sistema."""
    DOCUMENTO_CREATE = "documento_create"
    DOCUMENTO_READ = "documento_read"
    DOCUMENTO_UPDATE = "documento_update"
    DOCUMENTO_DELETE = "documento_delete"


class PermissionChecker:
    """Verificador de permisos (placeholder)."""
    
    def __init__(self, required_permissions: list[str]):
        """Inicializa el checker."""
        self.required_permissions = required_permissions
    
    async def __call__(self, current_user: Usuario = Depends(get_current_user)) -> bool:
        """Verifica permisos (siempre retorna True por ahora)."""
        return True


@router.post(
    "/upload",
    response_model=DocumentoUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionChecker([Permissions.DOCUMENTO_CREATE]))],
    summary="Subir documento",
    description="Sube un archivo y lo asocia a una incapacidad"
)
async def upload_documento(
    incapacidad_id: UUID = Form(..., description="ID de la incapacidad"),
    tipo_documento: str = Form(..., description="Tipo de documento"),
    file: UploadFile = File(..., description="Archivo a subir"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Sube un nuevo documento asociado a una incapacidad.
    
    - **incapacidad_id**: ID de la incapacidad
    - **tipo_documento**: Tipo de documento (INCAPACIDAD_MEDICA, CEDULA, etc.)
    - **file**: Archivo a subir (PDF, JPG, PNG, DOCX - máx 10MB)
    
    Returns:
        Documento creado con URL de descarga temporal
    """
    service = DocumentoService(db)
    
    # Subir documento
    documento = await service.upload_documento(
        incapacidad_id=incapacidad_id,
        file_data=file.file,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        tipo_documento=tipo_documento,
        uploaded_by_id=current_user.id
    )
    
    # Generar URL de descarga
    url_descarga = await service.get_download_url(documento.id, expires_hours=24)
    
    return DocumentoUploadResponse(
        documento=DocumentoResponse.model_validate(documento),
        url_descarga=url_descarga
    )


@router.get(
    "/{documento_id}",
    response_model=DocumentoResponse,
    dependencies=[Depends(PermissionChecker([Permissions.DOCUMENTO_READ]))],
    summary="Obtener documento",
    description="Obtiene la información de un documento por ID"
)
async def get_documento(
    documento_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la información de un documento.
    
    - **documento_id**: ID del documento
    
    Returns:
        Información del documento
    """
    service = DocumentoService(db)
    documento = await service.get_documento(documento_id)
    return DocumentoResponse.model_validate(documento)


@router.get(
    "/{documento_id}/view",
    dependencies=[Depends(PermissionChecker([Permissions.DOCUMENTO_READ]))],
    summary="Ver documento",
    description="Sirve el documento directamente para visualización en navegador (imagenes, PDFs)"
)
async def view_documento(
    documento_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Sirve el documento directamente para visualización.
    
    - **documento_id**: ID del documento
    
    Returns:
        El archivo con los headers aproppiados para visualización en el navegador
    """
    service = DocumentoService(db)
    documento = await service.get_documento(documento_id)
    
    try:
        # Obtener el contenido del archivo del storage
        file_content = await service.get_documento_contenido(documento_id)
        
        # Determinar el content-type basado en la extensión
        filename = documento.nombre_original.lower()
        if filename.endswith('.pdf'):
            content_type = 'application/pdf'
        elif filename.endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif filename.endswith('.png'):
            content_type = 'image/png'
        elif filename.endswith('.gif'):
            content_type = 'image/gif'
        elif filename.endswith('.webp'):
            content_type = 'image/webp'
        else:
            content_type = 'application/octet-stream'
        
        logger.info(f"Sirviendo documento {documento_id} con content-type: {content_type}")
        
        return StreamingResponse(
            iter([file_content]),
            media_type=content_type,
            headers={
                'Content-Disposition': f'inline; filename="{documento.nombre_original}"'
            }
        )
    except Exception as e:
        logger.error(f"Error sirviendo documento {documento_id}: {e}")
        raise


@router.get(
    "/{documento_id}/download",
    dependencies=[Depends(PermissionChecker([Permissions.DOCUMENTO_READ]))],
    summary="Descargar documento",
    description="Genera una URL firmada para descargar el archivo"
)
async def download_documento(
    documento_id: UUID,
    expires_hours: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Genera una URL firmada para descargar el documento.
    
    - **documento_id**: ID del documento
    - **expires_hours**: Horas de validez de la URL (por defecto 1)
    
    Returns:
        URL firmada para descarga y tiempo de expiración
    """
    service = DocumentoService(db)
    
    # Verificar que el documento existe
    documento = await service.get_documento(documento_id)
    
    # Generar URL firmada
    url = await service.get_download_url(documento_id, expires_hours)
    
    return {
        "url": url,
        "expires_in": expires_hours * 3600,  # en segundos
        "nombre_archivo": documento.nombre_original
    }


@router.delete(
    "/{documento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(PermissionChecker([Permissions.DOCUMENTO_DELETE]))],
    summary="Eliminar documento",
    description="Elimina un documento (soft delete por defecto)"
)
async def delete_documento(
    documento_id: UUID,
    hard_delete: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Elimina un documento.
    
    - **documento_id**: ID del documento
    - **hard_delete**: Si True, elimina también el archivo del storage
    
    Returns:
        Sin contenido (204)
    """
    service = DocumentoService(db)
    await service.delete_documento(documento_id, hard_delete=hard_delete)
    return None


@router.get(
    "/incapacidades/{incapacidad_id}",
    response_model=List[DocumentoListItem],
    dependencies=[Depends(PermissionChecker([Permissions.DOCUMENTO_READ]))],
    summary="Listar documentos de incapacidad",
    description="Lista todos los documentos asociados a una incapacidad"
)
async def list_documentos_incapacidad(
    incapacidad_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista documentos de una incapacidad.
    
    - **incapacidad_id**: ID de la incapacidad
    - **skip**: Registros a saltar
    - **limit**: Máximo de registros a retornar
    
    Returns:
        Lista de documentos
    """
    service = DocumentoService(db)
    documentos = await service.list_by_incapacidad(
        incapacidad_id=incapacidad_id,
        skip=skip,
        limit=limit
    )
    return [DocumentoListItem.model_validate(doc) for doc in documentos]


@router.get(
    "/siniestros/{siniestro_id}",
    response_model=List[DocumentoListItem],
    dependencies=[Depends(PermissionChecker([Permissions.DOCUMENTO_READ]))],
    summary="Listar documentos de siniestro",
    description="Lista todos los documentos asociados a un siniestro"
)
async def list_documentos_siniestro(
    siniestro_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista documentos de un siniestro.
    
    - **siniestro_id**: ID del siniestro
    - **skip**: Registros a saltar
    - **limit**: Máximo de registros a retornar
    
    Returns:
        Lista de documentos
    """
    service = DocumentoService(db)
    documentos = await service.list_by_siniestro(
        siniestro_id=siniestro_id,
        skip=skip,
        limit=limit
    )
    return [DocumentoListItem.model_validate(doc) for doc in documentos]
