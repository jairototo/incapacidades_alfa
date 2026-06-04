"""
Servicio para gestión de documentos.
"""
import os
from datetime import timedelta
from typing import BinaryIO, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    ValidationException,
    FileException
)
from app.core.storage_core import storage_backend
from app.db.repositories.documento_repository import DocumentoRepository
from app.models.documento import Documento
from app.schemas.documento import DocumentoCreate, DocumentoUpdate, DocumentoResponse
from app.utils.enums import AccionAuditoria


class DocumentoService:
    """Servicio para operaciones con documentos."""
    
    # Tipos MIME permitidos
    ALLOWED_MIME_TYPES = {
        "application/pdf": [".pdf"],
        "image/jpeg": [".jpg", ".jpeg"],
        "image/png": [".png"],
        "application/msword": [".doc"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"]
    }
    
    # Extensiones permitidas
    ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]
    
    # Tamaño máximo de archivo en bytes (10MB por defecto)
    MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa el servicio.
        
        Args:
            db: Sesión de base de datos
        """
        self.repository = DocumentoRepository()
        self.storage = storage_backend  # Usa el singleton del backend configurado
        self.db = db
    
    def _validate_file_extension(self, filename: str) -> None:
        """
        Valida la extensión del archivo.
        
        Args:
            filename: Nombre del archivo
            
        Raises:
            ValidationException: Si la extensión no es permitida
        """
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            allowed = ", ".join(self.ALLOWED_EXTENSIONS)
            raise ValidationException(
                f"Extensión de archivo no permitida. Permitidas: {allowed}"
            )
    
    def _validate_file_size(self, file_size: int) -> None:
        """
        Valida el tamaño del archivo.
        
        Args:
            file_size: Tamaño del archivo en bytes
            
        Raises:
            ValidationException: Si el tamaño excede el límite
        """
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationException(
                f"Archivo demasiado grande. Tamaño máximo: {max_mb}MB"
            )
    
    def _validate_mime_type(self, mime_type: str) -> None:
        """
        Valida el tipo MIME del archivo.
        
        Args:
            mime_type: Tipo MIME del archivo
            
        Raises:
            ValidationException: Si el tipo MIME no es permitido
        """
        if mime_type not in self.ALLOWED_MIME_TYPES:
            allowed = ", ".join(self.ALLOWED_MIME_TYPES.keys())
            raise ValidationException(
                f"Tipo de archivo no permitido. Permitidos: {allowed}"
            )
    
    async def upload_documento(
        self,
        incapacidad_id: UUID,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        tipo_documento: str,
        uploaded_by_id: UUID
    ) -> Documento:
        """
        Sube un documento y crea el registro en BD.
        
        Args:
            incapacidad_id: ID de la incapacidad
            file_data: Datos del archivo
            filename: Nombre original del archivo
            content_type: Tipo MIME del archivo
            tipo_documento: Tipo de documento
            uploaded_by_id: ID del usuario que sube el archivo
            
        Returns:
            Documento creado
            
        Raises:
            ValidationException: Si el archivo no cumple las validaciones
            FileException: Si hay error subiendo el archivo
        """
        # Validar extensión y tipo MIME
        self._validate_file_extension(filename)
        self._validate_mime_type(content_type)
        
        try:
            # Subir archivo a MinIO
            ruta_storage, hash_md5, hash_sha256, tamanio_bytes = self.storage.upload_file(
                file_data=file_data,
                file_name=filename,
                content_type=content_type,
                folder="documentos"
            )
            
            # Validar tamaño
            self._validate_file_size(tamanio_bytes)
            
            # Crear registro en BD
            documento_data = DocumentoCreate(
                incapacidad_id=incapacidad_id,
                tipo_documento=tipo_documento,
                nombre_archivo=os.path.basename(ruta_storage),
                nombre_original=filename,
                ruta_storage=ruta_storage,
                bucket=settings.STORAGE_BUCKET,
                mime_type=content_type,
                tamanio_bytes=tamanio_bytes,
                hash_md5=hash_md5,
                hash_sha256=hash_sha256,
                uploaded_by_id=uploaded_by_id
            )
            
            documento = await self.repository.create(self.db, documento_data.model_dump())
            
            logger.info(
                f"Documento subido exitosamente: {documento.id} "
                f"(incapacidad: {incapacidad_id}, usuario: {uploaded_by_id})"
            )
            
            # TODO: Registrar en historial de auditoría
            # await self._registrar_auditoria(
            #     incapacidad_id, uploaded_by_id, AccionAuditoria.UPLOAD_FILE
            # )
            
            return documento
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error subiendo documento: {e}")
            raise FileException(f"Error al subir archivo: {str(e)}")
    
    async def get_documento(self, documento_id: UUID) -> Documento:
        """
        Obtiene un documento por ID.
        
        Args:
            documento_id: ID del documento
            
        Returns:
            Documento encontrado
            
        Raises:
            NotFoundException: Si el documento no existe
        """
        documento = await self.repository.get(self.db, documento_id)
        if not documento:
            raise NotFoundException(f"Documento {documento_id} no encontrado")
        return documento
    
    async def get_download_url(
        self,
        documento_id: UUID,
        expires_hours: int = 1
    ) -> str:
        """
        Genera una URL firmada para descargar el documento.
        
        Args:
            documento_id: ID del documento
            expires_hours: Horas hasta que expire la URL
            
        Returns:
            URL firmada para descarga
            
        Raises:
            NotFoundException: Si el documento no existe
            FileException: Si hay error generando la URL
        """
        documento = await self.get_documento(documento_id)
        
        try:
            url = self.storage.get_presigned_url(
                object_path=documento.ruta_storage,
                expires=timedelta(hours=expires_hours)
            )
            
            logger.info(f"URL de descarga generada para documento: {documento_id}")
            
            # TODO: Registrar en historial de auditoría
            # await self._registrar_auditoria(
            #     documento.incapacidad_id, user_id, AccionAuditoria.DOWNLOAD_FILE
            # )
            
            return url
            
        except Exception as e:
            logger.error(f"Error generando URL de descarga: {e}")
            raise FileException(f"Error generando URL de descarga: {str(e)}")
    
    async def delete_documento(
        self,
        documento_id: UUID,
        hard_delete: bool = False
    ) -> None:
        """
        Elimina un documento (soft delete por defecto).
        
        Args:
            documento_id: ID del documento
            hard_delete: Si True, elimina físicamente el archivo del storage
            
        Raises:
            NotFoundException: Si el documento no existe
        """
        documento = await self.get_documento(documento_id)
        
        if hard_delete:
            # Eliminar archivo del storage
            try:
                self.storage.delete_file(documento.ruta_storage)
                logger.info(f"Archivo eliminado del storage: {documento.ruta_storage}")
            except Exception as e:
                logger.error(f"Error eliminando archivo del storage: {e}")
                # Continuar con eliminación de BD aunque falle el storage
        
        # Eliminar registro de BD
        await self.repository.delete(self.db, documento_id)
        logger.info(f"Documento eliminado: {documento_id} (hard: {hard_delete})")
    
    async def list_by_incapacidad(
        self,
        incapacidad_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Documento]:
        """
        Lista documentos de una incapacidad.
        
        Args:
            incapacidad_id: ID de la incapacidad
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de documentos
        """
        return await self.repository.get_by_incapacidad(
            self.db,
            incapacidad_id=incapacidad_id,
            skip=skip,
            limit=limit
        )
    
    async def list_by_siniestro(
        self,
        siniestro_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Documento]:
        """
        Lista documentos de un siniestro.
        
        Args:
            siniestro_id: ID del siniestro
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de documentos
        """
        return await self.repository.get_by_siniestro(
            self.db,
            siniestro_id=siniestro_id,
            skip=skip,
            limit=limit
        )
    
    async def update_documento(
        self,
        documento_id: UUID,
        data: DocumentoUpdate
    ) -> Documento:
        """
        Actualiza un documento.
        
        Args:
            documento_id: ID del documento
            data: Datos a actualizar
            
        Returns:
            Documento actualizado
            
        Raises:
            NotFoundException: Si el documento no existe
        """
        documento = await self.get_documento(documento_id)
        
        updated = await self.repository.update(
            self.db,
            documento_id,
            data.model_dump(exclude_unset=True)
        )
        
        logger.info(f"Documento actualizado: {documento_id}")
        return updated
    
    async def count_by_incapacidad(self, incapacidad_id: UUID) -> int:
        """
        Cuenta documentos de una incapacidad.
        
        Args:
            incapacidad_id: ID de la incapacidad
            
        Returns:
            Número de documentos
        """
        return await self.repository.count_by_incapacidad(self.db, incapacidad_id)
    
    async def get_documento_contenido(self, documento_id: UUID) -> bytes:
        """
        Obtiene el contenido del documento desde el storage.
        
        Args:
            documento_id: ID del documento
            
        Returns:
            Contenido del archivo en bytes
            
        Raises:
            NotFoundException: Si el documento no existe
            FileException: Si hay error leyendo el archivo
        """
        documento = await self.get_documento(documento_id)
        
        try:
            # Obtener el contenido del archivo del storage
            contenido = self.storage.get_file_content(documento.ruta_storage)
            if contenido is None:
                raise FileException(f"No se pudo leer el contenido del archivo: {documento.ruta_storage}")
            logger.info(f"Contenido obtenido para documento: {documento_id}")
            return contenido
        except FileException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo contenido del documento {documento_id}: {e}")
            raise FileException(f"Error obteniendo contenido del documento: {str(e)}")
