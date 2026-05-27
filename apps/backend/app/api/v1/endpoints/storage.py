"""
Endpoints para servir archivos del storage filesystem.
"""
import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path as PathParam, Depends
from fastapi.responses import FileResponse
from loguru import logger

from apps.backend.app.core.config import settings
from apps.backend.app.core.security import get_current_user
from apps.backend.app.models.usuario import Usuario


router = APIRouter()


@router.get("/files/{filepath:path}")
async def serve_file(
    filepath: str = PathParam(..., description="Ruta relativa del archivo")
):
    """
    Sirve archivos del filesystem local.
    
    Solo funciona si STORAGE_BACKEND=filesystem.
    Requiere autenticación para acceder a los archivos.
    
    Args:
        filepath: Ruta relativa del archivo (ej: "documentos/2026/01/file.pdf")
        current_user: Usuario autenticado
        
    Returns:
        Archivo solicitado
        
    Raises:
        HTTPException 403: Si STORAGE_BACKEND no es filesystem
        HTTPException 404: Si el archivo no existe
        HTTPException 403: Si se intenta path traversal
        
    Examples:
        GET /api/v1/storage/files/documentos/incapacidades/2026/01/abc123.pdf
    """
    # Validar que estamos en modo filesystem
    if settings.STORAGE_BACKEND != "filesystem":
        logger.warning(
            f"Intento de acceder a archivos en modo {settings.STORAGE_BACKEND}"
        )
        raise HTTPException(
            status_code=403,
            detail="File serving solo disponible en modo filesystem"
        )
    
    # Construir ruta completa
    base_path = Path(settings.FILESYSTEM_BASE_PATH).resolve()
    file_path = (base_path / filepath).resolve()
    
    # SEGURIDAD: Validar que el path no escape del directorio base (path traversal)
    try:
        file_path.relative_to(base_path)
    except ValueError:
        logger.error(
            f"Intento de path traversal bloqueado: {filepath} -> {file_path}",
            extra={"filepath": filepath}
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado"
        )
    
    # Verificar que el archivo existe
    if not file_path.exists() or not file_path.is_file():
        logger.warning(
            f"Archivo no encontrado: {filepath}",
            extra={"filepath": filepath}
        )
        raise HTTPException(
            status_code=404,
            detail="Archivo no encontrado"
        )
    
    # Detectar tipo MIME por extensión
    extension = file_path.suffix.lower()
    mime_map = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    media_type = mime_map.get(extension, 'application/octet-stream')
    
    logger.info(
        f"Archivo servido: {filepath}",
        extra={
            "filepath": filepath,
            "size_bytes": file_path.stat().st_size
        }
    )
    
    # Servir archivo con headers apropiados
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name,
        headers={
            "Cache-Control": "private, max-age=3600",  # Cache 1 hora
            "X-Content-Type-Options": "nosniff"  # Seguridad
        }
    )


@router.head("/files/{filepath:path}")
async def check_file_exists(
    filepath: str = PathParam(..., description="Ruta relativa del archivo")
):
    """
    Verifica si un archivo existe (HEAD request).
    
    Útil para validar existencia sin descargar el archivo completo.
    
    Args:
        filepath: Ruta relativa del archivo
        current_user: Usuario autenticado
        
    Returns:
        Headers del archivo
        
    Raises:
        HTTPException 404: Si el archivo no existe
    """
    if settings.STORAGE_BACKEND != "filesystem":
        raise HTTPException(
            status_code=403,
            detail="File serving solo disponible en modo filesystem"
        )
    
    base_path = Path(settings.FILESYSTEM_BASE_PATH).resolve()
    file_path = (base_path / filepath).resolve()
    
    # Validar path traversal
    try:
        file_path.relative_to(base_path)
    except ValueError:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return {"exists": True, "size": file_path.stat().st_size}
