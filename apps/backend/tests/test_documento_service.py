"""
Tests unitarios para DocumentoService.
"""
import hashlib
import io
from datetime import timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.core.exceptions import (
    ValidationException,
    NotFoundException,
    FileException
)
from apps.backend.app.models.documento import Documento
from apps.backend.app.services.documento_service import DocumentoService


@pytest.fixture
def mock_storage():
    """Mock del storage backend."""
    storage = Mock()
    storage.upload_file = Mock(return_value=(
        "documentos/test-uuid.pdf",
        "5d41402abc4b2a76b9719d911017c592",
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
        245680
    ))
    storage.get_presigned_url = Mock(return_value="/api/v1/storage/files/documentos/test-uuid.pdf")
    storage.delete_file = Mock()
    storage.file_exists = Mock(return_value=True)
    return storage


@pytest.fixture
def sample_file_data():
    """Datos de archivo de ejemplo."""
    content = b"PDF file content here"
    return io.BytesIO(content)


class TestDocumentoService:
    """Tests para DocumentoService."""
    
    @pytest.mark.asyncio
    async def test_upload_documento_success(
        self,
        db_session: AsyncSession,
        mock_storage,
        sample_file_data,
        test_incapacidad,
        test_usuario
    ):
        """Test de upload exitoso de documento."""
        # Patch el storage_backend global
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            documento = await service.upload_documento(
                incapacidad_id=test_incapacidad.id,
                file_data=sample_file_data,
                filename="test.pdf",
                content_type="application/pdf",
                tipo_documento="INCAPACIDAD_MEDICA",
                uploaded_by_id=test_usuario.id
            )
            
            assert documento is not None
            assert documento.nombre_original == "test.pdf"
            assert documento.mime_type == "application/pdf"
            assert documento.incapacidad_id == test_incapacidad.id
            assert documento.uploaded_by_id == test_usuario.id
            
            # Verificar que se llamó al storage
            mock_storage.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_documento_invalid_extension(
        self,
        db_session: AsyncSession,
        mock_storage,
        sample_file_data
    ):
        """Test de upload con extensión inválida."""
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            with pytest.raises(ValidationException) as exc_info:
                await service.upload_documento(
                    incapacidad_id=uuid4(),
                    file_data=sample_file_data,
                    filename="test.exe",
                    content_type="application/octet-stream",
                    tipo_documento="INCAPACIDAD_MEDICA",
                    uploaded_by_id=uuid4()
                )
            
            assert "Extensión de archivo no permitida" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_upload_documento_invalid_mime_type(
        self,
        db_session: AsyncSession,
        mock_storage,
        sample_file_data
    ):
        """Test de upload con tipo MIME inválido."""
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            with pytest.raises(ValidationException) as exc_info:
                await service.upload_documento(
                    incapacidad_id=uuid4(),
                    file_data=sample_file_data,
                    filename="test.pdf",
                    content_type="application/x-executable",
                    tipo_documento="INCAPACIDAD_MEDICA",
                    uploaded_by_id=uuid4()
                )
            
            assert "Tipo de archivo no permitido" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_upload_documento_file_too_large(
        self,
        db_session: AsyncSession,
        mock_storage
    ):
        """Test de upload con archivo demasiado grande."""
        # Mock de storage que retorna archivo muy grande
        mock_storage.upload_file = Mock(return_value=(
            "documentos/test-uuid.pdf",
            "hash_md5",
            "hash_sha256",
            15 * 1024 * 1024  # 15MB (límite es 10MB)
        ))
        
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            file_data = io.BytesIO(b"content")
            
            with pytest.raises(ValidationException) as exc_info:
                await service.upload_documento(
                    incapacidad_id=uuid4(),
                    file_data=file_data,
                    filename="test.pdf",
                    content_type="application/pdf",
                    tipo_documento="INCAPACIDAD_MEDICA",
                    uploaded_by_id=uuid4()
                )
            
            assert "demasiado grande" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_get_documento_success(
        self,
        db_session: AsyncSession,
        mock_storage,
        test_documento: Documento
    ):
        """Test de obtener documento por ID."""
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            documento = await service.get_documento(test_documento.id)
            
            assert documento is not None
            assert documento.id == test_documento.id
            assert documento.nombre_original == test_documento.nombre_original
    
    @pytest.mark.asyncio
    async def test_get_documento_not_found(
        self,
        db_session: AsyncSession,
        mock_storage
    ):
        """Test de obtener documento que no existe."""
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            with pytest.raises(NotFoundException):
                await service.get_documento(uuid4())
    
    @pytest.mark.asyncio
    async def test_get_download_url(
        self,
        db_session: AsyncSession,
        mock_storage,
        test_documento: Documento
    ):
        """Test de generación de URL de descarga."""
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            url = await service.get_download_url(test_documento.id, expires_hours=2)
            
            assert url == "/api/v1/storage/files/documentos/test-uuid.pdf"
            mock_storage.get_presigned_url.assert_called_once()
            
            # Verificar que se pasó el timedelta correcto
            call_args = mock_storage.get_presigned_url.call_args
            assert call_args[1]['expires'] == timedelta(hours=2)
    
    @pytest.mark.asyncio
    async def test_delete_documento_soft(
        self,
        db_session: AsyncSession,
        mock_storage,
        test_documento: Documento
    ):
        """Test de eliminación suave de documento."""
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            await service.delete_documento(test_documento.id, hard_delete=False)
            
            # Verificar que NO se llamó a delete_file del storage
            mock_storage.delete_file.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_documento_hard(
        self,
        db_session: AsyncSession,
        mock_storage,
        test_documento: Documento
    ):
        """Test de eliminación física de documento."""
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            await service.delete_documento(test_documento.id, hard_delete=True)
            
            # Verificar que SÍ se llamó a delete_file del storage
            mock_storage.delete_file.assert_called_once_with(test_documento.ruta_storage)
    
    @pytest.mark.asyncio
    async def test_list_by_incapacidad(
        self,
        db_session: AsyncSession,
        mock_storage,
        test_incapacidad,
        test_documento: Documento
    ):
        """Test de listar documentos por incapacidad."""
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
            
            documentos = await service.list_by_incapacidad(
                incapacidad_id=test_incapacidad.id
            )
            
            assert len(documentos) >= 1
            assert any(d.id == test_documento.id for d in documentos)
    
    @pytest.mark.asyncio
    async def test_count_by_incapacidad(
        self,
        db_session: AsyncSession,
        mock_storage,
        test_incapacidad
    ):
        """Test de contar documentos por incapacidad."""
        with patch("app.services.documento_service.storage_backend", mock_storage):
            service = DocumentoService(db_session)
        
        count = await service.count_by_incapacidad(test_incapacidad.id)
        
        assert isinstance(count, int)
        assert count >= 0
