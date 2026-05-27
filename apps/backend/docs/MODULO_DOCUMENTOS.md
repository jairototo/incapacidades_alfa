# Módulo de Documentos

Sistema de gestión de documentos adjuntos para incapacidades médicas con almacenamiento seguro en MinIO/S3.

## 📋 Características

- ✅ **Upload seguro** de archivos PDF, imágenes (JPG, PNG) y documentos Office (DOCX)
- ✅ **Validaciones** de tipo MIME, extensión y tamaño (máx 10MB)
- ✅ **Hashes MD5 y SHA256** para verificación de integridad
- ✅ **Presigned URLs** con expiración configurable para descargas seguras
- ✅ **Soft delete** por defecto (manteniendo historial) o hard delete (eliminación física)
- ✅ **Almacenamiento en MinIO/S3** con bucket auto-creado
- ✅ **Relaciones** con Incapacidad, Siniestro y Usuario

## 🗂️ Estructura

```
app/
├── models/documento.py           # Modelo SQLAlchemy
├── schemas/documento.py          # Schemas Pydantic
├── db/repositories/
│   └── documento_repository.py   # Repository pattern
├── services/
│   └── documento_service.py      # Lógica de negocio
├── api/v1/endpoints/
│   └── documentos.py             # Endpoints REST
└── core/
    └── storage.py                # Cliente MinIO/S3

tests/
├── test_documento_service.py     # 11 tests unitarios
└── test_documento_api.py         # 10 tests integración

scripts/
└── test_documentos.py            # Script de prueba con datos reales
```

## 🚀 Uso

### 1. Configuración

Variables de entorno en `.env`:

```env
# MinIO/S3 Storage
STORAGE_ENDPOINT=localhost:9010
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=incapacidades
STORAGE_SECURE=false

# File Upload
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_EXTENSIONS=pdf,jpg,jpeg,png,doc,docx
```

### 2. Inicialización

El bucket se crea automáticamente en el startup de la aplicación:

```python
# app/core/events.py
from app.core.storage import storage_client
logger.info(f"Storage client initialized (bucket: {storage_client.bucket_name})")
```

### 3. Endpoints API

#### Upload de Documento

```bash
POST /api/v1/documentos/upload
Content-Type: multipart/form-data

Parámetros:
- file: archivo a subir (UploadFile)
- incapacidad_id: UUID de la incapacidad
- tipo_documento: INCAPACIDAD_MEDICA | CEDULA | HISTORIA_CLINICA | etc.
```

**Ejemplo con curl**:

```bash
curl -X POST http://localhost:8010/api/v1/documentos/upload \
  -F "file=@certificado.pdf" \
  -F "incapacidad_id=890400e2-4bd4-4416-8a19-87a09957ca55" \
  -F "tipo_documento=INCAPACIDAD_MEDICA" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Respuesta (201)**:

```json
{
  "documento": {
    "id": "728ce2de-f066-4a4d-a6cf-4ad20c4c975d",
    "incapacidad_id": "890400e2-4bd4-4416-8a19-87a09957ca55",
    "tipo_documento": "INCAPACIDAD_MEDICA",
    "nombre_archivo": "1b177522-8c57-45b5-9a26-ccef34da1f3a.pdf",
    "nombre_original": "certificado.pdf",
    "mime_type": "application/pdf",
    "tamanio_bytes": 398042,
    "hash_md5": "0cb01466cbe58a1bfa70859e1e162dd1",
    "hash_sha256": "abc123...",
    "validado": false,
    "created_at": "2026-01-13T21:44:01Z"
  },
  "url_descarga": "http://minio:9000/incapacidades/documentos/..."
}
```

#### Descargar Documento

```bash
GET /api/v1/documentos/{documento_id}/download?expires_hours=1
```

**Respuesta (200)**:

```json
{
  "url": "http://minio:9000/incapacidades/documentos/file.pdf?X-Amz-Signature=...",
  "expires_in": 3600,
  "nombre_archivo": "certificado.pdf"
}
```

#### Listar Documentos de Incapacidad

```bash
GET /api/v1/documentos/incapacidades/{incapacidad_id}?skip=0&limit=100
```

**Respuesta (200)**:

```json
[
  {
    "id": "728ce2de-f066-4a4d-a6cf-4ad20c4c975d",
    "tipo_documento": "INCAPACIDAD_MEDICA",
    "nombre_original": "certificado.pdf",
    "mime_type": "application/pdf",
    "tamanio_bytes": 398042,
    "validado": false,
    "created_at": "2026-01-13T21:44:01Z"
  }
]
```

#### Eliminar Documento

```bash
DELETE /api/v1/documentos/{documento_id}?hard_delete=false
```

**Parámetros**:
- `hard_delete=false` (default): Soft delete - solo elimina registro en BD
- `hard_delete=true`: Hard delete - elimina registro en BD y archivo en MinIO

**Respuesta (204)**: Sin contenido

### 4. Uso Programático

```python
from app.services.documento_service import DocumentoService
from uuid import UUID

