"""
Tests para endpoints de storage (servir archivos).
"""
import os
import tempfile
from pathlib import Path
from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.storage_core.filesystem import FileSystemStorage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_user():
    """Return a minimal mock Usuario for dependency override."""
    user = MagicMock()
    user.id = "00000000-0000-0000-0000-000000000001"
    user.is_active = True
    user.rol = "ADMIN"
    return user


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class TestStorageEndpoint:
    """Tests para el endpoint de servir archivos."""

    @pytest.fixture
    def temp_storage_path(self):
        """Crea directorio temporal para tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def client_with_auth(self):
        """Cliente con dependencia get_current_user resuelta."""
        from app.core.security import get_current_user

        async def _mock_user():
            return _make_mock_user()

        app.dependency_overrides[get_current_user] = _mock_user
        test_client = TestClient(app)
        yield test_client
        app.dependency_overrides.pop(get_current_user, None)

    @pytest.fixture
    def client_no_auth(self):
        """Cliente SIN override de autenticación (prueba 401)."""
        return TestClient(app, raise_server_exceptions=False)

    # -----------------------------------------------------------------------
    # Tests existentes — ahora usando client_with_auth
    # -----------------------------------------------------------------------

    def test_serve_file_only_in_filesystem_mode(self, client_with_auth):
        """Test que el endpoint solo funciona en modo filesystem."""
        with patch("app.core.config.settings.STORAGE_BACKEND", "minio"):
            response = client_with_auth.get(
                "/api/v1/storage/files/documentos/2026/01/test.pdf"
            )
            assert response.status_code == 403
            assert "solo disponible en modo filesystem" in response.json()["detail"]

    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_not_found(self, client_with_auth, temp_storage_path):
        """Test que retorna 404 si el archivo no existe."""
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client_with_auth.get(
                "/api/v1/storage/files/documentos/2026/01/nonexistent.pdf"
            )
            assert response.status_code == 404
            assert "no encontrado" in response.json()["detail"].lower()

    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_success(self, client_with_auth, temp_storage_path):
        """Test que un archivo se sirve correctamente."""
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "test.pdf"
        test_content = b"PDF content here"
        test_file.write_bytes(test_content)

        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client_with_auth.get(
                "/api/v1/storage/files/documentos/2026/01/test.pdf"
            )

            assert response.status_code == 200
            assert response.content == test_content
            assert response.headers["content-type"] == "application/pdf"

    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_path_traversal_blocked(self, client_with_auth, temp_storage_path):
        """Test que path traversal está bloqueado a nivel de aplicación.

        HTTP clients normalize URLs before sending (e.g. ../../foo -> /foo),
        so we test the application-level guard directly by using a symlink
        that points outside the base directory.
        """
        # Create a "secret" file outside the storage root
        external_dir = Path(temp_storage_path).parent
        secret_file = external_dir / "secret_outside.txt"
        secret_file.write_text("Secret content")

        # Create a symlink inside the storage root that points outside
        storage_root = Path(temp_storage_path)
        symlink = storage_root / "evil_link.txt"
        symlink.symlink_to(secret_file)

        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            # Accessing the symlink target directly — the endpoint must
            # resolve the real path and block it because it escapes base_path
            response = client_with_auth.get(
                "/api/v1/storage/files/evil_link.txt"
            )

            # Either 403 (path traversal blocked) or 404 is acceptable;
            # what matters is that the content is NOT served (not 200)
            assert response.status_code in (403, 404), (
                f"Expected 403 or 404, got {response.status_code}"
            )

        # Cleanup
        symlink.unlink(missing_ok=True)
        secret_file.unlink(missing_ok=True)

    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_correct_mime_type_jpg(self, client_with_auth, temp_storage_path):
        """Test que el MIME type es correcto para JPG."""
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "image.jpg"
        test_file.write_bytes(b"JPEG content")

        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client_with_auth.get(
                "/api/v1/storage/files/documentos/2026/01/image.jpg"
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"

    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_correct_mime_type_png(self, client_with_auth, temp_storage_path):
        """Test que el MIME type es correcto para PNG."""
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "image.png"
        test_file.write_bytes(b"PNG content")

        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client_with_auth.get(
                "/api/v1/storage/files/documentos/2026/01/image.png"
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"

    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_has_cache_headers(self, client_with_auth, temp_storage_path):
        """Test que la respuesta incluye headers de cache."""
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "test.pdf"
        test_file.write_bytes(b"Content")

        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client_with_auth.get(
                "/api/v1/storage/files/documentos/2026/01/test.pdf"
            )

            assert response.status_code == 200
            assert "cache-control" in response.headers
            assert "max-age" in response.headers["cache-control"]

    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_head_request_check_file_exists(self, client_with_auth, temp_storage_path):
        """Test que HEAD request verifica existencia sin descargar."""
        file_path = Path(temp_storage_path) / "documentos" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "test.pdf"
        test_content = b"A" * 1000
        test_file.write_bytes(test_content)

        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client_with_auth.head(
                "/api/v1/storage/files/documentos/2026/01/test.pdf"
            )

            assert response.status_code == 200
            assert len(response.content) == 0

    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_head_request_file_not_found(self, client_with_auth, temp_storage_path):
        """Test que HEAD request retorna 404 si archivo no existe."""
        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client_with_auth.head(
                "/api/v1/storage/files/documentos/2026/01/nonexistent.pdf"
            )

            assert response.status_code == 404

    def test_serve_file_requires_authentication(self, client_no_auth, temp_storage_path):
        """Test que el endpoint requiere autenticación (401 sin token)."""
        with patch("app.core.config.settings.STORAGE_BACKEND", "filesystem"):
            with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
                response = client_no_auth.get(
                    "/api/v1/storage/files/documentos/2026/01/test.pdf"
                )

                assert response.status_code == 401

    @patch("app.core.config.settings.STORAGE_BACKEND", "filesystem")
    def test_serve_file_nested_folders(self, client_with_auth, temp_storage_path):
        """Test que archivos en carpetas anidadas se sirven correctamente."""
        file_path = Path(temp_storage_path) / "documentos" / "incapacidades" / "2026" / "01"
        file_path.mkdir(parents=True, exist_ok=True)
        test_file = file_path / "nested.pdf"
        test_content = b"Nested file content"
        test_file.write_bytes(test_content)

        with patch("app.core.config.settings.FILESYSTEM_BASE_PATH", temp_storage_path):
            response = client_with_auth.get(
                "/api/v1/storage/files/documentos/incapacidades/2026/01/nested.pdf"
            )

            assert response.status_code == 200
            assert response.content == test_content
