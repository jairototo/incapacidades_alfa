"""
Implementación de almacenamiento en MinIO/S3.
"""
import hashlib
import io
from datetime import timedelta
from typing import BinaryIO, Optional, Tuple
from uuid import uuid4

from minio import Minio
from minio.error import S3Error
from loguru import logger

from app.core.storage_core.base import StorageBackend
from app.core.exceptions import StorageException


class MinIOStorage(StorageBackend):
    """
    Backend de almacenamiento en MinIO/S3.
    
    Compatible con cualquier storage S3-compatible (MinIO, AWS S3, DigitalOcean Spaces, etc.)
    """
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str = "incapacidades",
        secure: bool = False
    ):
        """
        Inicializa el cliente de MinIO.
        
        Args:
            endpoint: URL del servidor MinIO (ej: "localhost:9010")
            access_key: Access key para autenticación
            secret_key: Secret key para autenticación
            bucket_name: Nombre del bucket a usar
            secure: True para HTTPS, False para HTTP
        """
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket_name = bucket_name
        self._ensure_bucket_exists()
        logger.info(f"MinIOStorage inicializado: {endpoint}/{bucket_name}")
    
    def _ensure_bucket_exists(self) -> None:
        """Crea el bucket si no existe."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' creado exitosamente")
            else:
                logger.debug(f"Bucket '{self.bucket_name}' ya existe")
        except S3Error as e:
            logger.error(f"Error verificando/creando bucket: {e}")
            raise StorageException(f"Error al configurar MinIO storage: {str(e)}")
    
    def upload_file(
        self,
        file_data: BinaryIO,
        file_name: str,
        content_type: str,
        folder: str = "documentos"
    ) -> Tuple[str, str, str, int]:
        """
        Sube un archivo a MinIO.
        
        Args:
            file_data: Datos del archivo (stream binario)
            file_name: Nombre original del archivo
            content_type: Tipo MIME del archivo
            folder: Carpeta dentro del bucket
            
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
            
            # Generar nombre único
            extension = file_name.split('.')[-1] if '.' in file_name else 'bin'
            unique_name = f"{uuid4()}.{extension}"
            object_path = f"{folder}/{unique_name}"
            
            # Convertir a stream nuevamente
            file_stream = io.BytesIO(file_content)
            
            # Subir archivo
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=file_stream,
                length=file_size,
                content_type=content_type
            )
            
            logger.info(
                f"Archivo subido a MinIO: {object_path} "
                f"(size: {file_size} bytes, md5: {hash_md5})"
            )
            
            return object_path, hash_md5, hash_sha256, file_size
            
        except S3Error as e:
            logger.error(f"Error subiendo archivo a MinIO: {e}")
            raise StorageException(f"Error al subir archivo: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado al subir archivo: {e}")
            raise StorageException(f"Error inesperado: {str(e)}")
    
    def get_presigned_url(
        self,
        object_path: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Genera una URL firmada para descargar un archivo de MinIO.
        
        Args:
            object_path: Ruta del objeto en el bucket
            expires: Tiempo de expiración de la URL
            
        Returns:
            URL firmada para descarga
            
        Raises:
            StorageException: Si hay error generando la URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                expires=expires
            )
            logger.debug(f"URL firmada generada para: {object_path}")
            return url
        except S3Error as e:
            logger.error(f"Error generando URL firmada: {e}")
            raise StorageException(f"Error generando URL de descarga: {str(e)}")
    
    def delete_file(self, object_path: str) -> None:
        """
        Elimina un archivo de MinIO.
        
        Args:
            object_path: Ruta del objeto en el bucket
            
        Raises:
            StorageException: Si hay error eliminando el archivo
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_path
            )
            logger.info(f"Archivo eliminado de MinIO: {object_path}")
        except S3Error as e:
            logger.error(f"Error eliminando archivo: {e}")
            raise StorageException(f"Error eliminando archivo: {str(e)}")
    
    def file_exists(self, object_path: str) -> bool:
        """
        Verifica si un archivo existe en MinIO.
        
        Args:
            object_path: Ruta del objeto en el bucket
            
        Returns:
            True si el archivo existe, False en caso contrario
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_path
            )
            return True
        except S3Error:
            return False
    
    def get_file_info(self, object_path: str) -> Optional[dict]:
        """
        Obtiene información de un archivo en MinIO.
        
        Args:
            object_path: Ruta del objeto en el bucket
            
        Returns:
            Diccionario con información del archivo o None si no existe
        """
        try:
            stat = self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_path
            )
            return {
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modidddddfied": stat.last_modified,  
                "metadata": stat.metadata
            }
        except S3Error as e:
            logger.error(f"Error obteniendo info del archivo: {e}")
            return None
