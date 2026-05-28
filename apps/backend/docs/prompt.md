## PROMPT PARA MODIFICAR SISTEMA DE ALMACENAMIENTO DE DOCUMENTOS

### **Contexto**

El sistema actual de gestión de incapacidades utiliza MinIO/S3 para almacenamiento de documentos. Se requiere cambiar a un sistema de almacenamiento en **filesystem local** (carpetas en el servidor), pero manteniendo la arquitectura extensible para poder reactivar MinIO en el futuro si es necesario.

**Estado actual**:
- Storage implementado: MinIO/S3 (app/core/storage.py)
- Documentos funcionando: 21 tests pasando
- Módulo completo: DocumentoService, DocumentoRepository, 6 endpoints REST

### **Objetivo**

Modificar el sistema de almacenamiento de documentos para usar **filesystem local** con estructura de carpetas organizada, manteniendo compatibilidad con MinIO mediante patrón Strategy.

### **Requerimientos Específicos**

#### 1. Crear Sistema de Storage Abstracto (Strategy Pattern)

**Archivo**: `app/core/storage/base.py` (NUEVO)
```python
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from datetime import datetime

class StorageBackend(ABC):
    """Interfaz abstracta para backends de almacenamiento."""
    
    @abstractmethod
    async def upload_file(
        self, 
        file: BinaryIO, 
        bucket: str, 
        object_name: str
    ) -> dict:
        """Upload archivo y retorna metadata."""
        pass
    
    @abstractmethod
    async def download_file(
        self, 
        bucket: str, 
        object_name: str
    ) -> bytes:
        """Download archivo como bytes."""
        pass
    
    @abstractmethod
    async def get_presigned_url(
        self, 
        bucket: str, 
        object_name: str, 
        expires: int = 3600
    ) -> str:
        """Genera URL de acceso temporal."""
        pass
    
    @abstractmethod
    async def delete_file(
        self, 
        bucket: str, 
        object_name: str
    ) -> bool:
        """Elimina archivo físicamente."""
        pass
    
    @abstractmethod
    async def file_exists(
        self, 
        bucket: str, 
        object_name: str
    ) -> bool:
        """Verifica existencia de archivo."""
        pass
```

#### 2. Implementar FileSystemStorage (Nueva Clase)

**Archivo**: `app/core/storage/filesystem.py` (NUEVO)

**Estructura de carpetas**:
```
storage/
├── documentos/           # Bucket principal
│   ├── incapacidades/   # Por tipo de entidad
│   │   ├── 2024/       # Por año
│   │   │   ├── 01/     # Por mes
│   │   │   │   ├── {uuid}.pdf
│   │   │   │   └── {uuid}.jpg
│   │   │   └── 02/
│   │   └── 2025/
│   └── siniestros/
│       └── 2024/
│           └── 01/
└── temp/                # Archivos temporales
```

**Funcionalidades requeridas**:
- `upload_file()`: Copia archivo a estructura de carpetas organizadas por año/mes
- `download_file()`: Lee archivo como bytes desde disco
- `get_presigned_url()`: Genera ruta relativa `/api/v1/storage/files/{bucket}/{path}` (nuevo endpoint)
- `delete_file()`: Elimina archivo físicamente del filesystem
- `file_exists()`: Verifica con `os.path.exists()`
- `get_file_info()`: Retorna metadata (tamaño, fecha, mime type usando `python-magic`)
- **Auto-creación de directorios**: `os.makedirs(exist_ok=True)`
- **Permisos**: Archivos 644, directorios 755
- **Logging**: Registrar todas las operaciones

**Configuración** (Settings):
```python
# Nuevo en app/core/config.py
STORAGE_BACKEND: str = "filesystem"  # "filesystem" | "minio"
FILESYSTEM_BASE_PATH: str = "/app/storage"  # Ruta base de almacenamiento
FILESYSTEM_SERVE_FILES: bool = True  # Servir archivos directamente
```

