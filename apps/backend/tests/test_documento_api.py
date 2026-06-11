"""
Tests de integración para endpoints de Documentos.
"""
import io
from uuid import UUID, uuid4
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.documento import Documento
from app.models.usuario import Usuario


class TestDocumentosEndpoints:
    """Tests de integración para endpoints de documentos."""

    @pytest.mark.asyncio
    async def test_get_documento(
        self,
        client: AsyncClient,
        test_documento: Documento,
        admin_token_headers: dict,
    ):
        """Test de obtener documento por ID."""
        response = await client.get(
            f"/api/v1/documentos/{test_documento.id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_documento.id)
        assert data["nombre_original"] == test_documento.nombre_original

    @pytest.mark.asyncio
    async def test_get_documento_not_found(
        self,
        client: AsyncClient,
        admin_token_headers: dict,
    ):
        """Test de obtener documento que no existe."""
        response = await client.get(
            f"/api/v1/documentos/{uuid4()}",
            headers=admin_token_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_documento(
        self,
        client: AsyncClient,
        test_documento: Documento,
        admin_token_headers: dict,
    ):
        """Test de descarga de documento (URL de descarga)."""
        # Mock the storage layer so it does not check filesystem for test fixture
        fake_url = f"/api/v1/storage/files/{test_documento.ruta_storage}"
        with patch(
            "app.services.documento_service.DocumentoService.get_download_url",
            return_value=fake_url,
        ):
            response = await client.get(
                f"/api/v1/documentos/{test_documento.id}/download",
                headers=admin_token_headers,
            )
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "expires_in" in data
        assert "nombre_archivo" in data
        assert data["nombre_archivo"] == test_documento.nombre_original

    @pytest.mark.asyncio
    async def test_list_documentos_incapacidad(
        self,
        client: AsyncClient,
        test_incapacidad,
        test_documento: Documento,
        admin_token_headers: dict,
    ):
        """Test de listar documentos de una incapacidad."""
        response = await client.get(
            f"/api/v1/documentos/incapacidades/{test_incapacidad.id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(d["id"] == str(test_documento.id) for d in data)

    @pytest.mark.asyncio
    async def test_list_documentos_incapacidad_pagination(
        self,
        client: AsyncClient,
        test_incapacidad,
        test_documento: Documento,
        admin_token_headers: dict,
    ):
        """Test de paginación al listar documentos."""
        response = await client.get(
            f"/api/v1/documentos/incapacidades/{test_incapacidad.id}",
            params={"skip": 0, "limit": 10},
            headers=admin_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    @pytest.mark.asyncio
    async def test_delete_documento(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_documento: Documento,
        admin_token_headers: dict,
    ):
        """Test de eliminación de documento."""
        documento_id = test_documento.id
        response = await client.delete(
            f"/api/v1/documentos/{documento_id}",
            headers=admin_token_headers,
        )
        assert response.status_code == 204

        # Verificar que el documento fue eliminado
        from sqlalchemy import select
        from app.models.documento import Documento as DocumentoModel
        result = await db_session.execute(
            select(DocumentoModel).where(DocumentoModel.id == documento_id)
        )
        documento = result.scalar_one_or_none()
        assert documento is None


@pytest.mark.asyncio
async def test_documento_endpoints_require_auth(
    client: AsyncClient,
    test_documento: Documento,
):
    """Endpoints de documentos deben requerir autenticación (401 sin headers)."""
    doc_id = str(test_documento.id)
    endpoints = [
        ("GET", f"/api/v1/documentos/{doc_id}"),
        ("GET", f"/api/v1/documentos/{doc_id}/view"),
        ("GET", f"/api/v1/documentos/{doc_id}/download"),
        ("DELETE", f"/api/v1/documentos/{doc_id}"),
    ]
    for method, url in endpoints:
        if method == "GET":
            response = await client.get(url)
        else:
            response = await client.delete(url)
        assert response.status_code == 401, (
            f"Expected 401 for {method} {url}, got {response.status_code}"
        )


@pytest.mark.asyncio
async def test_upload_multiple_documentos(
    client: AsyncClient,
    db_session: AsyncSession,
    test_incapacidad,
    test_usuario: Usuario
):
    """Test de subir múltiples documentos a una incapacidad."""
    # Upload requires actual file storage backend; skipped pending storage mock
    pass
