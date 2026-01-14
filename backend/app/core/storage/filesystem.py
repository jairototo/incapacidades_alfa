"""
Implementación de almacenamiento en filesystem local.
"""
import hashlib
import io
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Optional, Tuple
from uuid import uuid4

from loguru import logger

from app.core.storage.base import StorageBackend
from app.core.exceptions import StorageException


class FileSystemStorage(StorageBackend):
    """
    Backend de almacenamiento en filesystem local.
    
    Organiza archivos en estructura de carpetas por año/mes:
    {base_path}/{folder}/{year}/{month}/{uuid}.{extension}
    
    Ejemplo:
        storage/documentos/incapacidades/2026/01/abc123-def456.pdf
    """
    
    def __init__(self, base_path: str = "/app/storage"):
        """
        Inicializa el backend de filesystem.
        
        Args:
            base_path: Ruta base donde se almacenarán los archivos
        """
        self.base_path = Path(base_path).resolve()
        self._ensure_base_directory()
        logger.info(f"FileSystemStorage inicializado en: {self.base_path}")
    
    def _ensure_base_directory(self) -> None:
        """Crea el directorio base si no existe."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True, mode=0o755)
            logger.debug(f"Directorio base verificado: {self.base_path}")
        except Exception as e:
            logger.error(f"Error creando directorio base: {e}")
            raise StorageException(f"Error configurando filesystem storage: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitiza nombre de archivo para evitar path traversal.
        
        Args:
            filename: Nombre del archivo a sanitizar
            
        Returns:
            Nombre de archivo seguro
        """
        # Eliminar caracteres peligrosos
        dangerous_chars = ['/', '\\', '..', '~', '$', '&', '|', ';', '<', '>', '`']
        safe_name = filename
        for char in dangerous_chars:
            safe_name = safe_name.replace(char, '_')
        return safe_name
    
    def _get_storage_path(self, folder: str, filename: str) -> Path:
        """
        Genera ruta de almacenamiento organizada por año/mes.
        
        Args:
            folder: Carpeta base (ej: "documentos/incapacidades")
            filename: Nombre del archivo
            
        Returns:
            Path completo donde se guardará el archivo
        """
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        # Construir path: base_path/folder/year/month/filename
        storage_dir = self.base_path / folder / year / month
        storage_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
        
        return storage_dir / filename
    
    def _get_relative_path(self, full_path: Path) -> str:
        """
        Obtiene ruta relativa desde base_path.
        
        Args:
            full_path: Ruta completa del archivo
            
        Returns:
            Ruta relativa (ej: "documentos/incapacidades/2026/01/file.pdf")
        """
        return str(full_path.relative_to(self.base_path))
    
    def upload_file(
        self,
        file_data: BinaryIO,
        file_name: str,
        content_type: str,
        folder: str = "documentos"
    ) -> Tuple[str, str, str, int]:
        """
        Sube un archivo al filesystem.
        
        Args:
            file_data: Datos del archivo (stream binario)
            file_name: Nombre original del archivo
            content_type: Tipo MIME del archivo
            folder: Carpeta dentro del storage
            
        Returns:
            Tupla con (ruta_storage, hash_md5, hash_sha256, tamaño_bytes)
            
        Raises:
            StorageException: Si hay error al subir el archivo
        """
        try:
            # Leer contenido del archivo
            file_content = file_data.read()
            file_size = len(file_content)
            
            # Calcular hashes
            hash_md5 = hashlib.md5(file_content).hexdigest()
            hash_sha256 = hashlib.sha256(file_content).hexdigest()
            
            # Generar nombre único seguro
            safe_original_name = self._sanitize_filename(file_name)
            extension = safe_original_name.split('.')[-1] if '.' in safe_original_name else 'bin'
            unique_name = f"{uuid4()}.{extension}"
            
            # Obtener ruta de almacenamiento
            full_path = self._get_storage_path(folder, unique_name)
            relative_path = self._get_relative_path(full_path)
            
            # Escribir archivo con permisos restrictivos
            with open(full_path, 'wb') as f:
                f.write(file_content)
            
            # Establecer permisos 644 (rw-r--r--)
            os.chmod(full_path, 0o644)
            
            logger.info(
                f"Archivo guardado en filesystem: {relative_path} "
                f"(size: {file_size} bytes, md5: {hash_md5})"
            )
            
            return relative_path, hash_md5, hash_sha256, file_size
            
        except Exception as e:
            logger.error(f"Error guardando archivo en filesystem: {e}")
            raise StorageException(f"Error al guardar archivo: {str(e)}")
    
    def get_presigned_url(
        self,
        object_path: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Genera URL relativa para acceder al archivo vía API.
        
        Args:
            object_path: Ruta relativa del archivo
            expires: No usado en filesystem (compatibilidad con interfaz)
            
        Returns:
            URL relativa al endpoint de storage de la API
            
        Raises:
            StorageException: Si el archivo no existe
        """
        try:
            # Verificar que el archivo existe
            full_path = self.base_path / object_path
            if not full_path.exists():
                raise StorageException(f"Archivo no encontrado: {object_path}")
            
            # Generar URL relativa
            # El object_path ya tiene formato: folder/year/month/filename.ext
            url = f"/api/v1/storage/files/{object_path}"
            
            logger.debug(f"URL generada para: {object_path} -> {url}")
            return url
            
        except Exception as e:
            logger.error(f"Error generando URL para archivo: {e}")
            raise StorageException(f"Error generando URL: {str(e)}")
    
    def delete_file(self, object_path: str) -> None:
        """
        Elimina un archivo del filesystem.
        
        Args:
            object_path: Ruta relativa del archivo
            
        Raises:
            StorageException: Si hay error eliminando el archivo
        """
        try:
            full_path = self.base_path / object_path
            
            # Validar que el path está dentro de base_path (seguridad)
            try:
                resolved_path = full_path.resolve()
                resolved_base = self.base_path.resolve()
                resolved_path.relative_to(resolved_base)
            except ValueError:
                raise StorageException("Intento de acceso fuera del directorio permitido")
            
            if not full_path.exists():
                logger.warning(f"Intento de eliminar archivo inexistente: {object_path}")
                return
            
            full_path.unlink()
            logger.info(f"Archivo eliminado del filesystem: {object_path}")
            
        except StorageException:
            raise
        except Exception as e:
            logger.error(f"Error eliminando archivo: {e}")
            raise StorageException(f"Error eliminando archivo: {str(e)}")
    
    def file_exists(self, object_path: str) -> bool:
        """
        Verifica si un archivo existe en el filesystem.
        
        Args:
            object_path: Ruta relativa del archivo
            
        Returns:
            True si el archivo existe, False en caso contrario
        """
        try:
            full_path = self.base_path / object_path
            exists = full_path.exists() and full_path.is_file()
            logger.debug(f"Verificación de existencia {object_path}: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error verificando existencia de archivo: {e}")
            return False
    
    def get_file_info(self, object_path: str) -> Optional[dict]:
        """
        Obtiene información de un archivo.
        
        Args:
            object_path: Ruta relativa del archivo
            
        Returns:
            Diccionario con información del archivo o None si no existe
        """
        try:
            full_path = self.base_path / object_path
            
            if not full_path.exists():
                logger.debug(f"Archivo no encontrado: {object_path}")
                return None
            
            stat = full_path.stat()
            
            # Intentar detectar mime type (requiere python-magic)
            content_type = "application/octet-stream"
            try:
                import magic
                content_type = magic.from_file(str(full_path), mime=True)
            except ImportError:
                # Fallback: inferir por extensión
                extension = full_path.suffix.lower()
                mime_map = {
                    '.pdf': 'application/pdf',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.doc': 'application/msword',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                }
                content_type = mime_map.get(extension, 'application/octet-stream')
            
            return {
                "size": stat.st_size,
                "content_type": content_type,
                "last_modified": datetime.fromtimestamp(stat.st_mtime),
                "created": datetime.fromtimestamp(stat.st_ctime),
                "path": object_path
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo info del archivo: {e}")
            return None
    
    def get_file_content(self, object_path: str) -> Optional[bytes]:
        """
        Lee el contenido completo de un archivo.
        
        Args:
            object_path: Ruta relativa del archivo
            
        Returns:
            Contenido del archivo como bytes o None si no existe
        """
        try:
            full_path = self.base_path / object_path
            
            # Validar path (seguridad) - ANTES de verificar existencia
            try:
                resolved_path = full_path.resolve()
                resolved_base = self.base_path.resolve()
                resolved_path.relative_to(resolved_base)
            except ValueError:
                raise StorageException("Intento de acceso fuera del directorio permitido")
            
            if not full_path.exists():
                return None
            
            with open(full_path, 'rb') as f:
                content = f.read()
            
            logger.debug(f"Archivo leído: {object_path} ({len(content)} bytes)")
            return content
            
        except StorageException:
            raise
        except Exception as e:
            logger.error(f"Error leyendo archivo: {e}")
            raise StorageException(f"Error leyendo archivo: {str(e)}")
