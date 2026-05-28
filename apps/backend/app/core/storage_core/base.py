"""
Interfaz abstracta para backends de almacenamiento (Strategy Pattern).
"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, Tuple
from datetime import timedelta


class StorageBackend(ABC):
    """
    Interfaz abstracta para backends de almacenamiento.
    
    Permite implementar diferentes estrategias de storage (filesystem, MinIO, S3, etc.)
    manteniendo una API consistente.
    """
    
    @abstractmethod
    def upload_file(
        self,
        file_data: BinaryIO,
        file_name: str,
        content_type: str,
        folder: str = "documentos"
    ) -> Tuple[str, str, str, int]:
        """
        Sube un archivo al storage.
        
        Args:
            file_data: Datos del archivo (stream binario)
            file_name: Nombre original del archivo
            content_type: Tipo MIME del archivo
            folder: Carpeta/categoría dentro del storage
            
        Returns:
            Tupla con (ruta_storage, hash_md5, hash_sha256, tamaño_bytes)
            
        Raises:
            StorageException: Si hay error al subir el archivo
        """
        pass
    
    @abstractmethod
    def get_presigned_url(
        self,
        object_path: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Genera una URL de acceso temporal al archivo.
        
        En filesystem: URL relativa al endpoint de la API
        En MinIO/S3: URL firmada con expiración
        
        Args:
            object_path: Ruta del objeto en el storage
            expires: Tiempo de expiración de la URL
            
        Returns:
            URL de acceso al archivo
            
        Raises:
            StorageException: Si hay error generando la URL
        """
        pass
    
    @abstractmethod
    def delete_file(self, object_path: str) -> None:
        """
        Elimina un archivo del storage.
        
        Args:
            object_path: Ruta del objeto en el storage
            
        Raises:
            StorageException: Si hay error eliminando el archivo
        """
        pass
    
    @abstractmethod
    def file_exists(self, object_path: str) -> bool:
        """
        Verifica si un archivo existe en el storage.
        
        Args:
            object_path: Ruta del objeto en el storage
            
        Returns:
            True si el archivo existe, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_file_info(self, object_path: str) -> Optional[dict]:
        """
        Obtiene información/metadata de un archivo. ASDad SD
        
        Args:
            object_path: Ruta del objeto en el storage
            
        Returns:
            Diccionario con información del archivo o None si no existe
        """
        pass