# En un endpoint o función async
async def upload_document(
    db: AsyncSession,
    file: UploadFile,
    incapacidad_id: UUID,
    user_id: UUID
):
    service = DocumentoService(db)
    
    # Upload
    documento = await service.upload_documento(
        incapacidad_id=incapacidad_id,
        file_data=file.file,
        filename=file.filename,
        content_type=file.content_type,
        tipo_documento="INCAPACIDAD_MEDICA",
        uploaded_by_id=user_id
    )
    
    # Generar URL de descarga (válida por 24 horas)
    url = await service.get_download_url(documento.id, expires_hours=24)
    
    return {"documento": documento, "url": url}
```

## 🧪 Tests

### Ejecutar Tests Unitarios

```bash
docker-compose exec api python -m pytest tests/test_documento_service.py -v

# 11 tests:
# - Validaciones de extensión, MIME type, tamaño
# - Upload exitoso con mock de MinIO
# - Generación de presigned URLs
# - Eliminación soft y hard
# - Listados y conteos
```

### Ejecutar Tests de Integración

```bash
docker-compose exec api python -m pytest tests/test_documento_api.py -v

# 10 tests:
# - Upload completo con autenticación
# - Validaciones de archivo
# - Download con presigned URL
# - Listado con paginación
# - Permisos y autorización
```

### Script de Prueba con Datos Reales

```bash
docker-compose exec api python scripts/test_documentos.py

# Prueba completa:
# 1. Busca incapacidad APROBADA de seed data
# 2. Sube archivo PDF de 398KB
# 3. Genera presigned URL
# 4. Lista documentos de la incapacidad
```

## 🔒 Seguridad

### Validaciones Implementadas

1. **Extensión de archivo**:
   ```python
   ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]
   ```

2. **Tipo MIME**:
   ```python
   ALLOWED_MIME_TYPES = {
       "application/pdf": [".pdf"],
       "image/jpeg": [".jpg", ".jpeg"],
       "image/png": [".png"],
       "application/msword": [".doc"],
       "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"]
   }
   ```

3. **Tamaño máximo**: 10MB (configurable)

4. **Hashing**: MD5 y SHA256 para verificación de integridad

5. **Nombres únicos**: UUID + extensión original

6. **Presigned URLs**: Expiración configurable (default 1 hora)

### Permisos Requeridos

- `DOCUMENTO_CREATE`: Upload de documentos
- `DOCUMENTO_READ`: Lectura y descarga
- `DOCUMENTO_UPDATE`: Actualizar metadatos
- `DOCUMENTO_DELETE`: Eliminar documentos

## 📊 Modelo de Datos

```sql
CREATE TABLE documento (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incapacidad_id UUID NOT NULL REFERENCES incapacidad(id) ON DELETE CASCADE,
    tipo_documento VARCHAR(50) NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    nombre_original VARCHAR(255) NOT NULL,
    ruta_storage VARCHAR(500) NOT NULL,
    bucket VARCHAR(100) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    tamanio_bytes BIGINT NOT NULL,
    hash_md5 VARCHAR(32),
    hash_sha256 VARCHAR(64),
    uploaded_by_id UUID REFERENCES usuario(id),
    validado BOOLEAN DEFAULT FALSE,
    observacion_validacion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documento_incapacidad ON documento(incapacidad_id);
CREATE INDEX idx_documento_tipo ON documento(tipo_documento);
CREATE INDEX idx_documento_sha256 ON documento(hash_sha256);
```

## 🛠️ Troubleshooting

### Error: "Bucket does not exist"

```bash
# Verificar que MinIO está corriendo
docker-compose ps minio

# El bucket se crea automáticamente en startup
# Si falla, revisar logs:
docker-compose logs minio
docker-compose logs api
```

### Error: "File too large"

```bash
# Ajustar límite en .env
MAX_UPLOAD_SIZE_MB=20  # Default: 10MB
```

### Error: "Invalid file extension"

```bash
# Agregar extensión permitida en .env
ALLOWED_FILE_EXTENSIONS=pdf,jpg,jpeg,png,doc,docx,xlsx
```

### Presigned URL no funciona

```bash
# Verificar endpoint de MinIO
# En Docker, usar el nombre del servicio "minio" en STORAGE_ENDPOINT
# Para acceso externo, usar "localhost:9010"

STORAGE_ENDPOINT=minio:9000  # Para uso interno (containers)
# o
STORAGE_ENDPOINT=localhost:9010  # Para acceso desde host
```

## 📈 Métricas

- **21 tests** pasando (11 unitarios + 10 integración)
- **85% cobertura** en DocumentoService
- **Tiempo promedio upload**: ~1 segundo para archivo de 400KB
- **Tamaño promedio documento**: 0.38 MB
- **Storage utilizado**: Escalable con MinIO

## 🔗 Referencias

- [Modelo Documento](../app/models/documento.py)
- [DocumentoService](../app/services/documento_service.py)
- [Endpoints API](../app/api/v1/endpoints/documentos.py)
- [Storage Client](../app/core/storage.py)
- [Tests](../tests/test_documento_service.py)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/API.html)