#### 3. Refactorizar MinIOStorage (Mantener Existente)

**Archivo**: `app/core/storage/minio.py` (MOVER CÓDIGO ACTUAL)

- Mover clase `StorageClient` existente de `app/core/storage.py`
- Renombrar a `MinIOStorage`
- Implementar interfaz `StorageBackend`
- Mantener toda la funcionalidad actual
- Agregar flag `enabled: bool = False` por defecto

#### 4. Factory de Storage

**Archivo**: `app/core/storage/__init__.py` (MODIFICAR)

```python
from app.core.config import settings
from app.core.storage_core.base import StorageBackend
from app.core.storage_core.filesystem import FileSystemStorage
from app.core.storage_core.minio import MinIOStorage

def get_storage_backend() -> StorageBackend:
    """Factory para obtener backend de storage según configuración."""
    
    backend_type = settings.STORAGE_BACKEND.lower()
    
    if backend_type == "filesystem":
        return FileSystemStorage(
            base_path=settings.FILESYSTEM_BASE_PATH
        )
    elif backend_type == "minio":
        return MinIOStorage(
            endpoint=settings.STORAGE_ENDPOINT,
            access_key=settings.STORAGE_ACCESS_KEY,
            secret_key=settings.STORAGE_SECRET_KEY,
            secure=settings.STORAGE_SECURE
        )
    else:
        raise ValueError(f"Storage backend no soportado: {backend_type}")

# Singleton global
storage_backend: StorageBackend = get_storage_backend()
```

#### 5. Nuevo Endpoint para Servir Archivos

**Archivo**: `app/api/v1/endpoints/storage.py` (NUEVO)

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/files/{bucket}/{year}/{month}/{filename}")
async def serve_file(
    bucket: str, 
    year: str, 
    month: str, 
    filename: str
):
    """
    Sirve archivos del filesystem local.
    Solo funciona si STORAGE_BACKEND=filesystem.
    """
    if settings.STORAGE_BACKEND != "filesystem":
        raise HTTPException(
            status_code=404, 
            detail="File serving solo disponible en modo filesystem"
        )
    
    file_path = os.path.join(
        settings.FILESYSTEM_BASE_PATH,
        bucket,
        year,
        month,
        filename
    )
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Validar que el path no escape del directorio base (seguridad)
    real_path = os.path.realpath(file_path)
    base_path = os.path.realpath(settings.FILESYSTEM_BASE_PATH)
    if not real_path.startswith(base_path):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename
    )
```

Registrar en `app/api/v1/router.py`:
```python
from app.api.v1.endpoints import storage

router.include_router(
    storage.router, 
    prefix="/storage", 
    tags=["storage"]
)
```

#### 6. Actualizar DocumentoService

**Archivo**: `app/services/documento_service.py` (MODIFICAR)

- Cambiar import: `from app.core.storage_core import storage_backend`
- Reemplazar `storage_client` por `storage_backend`
- Mantener toda la lógica de validación existente
- **NO cambiar** firmas de métodos públicos (compatibilidad)

#### 7. Actualizar Event Handlers

**Archivo**: `app/core/events.py` (MODIFICAR)

```python
async def startup_event():
    """Inicialización en startup."""
    
    logger.info("Inicializando backend de storage...")
    
    if settings.STORAGE_BACKEND == "filesystem":
        # Crear directorio base si no existe
        os.makedirs(settings.FILESYSTEM_BASE_PATH, exist_ok=True)
        logger.info(f"Filesystem storage inicializado en: {settings.FILESYSTEM_BASE_PATH}")
    
    elif settings.STORAGE_BACKEND == "minio":
        # Inicializar MinIO (código actual)
        from app.core.storage_core import storage_backend
        if hasattr(storage_backend, 'create_bucket'):
            await storage_backend.create_bucket(settings.STORAGE_BUCKET)
        logger.info("MinIO storage inicializado")
