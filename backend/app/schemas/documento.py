"""
Schemas de Pydantic para Documento.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentoBase(BaseModel):
    """Schema base para Documento."""
    tipo_documento: str = Field(..., description="Tipo de documento")
    nombre_original: str = Field(..., min_length=1, max_length=255, description="Nombre original del archivo")


class DocumentoCreate(DocumentoBase):
    """Schema para crear un documento (usado internamente)."""
    incapacidad_id: UUID = Field(..., description="ID de la incapacidad")
    nombre_archivo: str = Field(..., description="Nombre del archivo en storage")
    ruta_storage: str = Field(..., description="Ruta completa en storage")
    bucket: str = Field(..., description="Bucket de almacenamiento")
    mime_type: str = Field(..., description="Tipo MIME del archivo")
    tamanio_bytes: int = Field(..., ge=0, description="Tamaño en bytes")
    hash_md5: str = Field(..., description="Hash MD5 del archivo")
    hash_sha256: str = Field(..., description="Hash SHA256 del archivo")
    uploaded_by_id: UUID = Field(..., description="ID del usuario que subió el archivo")


class DocumentoUpdate(BaseModel):
    """Schema para actualizar un documento."""
    validado: Optional[bool] = Field(None, description="Si el documento ha sido validado")
    observacion_validacion: Optional[str] = Field(None, description="Observaciones de la validación")


class DocumentoResponse(DocumentoBase):
    """Schema para respuesta de documento."""
    id: UUID
    incapacidad_id: UUID
    nombre_archivo: str
    ruta_storage: str
    bucket: str
    mime_type: str
    tamanio_bytes: int
    hash_md5: str
    hash_sha256: str
    uploaded_by_id: UUID
    validado: bool
    observacion_validacion: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentoListItem(BaseModel):
    """Schema para item en listado de documentos."""
    id: UUID
    tipo_documento: str
    nombre_original: str
    mime_type: str
    tamanio_bytes: int
    validado: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentoUploadRequest(BaseModel):
    """Schema para solicitud de carga de documento."""
    tipo_documento: str = Field(..., description="Tipo de documento")


class DocumentoUploadResponse(BaseModel):
    """Schema para respuesta de carga exitosa."""
    documento: DocumentoResponse
    url_descarga: Optional[str] = Field(None, description="URL temporal para descargar")
