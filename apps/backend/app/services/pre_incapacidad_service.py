"""
Servicio para PreIncapacidad y PreDocumento.
Gestiona la radicación pública desde el portal externo.
"""
import os
from typing import BinaryIO, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException, ValidationException
from app.core.storage_core import storage_backend
from app.db.repositories.pre_incapacidad_repository import (
    PreDocumentoRepository,
    PreIncapacidadRepository,
)
from app.models.pre_documento import PreDocumento
from app.models.pre_incapacidad import PreIncapacidad
from app.schemas.pre_incapacidad import PreIncapacidadCreate

# Tipos MIME permitidos para pre-documentos
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # bytes

TIPOS_DOCUMENTO_VALIDOS = {"INCAPACIDAD_MEDICA", "HISTORIA_CLINICA", "SOPORTE_ADICIONAL"}


class PreIncapacidadService:
    """Servicio de radicación pública — sin acceso a tablas de empleados/empresas."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PreIncapacidadRepository()
        self.doc_repo = PreDocumentoRepository()
        self.storage = storage_backend

    async def radicar(self, data: PreIncapacidadCreate) -> PreIncapacidad:
        """
        Crea una pre-incapacidad con los datos planos del portal externo.
        No valida existencia en BD de empresa ni empleado.

        Returns:
            PreIncapacidad creada con número de radicación secuencial.
        """
        inc = data.incapacidad
        dias = (inc.fecha_fin - inc.fecha_inicio).days + 1

        obj = {
            "estado": "PENDIENTE",
            "tipo": "ARL",
            # Solicitante
            "solicitante_correo": str(data.solicitante.correo),
            "solicitante_nombres": data.solicitante.nombres,
            "solicitante_apellidos": data.solicitante.apellidos,
            "solicitante_telefono": data.solicitante.telefono,
            # Empresa (puede ser None si independiente)
            "empresa_nit": data.empresa.nit if data.empresa else None,
            "empresa_nombre": data.empresa.nombre if data.empresa else None,
            # Empleado
            "empleado_tipo_documento": data.empleado.tipo_documento,
            "empleado_numero_documento": data.empleado.numero_documento,
            "empleado_nombres": data.empleado.nombres,
            "empleado_apellidos": data.empleado.apellidos,
            "empleado_email": str(data.empleado.email) if data.empleado.email else None,
            "empleado_telefono": data.empleado.telefono,
            # Incapacidad
            "tipo_enfermedad": inc.tipo_enfermedad,
            "fecha_inicio": inc.fecha_inicio,
            "fecha_fin": inc.fecha_fin,
            "dias_totales": dias,
            "diagnostico_cie10": inc.diagnostico_cie10,
            "descripcion_diagnostico": inc.descripcion_diagnostico,
            "nombre_medico": inc.nombre_medico,
            "registro_medico": inc.registro_medico,
            "ips": inc.ips,
            "valor_dia": inc.valor_dia,
            "observaciones": inc.observaciones,
        }

        pre_inc = await self.repo.create_with_numero(self.db, obj)
        logger.info(
            f"PreIncapacidad creada: numero_radicacion={pre_inc.numero_radicacion} "
            f"empleado={data.empleado.numero_documento}"
        )
        return pre_inc

    async def get_by_id(self, pre_incapacidad_id: UUID) -> PreIncapacidad:
        """Obtiene una pre-incapacidad por ID. Lanza 404 si no existe."""
        obj = await self.repo.get_by_id_with_documentos(self.db, pre_incapacidad_id)
        if not obj:
            raise NotFoundException(f"Pre-incapacidad {pre_incapacidad_id} no encontrada")
        return obj

    async def subir_documento(
        self,
        pre_incapacidad_id: UUID,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        tipo_documento: str,
    ) -> PreDocumento:
        """
        Sube un documento asociado a una pre-incapacidad.
        Registra el documento en BD incluso si hubo errores parciales.

        Args:
            pre_incapacidad_id: ID de la pre-incapacidad
            file_data: Stream binario del archivo
            filename: Nombre original del archivo
            content_type: MIME type del archivo
            tipo_documento: INCAPACIDAD_MEDICA | HISTORIA_CLINICA | SOPORTE_ADICIONAL

        Returns:
            PreDocumento creado
        """
        # Validar que la pre-incapacidad existe
        pre_inc = await self.get_by_id(pre_incapacidad_id)

        # Validar tipo de documento
        if tipo_documento not in TIPOS_DOCUMENTO_VALIDOS:
            raise ValidationException(
                f"tipo_documento debe ser uno de: {', '.join(TIPOS_DOCUMENTO_VALIDOS)}"
            )

        # Validar extensión
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationException(
                f"Extensión no permitida. Permitidas: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Validar MIME
        if content_type not in ALLOWED_MIME_TYPES:
            raise ValidationException(
                f"Tipo de archivo no permitido: {content_type}"
            )

        estado_subida = "OK"
        error_subida: Optional[str] = None
        ruta_storage = ""
        bucket = settings.STORAGE_BUCKET
        tamanio_bytes = 0

        try:
            ruta_storage, _md5, _sha256, tamanio_bytes = self.storage.upload_file(
                file_data=file_data,
                file_name=filename,
                content_type=content_type,
                folder="pre-documentos",
            )

            if tamanio_bytes > MAX_FILE_SIZE:
                # Archivo ya subido pero demasiado grande — registrar error
                estado_subida = "ERROR"
                error_subida = f"Archivo supera el límite de {settings.MAX_UPLOAD_SIZE_MB}MB"
                logger.warning(
                    f"Archivo {filename} supera el límite ({tamanio_bytes} bytes)"
                )

        except Exception as exc:
            estado_subida = "ERROR"
            error_subida = str(exc)
            logger.error(
                f"Error subiendo pre-documento {filename} "
                f"para pre_incapacidad={pre_incapacidad_id}: {exc}"
            )
            # No re-lanzamos — el registro se crea con estado ERROR
            # para que el job pueda reintentarlo

        pre_doc_data = {
            "pre_incapacidad_id": pre_incapacidad_id,
            "tipo_documento": tipo_documento,
            "nombre_original": filename,
            "ruta_storage": ruta_storage,
            "bucket": bucket,
            "mime_type": content_type,
            "tamanio_bytes": tamanio_bytes,
            "estado_subida": estado_subida,
            "error_subida": error_subida,
        }

        pre_doc = await self.doc_repo.create(self.db, pre_doc_data)
        logger.info(
            f"PreDocumento registrado: {pre_doc.id} "
            f"[{tipo_documento}] estado={estado_subida}"
        )

        # If this pre-incapacidad was already promoted, link the new document to the
        # existing incapacidad too — avoids losing documents added after promotion.
        if estado_subida == "OK" and pre_inc.incapacidad_id:
            from app.models.documento import Documento
            from app.utils.enums import TipoDocumentoArchivo
            _TIPO_MAP = {
                "INCAPACIDAD_MEDICA": TipoDocumentoArchivo.INCAPACIDAD_MEDICA,
                "HISTORIA_CLINICA": TipoDocumentoArchivo.HISTORIA_CLINICA,
            }
            doc = Documento(
                incapacidad_id=pre_inc.incapacidad_id,
                tipo_documento=_TIPO_MAP.get(tipo_documento, TipoDocumentoArchivo.OTROS),
                nombre_archivo=pre_doc.nombre_original,
                nombre_original=pre_doc.nombre_original,
                ruta_storage=pre_doc.ruta_storage,
                bucket=pre_doc.bucket,
                mime_type=pre_doc.mime_type,
                tamanio_bytes=pre_doc.tamanio_bytes,
                uploaded_by_id=None,
                validado=False,
            )
            self.db.add(doc)
            await self.db.flush()
            logger.info(
                f"Documento también vinculado a incapacidad {pre_inc.incapacidad_id} "
                f"(pre-incapacidad {pre_incapacidad_id} ya promovida)"
            )

        return pre_doc