```

#### 8. Variables de Entorno

**Archivo**: `.env` (ACTUALIZAR)

```bash
# Storage Backend Configuration
STORAGE_BACKEND=filesystem  # "filesystem" o "minio"

# Filesystem Storage (cuando STORAGE_BACKEND=filesystem)
FILESYSTEM_BASE_PATH=/app/storage
FILESYSTEM_SERVE_FILES=true

# MinIO Storage (cuando STORAGE_BACKEND=minio)
STORAGE_ENDPOINT=localhost:9010
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=incapacidades
STORAGE_SECURE=false
```

#### 9. Docker Compose

**Archivo**: `docker-compose.yml` (MODIFICAR)

```yaml
services:
  api:
    # ... config existente
    volumes:
      - ./storage:/app/storage  # NUEVO: Montar directorio de storage
      - ./backend:/app
    environment:
      - STORAGE_BACKEND=filesystem
      - FILESYSTEM_BASE_PATH=/app/storage
  
  # MinIO ahora es OPCIONAL
  minio:
    # ... config existente
    profiles:
      - minio  # Solo se levanta si se especifica: docker-compose --profile minio up
```

**Comandos**:
```bash
# Solo con filesystem (predeterminado)
docker-compose up -d

# Con MinIO habilitado
docker-compose --profile minio up -d
```

#### 10. Tests

**Actualizar**: `tests/test_documento_service.py`

- Crear fixture `mock_filesystem_storage`
- Mockear `os.path.exists`, `open()`, `os.makedirs`
- Parametrizar tests para correr con ambos backends:
  ```python
  @pytest.mark.parametrize("storage_backend", ["filesystem", "minio"])
  async def test_upload_documento(storage_backend, ...):
      with patch("app.core.config.settings.STORAGE_BACKEND", storage_backend):
          # Test code
  ```

**Crear**: `tests/test_filesystem_storage.py` (NUEVO)

- 10 tests unitarios específicos para FileSystemStorage
- Mock de sistema de archivos
- Tests de permisos, paths, estructura de directorios

**Crear**: `tests/test_storage_endpoint.py` (NUEVO)

- Test de endpoint `/api/v1/storage/files/{path}`
- Validación de path traversal (seguridad)
- Test de archivo no encontrado

### **Criterios de Aceptación**

- [ ] Patrón Strategy implementado con interfaz `StorageBackend`
- [ ] `FileSystemStorage` funcional con estructura año/mes
- [ ] `MinIOStorage` refactorizado pero funcional (sin cambios de comportamiento)
- [ ] Factory `get_storage_backend()` selecciona según configuración
- [ ] Endpoint `/api/v1/storage/files/{path}` funciona en modo filesystem
- [ ] `DocumentoService` funciona con ambos backends sin cambios en API
- [ ] Variables de entorno permiten cambiar backend fácilmente
- [ ] MinIO opcional en docker-compose (profiles)
- [ ] Tests parametrizados corren para ambos backends
- [ ] 15+ tests nuevos (filesystem + endpoint)
- [ ] Todos los tests existentes (21) siguen pasando
- [ ] Documentación actualizada con ejemplos de configuración
- [ ] Path traversal validation implementada (seguridad)
- [ ] Logging completo de operaciones de storage

### **Consideraciones Técnicas**

**Seguridad**:
- Validar nombres de archivos (sin `../`, caracteres especiales)
- Verificar `os.path.realpath()` para evitar path traversal
- Permisos restrictivos en archivos (644) y directorios (755)
- No servir archivos fuera de `FILESYSTEM_BASE_PATH`

**Performance**:
- Usar `aiofiles` para operaciones async de archivos
- Chunk reading para archivos grandes (no cargar todo en memoria)
- Headers de cache en endpoint de archivos

**Compatibilidad**:
- Mantener API pública de `DocumentoService` sin cambios
- Presigned URLs funcionan diferente pero retornan string en ambos casos
- Metadata de archivos consistente entre backends

**Migración**:
- Crear script `scripts/migrate_storage.py` para migrar de MinIO a filesystem
- Script debe descargar todos los archivos de MinIO y organizarlos en estructura local

**Rollback**:
- Documentar cómo volver a MinIO (cambiar `STORAGE_BACKEND=minio`)
- Verificar que no se pierdan datos en el cambio

### **Tests Esperados**

**Nuevos tests** (15 mínimo):
- `tests/test_filesystem_storage.py`: 10 tests
  - test_upload_file_creates_directories
  - test_upload_file_year_month_structure
  - test_download_file_success
  - test_delete_file_success
  - test_file_exists_true
  - test_file_exists_false
  - test_get_presigned_url_format
  - test_upload_invalid_path
  - test_permissions_644_for_files
  - test_auto_create_missing_directories

- `tests/test_storage_endpoint.py`: 5 tests
  - test_serve_file_success
  - test_serve_file_not_found
  - test_serve_file_path_traversal_blocked
  - test_serve_file_only_filesystem_mode
  - test_serve_file_correct_mime_type

**Tests existentes** (21):
- Deben seguir pasando con ambos backends
- Parametrizar con `@pytest.mark.parametrize("storage_backend", [...])`

### **Ejemplo de Uso/Salida Esperada**

#### Modo Filesystem (Nuevo - Predeterminado)

```bash
# .env
STORAGE_BACKEND=filesystem
FILESYSTEM_BASE_PATH=/app/storage

