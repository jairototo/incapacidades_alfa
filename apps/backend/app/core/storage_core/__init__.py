"""
Factory de backends de almacenamiento.

Proporciona acceso al backend de storage configurado mediante patrón Strategy.
"""
from loguru import logger

from app.core.storage_core.base import StorageBackend
from app.core.storage_core.filesystem import FileSystemStorage
from app.core.storage_core.minio import MinIOStorage


def get_storage_backend() -> StorageBackend:
    """
    Factory para obtener el backend de storage según configuración.
    
    El tipo de backend se determina por la variable STORAGE_BACKEND en settings.
    
    Backends soportados:
        - "filesystem": Almacenamiento en disco local
        - "minio": Almacenamiento en MinIO/S3
    
    Returns:
        Instancia del backend de storage configurado
        
    Raises:
        ValueError: Si el backend configurado no es soportado
        
    Examples:
        >>> from app.core.storage_core import storage_backend
        >>> url = storage_backend.get_presigned_url("path/to/file.pdf")
    """
    # Import settings here to avoid circular imports
    from app.core.config import settings
    
    backend_type = settings.STORAGE_BACKEND.lower()
    
    if backend_type == "filesystem":
        logger.info("Usando FileSystemStorage como backend de almacenamiento")
        return FileSystemStorage(
            base_path=settings.FILESYSTEM_BASE_PATH
        )
    
    elif backend_type == "minio":
        logger.info("Usando MinIOStorage como backend de almacenamiento")
        return MinIOStorage(
            endpoint=settings.STORAGE_ENDPOINT,
            access_key=settings.STORAGE_ACCESS_KEY,
            secret_key=settings.STORAGE_SECRET_KEY,
            bucket_name=settings.STORAGE_BUCKET,
            secure=settings.STORAGE_SECURE
        )
    
    else:
        raise ValueError(
            f"Storage backend no soportado: '{backend_type}'. "
            f"Opciones válidas: 'filesystem', 'minio'"
        )


# Singleton global - se inicializa una vez al importar el módulo
storage_backend: StorageBackend = get_storage_backend()


__all__ = [
    "StorageBackend",
    "FileSystemStorage",
    "MinIOStorage",
    "storage_backend",
    "get_storage_backend"
]
