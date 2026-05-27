"""
Tests de integración para endpoints de Documentos.
"""
import io
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.models.documento import Documento
from apps.backend.app.models.usuario import Usuario


class TestDocumentosEndpoints:
    """Tests de integración para endpoints de documentos."""
    
    @pytest.mark.asyncio
    async def test_upload_documento(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_incapacidad,
        test_usuario: Usuario
    ):
        """Test de upload de documento."""
        # Crear archivo de prueba
        file_content = b"PDF file content here"
        files = {
            "file": ("test.pdf", io.BytesIO(file_content), "application/pdf")
        }
        data = {
            "incapacidad_id": str(test_incapacidad.id),
            "tipo_documento": "INCAPACIDAD_MEDICA"
        }
        
        # TODO: Agregar autenticación cuando esté implementada
        # response = await client.post(
        #     "/api/v1/documentos/upload",
        #     files=files,
        #     data=data,
        #     headers={"Authorization": f"Bearer {token}"}
        # )
        
        # assert response.status_code == 201
        # data = response.json()
        # assert "documento" in data
        # assert data["documento"]["nombre_original"] == "test.pdf"
        # assert data["documento"]["mime_type"] == "application/pdf"
        # assert "url_descarga" in data
    
    @pytest.mark.asyncio
    async def test_upload_documento_invalid_extension(
        self,
        client: AsyncClient,
        test_incapacidad,
        test_usuario: Usuario
    ):
        """Test de upload con extensión inválida."""
        file_content = b"Executable content"
        files = {
            "file": ("malware.exe", io.BytesIO(file_content), "application/octet-stream")
        }
        data = {
            "incapacidad_id": str(test_incapacidad.id),
            "tipo_documento": "INCAPACIDAD_MEDICA"
        }
        
        # TODO: Agregar autenticación
        # response = await client.post("/api/v1/documentos/upload", files=files, data=data)
        # assert response.status_code == 422
        # assert "Extensión de archivo no permitida" in response.text
    
    @pytest.mark.asyncio
    async def test_get_documento(
        self,
        client: AsyncClient,
        test_documento: Documento,
        test_usuario: Usuario
    ):
        """Test de obtener documento por ID."""
        # TODO: Agregar autenticación
        # response = await client.get(f"/api/v1/documentos/{test_documento.id}")
        # assert response.status_code == 200
        # data = response.json()
        # assert data["id"] == str(test_documento.id)
        # assert data["nombre_original"] == test_documento.nombre_original
    
    @pytest.mark.asyncio
    async def test_get_documento_not_found(
        self,
        client: AsyncClient,
        test_usuario: Usuario
    ):
        """Test de obtener documento que no existe."""
        from uuid import uuid4
        
        # TODO: Agregar autenticación
        # response = await client.get(f"/api/v1/documentos/{uuid4()}")
        # assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_download_documento(
        self,
        client: AsyncClient,
        test_documento: Documento,
        test_usuario: Usuario
    ):
        """Test de descarga de documento."""
        # TODO: Agregar autenticación
        # response = await client.get(f"/api/v1/documentos/{test_documento.id}/download")
        # assert response.status_code == 200
        # data = response.json()
        # assert "url" in data
        # assert "expires_in" in data
        # assert "nombre_archivo" in data
        # assert data["nombre_archivo"] == test_documento.nombre_original
    
    @pytest.mark.asyncio
    async def test_delete_documento(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_documento: Documento,
        test_usuario: Usuario
    ):
        """Test de eliminación de documento."""
        documento_id = test_documento.id
        
        # TODO: Agregar autenticación
        # response = await client.delete(f"/api/v1/documentos/{documento_id}")
        # assert response.status_code == 204
        
        # # Verificar que el documento fue eliminado
        # from sqlalchemy import select
        # result = await db_session.execute(
        #     select(Documento).where(Documento.id == documento_id)
        # )
        # documento = result.scalar_one_or_none()
        # assert documento is None
    
    @pytest.mark.asyncio
    async def test_list_documentos_incapacidad(
        self,
        client: AsyncClient,
        test_incapacidad,
        test_documento: Documento,
        test_usuario: Usuario
    ):
        """Test de listar documentos de una incapacidad."""
        # TODO: Agregar autenticación
        # response = await client.get(
        #     f"/api/v1/documentos/incapacidad/{test_incapacidad.id}/documentos"
        # )
        # assert response.status_code == 200
        # data = response.json()
        # assert isinstance(data, list)
        # assert len(data) >= 1
        # assert any(d["id"] == str(test_documento.id) for d in data)
    
    @pytest.mark.asyncio
    async def test_list_documentos_incapacidad_pagination(
        self,
        client: AsyncClient,
        test_incapacidad,
        test_usuario: Usuario
    ):
        """Test de paginación al listar documentos."""
        # TODO: Agregar autenticación
        # response = await client.get(
        #     f"/api/v1/documentos/incapacidad/{test_incapacidad.id}/documentos",
        #     params={"skip": 0, "limit": 10}
        # )
        # assert response.status_code == 200
        # data = response.json()
        # assert isinstance(data, list)
        # assert len(data) <= 10


@pytest.mark.asyncio
async def test_upload_multiple_documentos(
    client: AsyncClient,
    db_session: AsyncSession,
    test_incapacidad,
    test_usuario: Usuario
):
    """Test de subir múltiples documentos a una incapacidad."""
    # TODO: Implementar cuando se tenga autenticación
    pass


@pytest.mark.asyncio
async def test_documento_permissions(
    client: AsyncClient,
    test_documento: Documento
):
    """Test de validación de permisos para documentos."""
    # TODO: Implementar tests de permisos cuando se tenga RBAC completo
    pass
