"""
Tests para endpoints de storage (servir archivos).
"""
import os
import tempfile
from pathlib import Path
from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from apps.backend.app.main import app
from app.core.storage.filesystem import FileSystemStorage


class TestStorageEndpoint:
    """Tests para el endpoint de servir archivos."""
    
    @pytest.fixture
    def temp_storage_path(self):
        """Crea directorio temporal para tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def client(self):
        """Cliente de prueba."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, client):
        """Headers de autenticación para tests."""
        # Crear usuario y hacer login
        # (Asume que ya tienes fixtures de autenticación en conftest.py)
        # Por ahora, mock simple
        return {"Authorization": "Bearer fake-token-for-testing"}
    
    def test_serve_file_only_in_filesystem_mode(self, client, auth_headers):
        """Test que el endpoint solo funciona en modo filesystem."""
        with patch("app.core.config.settings.STORAGE_BACKEND", "minio"):
            response = client.get(
                "/api/v1/storage/files/documentos/2026/01/test.pdf",
                headers=auth_headers
            )
            assert response.status_code == 403
            assert "solo disponible en modo filesystem" in response.json()["detail"]
    
    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_not_found(self, client, auth_headers, temp_storage_path):
        """Test que retorna 404 si el archivo no existe."""
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client.get(
                "/api/v1/storage/files/documentos/2026/01/nonexistent.pdf",
                headers=auth_headers
            )
            assert response.status_code == 404
            assert "no encontrado" in response.json()["detail"].lower()
    
    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_success(self, client, auth_headers, temp_storage_path):
        """Test que un archivo se sirve correctamente."""
        # Crear archivo de prueba
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "test.pdf"
        test_content = b"PDF content here"
        test_file.write_bytes(test_content)
        
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client.get(
                "/api/v1/storage/files/documentos/2026/01/test.pdf",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.content == test_content
            assert response.headers["content-type"] == "application/pdf"
    
    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_path_traversal_blocked(self, client, auth_headers, temp_storage_path):
        """Test que path traversal está bloqueado."""
        # Crear archivo fuera del directorio permitido
        external_dir = Path(temp_storage_path).parent
        external_file = external_dir / "secret.txt"
        external_file.write_text("Secret content")
        
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            # Intentar acceder con path traversal
            response = client.get(
                "/api/v1/storage/files/../../secret.txt",
                headers=auth_headers
            )
            
            assert response.status_code == 403
            assert "denegado" in response.json()["detail"].lower()
        
        external_file.unlink()  # Limpiar
    
    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_correct_mime_type_jpg(self, client, auth_headers, temp_storage_path):
        """Test que el MIME type es correcto para JPG."""
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "image.jpg"
        test_file.write_bytes(b"JPEG content")
        
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client.get(
                "/api/v1/storage/files/documentos/2026/01/image.jpg",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"
    
    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_correct_mime_type_png(self, client, auth_headers, temp_storage_path):
        """Test que el MIME type es correcto para PNG."""
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "image.png"
        test_file.write_bytes(b"PNG content")
        
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client.get(
                "/api/v1/storage/files/documentos/2026/01/image.png",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
    
    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_has_cache_headers(self, client, auth_headers, temp_storage_path):
        """Test que la respuesta incluye headers de cache."""
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "test.pdf"
        test_file.write_bytes(b"Content")
        
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client.get(
                "/api/v1/storage/files/documentos/2026/01/test.pdf",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert "cache-control" in response.headers
            assert "max-age" in response.headers["cache-control"]
    
    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_head_request_check_file_exists(self, client, auth_headers, temp_storage_path):
        """Test que HEAD request verifica existencia sin descargar."""
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "test.pdf"
        test_content = b"A" * 1000  # 1KB
        test_file.write_bytes(test_content)
        
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client.head(
                "/api/v1/storage/files/documentos/2026/01/test.pdf",
                headers=auth_headers
            )
            
            # HEAD request no debe retornar contenido
            assert response.status_code == 200
            # El contenido debe estar vacío
            assert len(response.content) == 0 or response.json()["exists"] is True
    
    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_head_request_file_not_found(self, client, auth_headers, temp_storage_path):
        """Test que HEAD request retorna 404 si archivo no existe."""
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client.head(
                "/api/v1/storage/files/documentos/2026/01/nonexistent.pdf",
                headers=auth_headers
            )
            
            assert response.status_code == 404
    
    def test_serve_file_requires_authentication(self, client, temp_storage_path):
        """Test que el endpoint requiere autenticación."""
        with patch("app.core.config.settings.STORAGE_BACKEND", "filesystem"):
            with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
                # Petición sin headers de autenticación
                response = client.get(
                    "/api/v1/storage/files/documentos/2026/01/test.pdf"
                )
                
                # Debe retornar 401 Unauthorized
                assert response.status_code == 401
    
    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_nested_folders(self, client, auth_headers, temp_storage_path):
        """Test que archivos en carpetas anidadas se sirven correctamente."""
        file_path = Path(temp_storage_path) / "documentos" / "incapacidades" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "nested.pdf"
        test_content = b"Nested file content"
        test_file.write_bytes(test_content)
        
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client.get(
                "/api/v1/storage/files/documentos/incapacidades/2026/01/nested.pdf",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.content == test_content