# Upload documento
POST /api/v1/documentos/upload
file: certificado.pdf
incapacidad_id: "uuid"

# Response
{
  "id": "uuid",
  "ruta_storage": "documentos/incapacidades/2026/01/abc123.pdf",
  "hash_md5": "...",
  ...
}

# Download (URL relativa local)
GET /api/v1/documentos/{id}/download

# Response
{
  "url": "http://localhost:8010/api/v1/storage/files/documentos/incapacidades/2026/01/abc123.pdf",
  "expires_in": 3600
}

# Estructura en disco
/app/storage/
└── documentos/
    └── incapacidades/
        └── 2026/
            └── 01/
                └── abc123.pdf
```

#### Modo MinIO (Opcional - Futuro)

```bash
# .env
STORAGE_BACKEND=minio
STORAGE_ENDPOINT=minio:9010
STORAGE_BUCKET=incapacidades

# Mismo comportamiento de API
# Cambio solo interno (storage backend diferente)
```

### **Documentación a Actualizar**

1. **README.md**: Sección de configuración de storage
2. **docs/MODULO_DOCUMENTOS.md**: Explicar ambos backends
3. **ESTADO_PROYECTO.md**: Actualizar con arquitectura de storage
4. **.env.example**: Comentarios explicando cada variable

### **Entrega Esperada**

Al finalizar, debe entregar:

1. **Código**:
   - 3 archivos nuevos (base.py, filesystem.py, storage.py endpoint)
   - 1 archivo refactorizado (minio.py)
   - 3 archivos modificados (storage/__init__.py, documento_service.py, events.py)
   - 2 archivos de tests nuevos
   
2. **Tests**:
   - 15+ tests nuevos pasando
   - 21 tests existentes siguen pasando
   - Total: 36+ tests (100% passing)

3. **Documentación**:
   - README actualizado
   - Sección en MODULO_DOCUMENTOS.md
   - Comentarios en código

4. **Configuración**:
   - .env.example actualizado
   - docker-compose.yml con profiles

5. **Prompt Estructurado**:
   - Prompt para próximo paso (migración de datos o implementación de otro módulo)

---

## ¿Proceder con la Implementación?

Este prompt está listo para ser usado en modo agente. Contiene todos los detalles técnicos, criterios de aceptación, y ejemplos necesarios para realizar el cambio de manera estructurada y manteniendo la flexibilidad para volver a MinIO en el futuro.