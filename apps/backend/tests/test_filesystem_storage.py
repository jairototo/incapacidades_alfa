"""
Tests para FileSystemStorage.
"""
import os
import tempfile
from pathlib import Path
from datetime import datetime
import pytest
from io import BytesIO

from app.core.storage.filesystem import FileSystemStorage
from apps.backend.app.core.exceptions import StorageException


class TestFileSystemStorage:
    """Tests para el backend de FileSystem storage."""
    
    @pytest.fixture
    def temp_storage_path(self):
        """Crea directorio temporal para tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def storage(self, temp_storage_path):
        """Crea instancia de FileSystemStorage para tests."""
        return FileSystemStorage(base_path=temp_storage_path)
    
    def test_storage_initialization(self, temp_storage_path):
        """Test que el storage se inicializa correctamente."""
        storage = FileSystemStorage(base_path=temp_storage_path)
        assert storage.base_path == Path(temp_storage_path).resolve()
        assert storage.base_path.exists()
    
    def test_base_directory_creation(self):
        """Test que el directorio base se crea automáticamente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_path = os.path.join(tmpdir, "nested", "storage")
            storage = FileSystemStorage(base_path=non_existent_path)
            assert storage.base_path.exists()
            assert storage.base_path.is_dir()
    
    def test_upload_file_success(self, storage, temp_storage_path):
        """Test que un archivo se sube correctamente."""
        file_content = b"Test file content"
        file_data = BytesIO(file_content)
        
        ruta, md5, sha256, size = storage.upload_file(
            file_data=file_data,
            file_name="test.pdf",
            content_type="application/pdf",
            folder="documentos"
        )
        
        # Verificar que se retorna información correcta
        assert ruta.startswith("documentos/")
        assert ruta.endswith(".pdf")
        assert len(md5) == 32  # MD5 hash length
        assert len(sha256) == 64  # SHA256 hash length
        assert size == len(file_content)
        
        # Verificar que el archivo existe en el filesystem
        full_path = storage.base_path / ruta
        assert full_path.exists()
        assert full_path.read_bytes() == file_content
    
    def test_upload_file_creates_year_month_structure(self, storage):
        """Test que la estructura año/mes se crea correctamente."""
        file_data = BytesIO(b"Content")
        
        ruta, _, _, _ = storage.upload_file(
            file_data=file_data,
            file_name="test.jpg",
            content_type="image/jpeg",
            folder="documentos"
        )
        
        # Verificar estructura: documentos/{year}/{month}/filename.ext
        parts = ruta.split('/')
        assert len(parts) >= 3
        assert parts[0] == "documentos"
        
        # Verificar que año y mes son válidos
        year = parts[1]
        month = parts[2]
        assert len(year) == 4 and year.isdigit()
        assert len(month) == 2 and month.isdigit()
        assert 1 <= int(month) <= 12
    
    def test_upload_file_sanitizes_filename(self, storage):
        """Test que nombres de archivo peligrosos se sanitizan."""
        dangerous_filename = "../../../etc/passwd"
        file_data = BytesIO(b"Content")
        
        ruta, _, _, _ = storage.upload_file(
            file_data=file_data,
            file_name=dangerous_filename,
            content_type="application/pdf",
            folder="documentos"
        )
        
        # Verificar que no contiene caracteres peligrosos
        assert ".." not in ruta
        assert ruta.startswith("documentos/")
    
    def test_upload_file_permissions_644(self, storage):
        """Test que los archivos se crean con permisos 644."""
        file_data = BytesIO(b"Content")
        
        ruta, _, _, _ = storage.upload_file(
            file_data=file_data,
            file_name="test.pdf",
            content_type="application/pdf",
            folder="documentos"
        )
        
        full_path = storage.base_path / ruta
        file_mode = oct(full_path.stat().st_mode)[-3:]
        assert file_mode == "644"
    
    def test_file_exists_true(self, storage):
        """Test que file_exists retorna True para archivos existentes."""
        file_data = BytesIO(b"Content")
        
        ruta, _, _, _ = storage.upload_file(
            file_data=file_data,
            file_name="test.pdf",
            content_type="application/pdf",
            folder="documentos"
        )
        
        assert storage.file_exists(ruta) is True
    
    def test_file_exists_false(self, storage):
        """Test que file_exists retorna False para archivos inexistentes."""
        assert storage.file_exists("documentos/nonexistent.pdf") is False
    
    def test_get_file_info_success(self, storage):
        """Test que get_file_info retorna información correcta."""
        file_content = b"Test content"
        file_data = BytesIO(file_content)
        
        ruta, _, _, _ = storage.upload_file(
            file_data=file_data,
            file_name="test.pdf",
            content_type="application/pdf",
            folder="documentos"
        )
        
        info = storage.get_file_info(ruta)
        assert info is not None
        assert info["size"] == len(file_content)
        assert "content_type" in info
        assert "last_modified" in info
        assert isinstance(info["last_modified"], datetime)
    
    def test_get_file_info_nonexistent(self, storage):
        """Test que get_file_info retorna None para archivos inexistentes."""
        info = storage.get_file_info("documentos/nonexistent.pdf")
        assert info is None
    
    def test_get_presigned_url_format(self, storage):
        """Test que get_presigned_url genera URL correcta."""
        file_data = BytesIO(b"Content")
        
        ruta, _, _, _ = storage.upload_file(
            file_data=file_data,
            file_name="test.pdf",
            content_type="application/pdf",
            folder="documentos"
        )
        
        url = storage.get_presigned_url(ruta)
        assert url.startswith("/api/v1/storage/files/")
        assert ruta in url
    
    def test_get_presigned_url_nonexistent_file_raises(self, storage):
        """Test que get_presigned_url falla para archivos inexistentes."""
        with pytest.raises(StorageException):
            storage.get_presigned_url("documentos/nonexistent.pdf")
    
    def test_delete_file_success(self, storage):
        """Test que un archivo se elimina correctamente."""
        file_data = BytesIO(b"Content to delete")
        
        ruta, _, _, _ = storage.upload_file(
            file_data=file_data,
            file_name="test.pdf",
            content_type="application/pdf",
            folder="documentos"
        )
        
        # Verificar que existe
        assert storage.file_exists(ruta) is True
        
        # Eliminar
        storage.delete_file(ruta)
        
        # Verificar que ya no existe
        assert storage.file_exists(ruta) is False
    
    def test_delete_nonexistent_file_no_error(self, storage):
        """Test que eliminar archivo inexistente no lanza error."""
        # No debe lanzar excepción
        storage.delete_file("documentos/nonexistent.pdf")
    
    def test_delete_file_path_traversal_blocked(self, storage, temp_storage_path):
        """Test que path traversal en delete está bloqueado."""
        # Crear archivo fuera del directorio permitido
        external_file = Path(temp_storage_path).parent / "external.txt"
        external_file.write_text("Should not be deletable")
        
        # Intentar eliminar usando path traversal
        with pytest.raises(StorageException, match="fuera del directorio permitido"):
            storage.delete_file("../../external.txt")
        
        # Verificar que el archivo externo sigue existiendo
        assert external_file.exists()
        external_file.unlink()  # Limpiar
    
    def test_get_file_content_success(self, storage):
        """Test que get_file_content retorna el contenido correcto."""
        file_content = b"Test file content for reading"
        file_data = BytesIO(file_content)
        
        ruta, _, _, _ = storage.upload_file(
            file_data=file_data,
            file_name="test.pdf",
            content_type="application/pdf",
            folder="documentos"
        )
        
        content = storage.get_file_content(ruta)
        assert content == file_content
    
    def test_get_file_content_nonexistent(self, storage):
        """Test que get_file_content retorna None para archivos inexistentes."""
        content = storage.get_file_content("documentos/nonexistent.pdf")
        assert content is None
    
    def test_get_file_content_path_traversal_blocked(self, storage, temp_storage_path):
        """Test que path traversal en get_file_content está bloqueado."""
        # Crear archivo fuera del directorio permitido
        external_file = Path(temp_storage_path).parent / "secret.txt"
        external_file.write_text("Secret content")
        
        # Intentar leer usando path traversal
        with pytest.raises(StorageException, match="fuera del directorio permitido"):
            storage.get_file_content("../../secret.txt")
        
        external_file.unlink()  # Limpiar
    
    def test_upload_different_folders(self, storage):
        """Test que archivos se pueden subir a diferentes carpetas."""
        file_data1 = BytesIO(b"Content 1")
        file_data2 = BytesIO(b"Content 2")
        
        ruta1, _, _, _ = storage.upload_file(
            file_data=file_data1,
            file_name="file1.pdf",
            content_type="application/pdf",
            folder="documentos/incapacidades"
        )
        
        ruta2, _, _, _ = storage.upload_file(
            file_data=file_data2,
            file_name="file2.pdf",
            content_type="application/pdf",
            folder="documentos/siniestros"
        )
        
        assert ruta1.startswith("documentos/incapacidades/")
        assert ruta2.startswith("documentos/siniestros/")
        assert storage.file_exists(ruta1)
        assert storage.file_exists(ruta2)
    
    def test_hash_consistency(self, storage):
        """Test que los hashes son consistentes para el mismo contenido."""
        file_content = b"Same content for hashing"
        
        file_data1 = BytesIO(file_content)
        _, md5_1, sha256_1, _ = storage.upload_file(
            file_data=file_data1,
            file_name="file1.pdf",
            content_type="application/pdf",
            folder="test"
        )
        
        file_data2 = BytesIO(file_content)
        _, md5_2, sha256_2, _ = storage.upload_file(
            file_data=file_data2,
            file_name="file2.pdf",
            content_type="application/pdf",
            folder="test"
        )
        
        # Los hashes deben ser idénticos para el mismo contenido
        assert md5_1 == md5_2
        assert sha256_1 == sha256_2
