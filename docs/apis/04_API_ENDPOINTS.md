# API Endpoints - Sistema de Gestión de Incapacidades

**Versión API**: v1.0.0  
**Base URL**: `http://localhost:8010/api/v1`  
**Última actualización**: 20 de junio de 2026

---

> ## 🔁 ACTUALIZACIÓN 2026-06-20 — Endpoints del Portal Externo
>
> El Portal Externo dejó de ser público. Los endpoints que consume hoy requieren
> autenticación con rol `EMPRESA` (`empresa_id` del token):
>
> | Endpoint | Método | Uso |
> |----------|--------|-----|
> | `/api/v1/auth/login` | POST | Login de la empresa (reutilizado) |
> | `/api/v1/incapacidades/radicar` | POST | Radicación individual |
> | `/api/v1/incapacidades/radicar-masiva/validar` | POST | Valida plantilla Excel por fila |
> | `/api/v1/incapacidades/radicar-masiva` | POST | Radicación masiva (lote + ZIP de soportes) |
> | `/api/v1/incapacidades/mi-empresa` | GET | Consulta de incapacidades de la empresa |
> | `/api/v1/empresas/{empresa_id}/empleados` | GET | Empleados de la empresa (anidado) |
>
> El endpoint **`GET /api/v1/incapacidades/consultar` (público, sin auth) ya no
> se usa desde el Portal Externo**; la consulta es autenticada por empresa. Las
> referencias a "endpoints públicos sin autenticación" más abajo corresponden al
> diseño original. Integraciones ServiAlfa/Sicat son **STUB**. Fuente:
> [`../superpowers/PR-portal-externo-empresa-refactor.md`](../superpowers/PR-portal-externo-empresa-refactor.md).

## Tabla de Contenidos

1. [Autenticación](#autenticación)
2. [Usuarios](#usuarios)
3. [Solicitantes](#solicitantes)
4. [Catálogos](#catálogos)
5. [Afiliados](#afiliados)
6. [Empresas](#empresas)
7. [Empleados](#empleados)
8. [Incapacidades](#incapacidades)
9. [Siniestros](#siniestros)
10. [Órdenes de Pago](#órdenes-de-pago)
11. [Documentos](#documentos)
12. [Historial de Estados](#historial-de-estados)
13. [Storage](#storage)
14. [Health Checks](#health-checks)

---

## Convenciones

### Autenticación
La mayoría de endpoints requieren autenticación JWT:
```http
Authorization: Bearer <access_token>
```

**Excepciones** (endpoints públicos sin autenticación):
- `GET /api/v1/incapacidades/consultar`
- `GET /api/v1/incapacidades/{numero}/documentos/{documento_id}/download`
- `GET /api/v1/health`
- `GET /api/v1/health/db`

### Códigos de Estado HTTP
- `200` OK - Solicitud exitosa
- `201` Created - Recurso creado exitosamente
- `204` No Content - Operación exitosa sin contenido de respuesta
- `400` Bad Request - Error de validación o parámetros inválidos
- `401` Unauthorized - Token ausente o inválido
- `403` Forbidden - Permisos insuficientes
- `404` Not Found - Recurso no encontrado
- `422` Unprocessable Entity - Error de validación de datos
- `500` Internal Server Error - Error del servidor

### Paginación
Endpoints de listado soportan:
```
?skip=0&limit=100
```
- `skip`: Registros a omitir (default: 0)
- `limit`: Máximo de registros (default: 100, max: 500)

---

## 1. Autenticación

### 1.1. Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
```

**Body**:
```
username=usuario@example.com
password=contraseña_segura
```

**Response 200**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "usuario@example.com",
    "nombres": "Juan",
    "apellidos": "Pérez",
    "rol": "AUDITOR",
    "estado": "ACTIVO"
  }
}
```

**Roles disponibles**: `ADMIN`, `AUDITOR`, `APROBADOR`, `EMPRESA`, `EMPLEADO`, `READONLY`

---

### 1.2. Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response 204**: No content (logout exitoso)

---

### 1.3. Logout All
```http
POST /api/v1/auth/logout-all
Authorization: Bearer <access_token>
```

**Response 204**: No content  
**Efecto**: Invalida todos los tokens del usuario (incrementa `token_version`)

---

### 1.4. Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json
```

**Body**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response 200**:
```json
{
  "access_token": "nuevo_eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### 1.5. Get Current User (Me)
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response 200**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "usuario@example.com",
  "nombres": "Juan",
  "apellidos": "Pérez",
  "rol": "AUDITOR",
  "estado": "ACTIVO",
  "created_at": "2026-01-15T10:30:00",
  "permisos": [
    "INCAPACIDAD_READ",
    "INCAPACIDAD_AUDIT",
    "DOCUMENTO_READ"
  ]
}
```

---

### 1.6. Change Password
```http
POST /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body**:
```json
{
  "current_password": "contraseña_actual",
  "new_password": "nueva_contraseña_segura123"
}
```

**Response 204**: No content (cambio exitoso)

---

## 8. Incapacidades

### 8.1. Listar Incapacidades
```http
GET /api/v1/incapacidades/
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `skip` (integer, default: 0) - Registros a omitir
- `limit` (integer, default: 100) - Máximo de registros

**Response 200**:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "numero": "INC-ARL-20260123-000001",
    "tipo": "ARL",
    "subtipo": "ACCIDENTE_TRABAJO",
    "estado": "EN_AUDITORIA",
    "prioridad": "ALTA",
    "fecha_inicio": "2026-01-20",
    "fecha_fin": "2026-01-25",
    "dias_totales": 5,
    "diagnostico_cie10": "S06.0",
    "diagnostico_descripcion": "Conmoción cerebral",
    "valor_total": 2500000.00,
    "empleado": {
      "id": "...",
      "nombres": "María",
      "apellidos": "González"
    },
    "empresa": {
      "id": "...",
      "razon_social": "Empresa XYZ S.A."
    },
    "created_at": "2026-01-23T08:15:00",
    "updated_at": "2026-01-23T09:00:00"
  }
]
```

**Roles**: `ADMIN`, `AUDITOR`, `APROBADOR`, `READONLY`

---

### 8.2. Obtener Incapacidad por ID
```http
GET /api/v1/incapacidades/{incapacidad_id}
Authorization: Bearer <access_token>
```

**Path Parameters**:
- `incapacidad_id` (UUID) - ID de la incapacidad

**Response 200**: `IncapacidadInDB` (igual estructura que 8.1)

**Response 404**:
```json
{
  "detail": "Incapacidad no encontrada"
}
```

---

### 8.3. Consultar Incapacidad Pública (Sin Autenticación)
```http
GET /api/v1/incapacidades/consultar
```

**Query Parameters** (al menos uno requerido):
- `numero` (string) - Número de radicación (ej: INC-ARL-20260123-000001)
- `documento` (string) + `tipo_documento` (string) - Documento del empleado/afiliado

**Response 200**:
```json
{
  "numero": "INC-ARL-20260123-000001",
  "tipo": "ARL",
  "estado": "EN_AUDITORIA",
  "fecha_inicio": "2026-01-20",
  "fecha_fin": "2026-01-25",
  "dias_totales": 5,
  "diagnostico_cie10": "S06.0",
  "valor_total": 2500000.00,
  "created_at": "2026-01-23T08:15:00",
  "historial_estados": [
    {
      "estado": "RADICADA",
      "fecha_cambio": "2026-01-23T08:15:00",
      "observaciones": null
    },
    {
      "estado": "EN_AUDITORIA",
      "fecha_cambio": "2026-01-23T09:00:00",
      "observaciones": "Asignado a auditor"
    }
  ]
}
```

**Response 400**:
```json
{
  "detail": "Debe proporcionar número de radicación O documento + tipo_documento"
}
```

**Response 404**:
```json
{
  "detail": "No se encontró ninguna incapacidad con los datos proporcionados"
}
```

---

### 8.4. Crear Incapacidad
```http
POST /api/v1/incapacidades/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body** (Incapacidad ARL):
```json
{
  "tipo": "ARL",
  "subtipo": "ACCIDENTE_TRABAJO",
  "fecha_inicio": "2026-01-20",
  "fecha_fin": "2026-01-25",
  "diagnostico_cie10": "S06.0",
  "descripcion_diagnostico": "Conmoción cerebral",
  "valor_dia": 500000.00,
  "prioridad": "ALTA",
  "observaciones": "Caída desde altura",
  "empleado_id": "550e8400-e29b-41d4-a716-446655440000",
  "empresa_id": "660e8400-e29b-41d4-a716-446655440000",
  "siniestro_id": "770e8400-e29b-41d4-a716-446655440000"
}
```

**Body** (Incapacidad SALUD):
```json
{
  "tipo": "SALUD",
  "subtipo": "ENFERMEDAD_GENERAL",
  "fecha_inicio": "2026-01-20",
  "fecha_fin": "2026-01-25",
  "diagnostico_cie10": "J06.9",
  "descripcion_diagnostico": "Infección respiratoria aguda",
  "valor_dia": 300000.00,
  "prioridad": "NORMAL",
  "afiliado_id": "880e8400-e29b-41d4-a716-446655440000"
}
```

**Response 201**: `IncapacidadInDB` con número generado automáticamente

**Validaciones**:
- ARL requiere: `empleado_id` + `empresa_id`
- SALUD requiere: `afiliado_id`
- CIE-10 debe ser válido (verificación en catálogo)
- Fechas: `fecha_fin` debe ser >= `fecha_inicio`

---

### 8.5. Actualizar Incapacidad
```http
PUT /api/v1/incapacidades/{incapacidad_id}
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body** (campos opcionales):
```json
{
  "fecha_fin": "2026-01-27",
  "diagnostico_cie10": "S06.1",
  "prioridad": "URGENTE",
  "observaciones": "Actualización médica"
}
```

**Response 200**: `IncapacidadInDB` actualizado

**Restricciones**: No se puede modificar si estado es `APROBADA`, `EN_PAGO` o `PAGADA`

---

### 8.6. Radicar Incapacidad
```http
POST /api/v1/incapacidades/{incapacidad_id}/radicar
Authorization: Bearer <access_token>
```

**Transición**: `RADICADA` → `EN_AUDITORIA`

**Response 200**: `IncapacidadInDB` con estado actualizado

**Roles**: `ADMIN`, `AUDITOR`

---

### 8.7. Auditar Incapacidad
```http
POST /api/v1/incapacidades/{incapacidad_id}/auditar
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body**:
```json
{
  "accion": "SOLICITAR_INFORMACION",
  "observaciones": "Se requiere historia clínica completa para continuar auditoría"
}
```

**Acciones disponibles**:
- `SOLICITAR_INFORMACION` - Marca como `OBSERVADA` (requiere respuesta)
- `APROBAR_PARA_PAGO` - Marca como `APROBADA`
- `RECHAZAR` - Marca como `RECHAZADA`

**Validaciones**:
- `observaciones`: mínimo 10 caracteres
- Estado actual debe ser `EN_AUDITORIA`

**Response 200**: `IncapacidadInDB` con nuevo estado

**Roles**: `ADMIN`, `AUDITOR`, `APROBADOR`

---

### 8.8. Aprobar Incapacidad
```http
POST /api/v1/incapacidades/{incapacidad_id}/aprobar
Authorization: Bearer <access_token>
```

**Transición**: `EN_AUDITORIA` → `APROBADA`

**Response 200**: `IncapacidadInDB`

**Roles**: `ADMIN`, `APROBADOR`

---

### 8.9. Rechazar Incapacidad
```http
POST /api/v1/incapacidades/{incapacidad_id}/rechazar
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body**:
```json
{
  "motivo": "Documentación incompleta: falta historia clínica"
}
```

**Validaciones**:
- `motivo`: mínimo 10 caracteres (obligatorio)

**Transición**: `EN_AUDITORIA` → `RECHAZADA`

**Response 200**: `IncapacidadInDB`

**Roles**: `ADMIN`, `APROBADOR`

---

### 8.10. Enviar a Pago
```http
POST /api/v1/incapacidades/{incapacidad_id}/enviar-pago
Authorization: Bearer <access_token>
```

**Transición**: `APROBADA` → `EN_PAGO`

**Efecto**: Genera automáticamente una `OrdenPago` con estado `GENERADA`

**Response 200**: `IncapacidadInDB` con `orden_pago` incluida

**Roles**: `ADMIN`

---

### 8.11. Marcar como Pagada
```http
POST /api/v1/incapacidades/{incapacidad_id}/marcar-pagada
Authorization: Bearer <access_token>
```

**Transición**: `EN_PAGO` → `PAGADA`

**Efecto**: Actualiza también la `OrdenPago` asociada a estado `PAGADA`

**Response 200**: `IncapacidadInDB`

**Roles**: `ADMIN`

---

### 8.12. Obtener Documentos de Incapacidad
```http
GET /api/v1/incapacidades/{incapacidad_id}/documentos
Authorization: Bearer <access_token>
```

**Response 200**:
```json
[
  {
    "id": "990e8400-e29b-41d4-a716-446655440000",
    "nombre_archivo": "incapacidad_medica.pdf",
    "tipo_documento": "INCAPACIDAD_MEDICA",
    "extension": "pdf",
    "tamano_bytes": 245678,
    "mime_type": "application/pdf",
    "uploaded_by": "usuario@example.com",
    "uploaded_at": "2026-01-23T08:20:00"
  }
]
```

**Roles**: Todos los autenticados

---

### 8.13. Obtener Historial de Estados
```http
GET /api/v1/incapacidades/{incapacidad_id}/historial
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `skip` (integer, default: 0)
- `limit` (integer, default: 100)

**Response 200**:
```json
[
  {
    "id": "...",
    "estado_anterior": null,
    "estado_nuevo": "RADICADA",
    "observacion": "Incapacidad radicada vía portal externo",
    "cambiado_por": "550e8400-e29b-41d4-a716-446655440000",
    "cambiado_por_nombre": "Juan Pérez",
    "created_at": "2026-01-23T08:15:00"
  },
  {
    "id": "...",
    "estado_anterior": "RADICADA",
    "estado_nuevo": "EN_AUDITORIA",
    "observacion": "Asignado a auditor María González",
    "cambiado_por": "660e8400-e29b-41d4-a716-446655440000",
    "cambiado_por_nombre": "María González",
    "created_at": "2026-01-23T09:00:00"
  }
]
```

**Roles**: Todos los autenticados

---

## 11. Documentos

### 11.1. Upload Documento
```http
POST /api/v1/documentos/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data**:
```
file: <archivo>
entity_type: "incapacidad"
entity_id: "123e4567-e89b-12d3-a456-426614174000"
tipo_documento: "INCAPACIDAD_MEDICA"
```

**Validaciones**:
- Extensiones permitidas: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.doc`, `.docx`
- Tamaño máximo: 10 MB
- Tipos de documento: `INCAPACIDAD_MEDICA`, `HISTORIA_CLINICA`, `SOPORTE_ARL`, `CEDULA`, `COMPROBANTE_PAGO`

**Response 201**:
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "nombre_archivo": "incapacidad_medica.pdf",
  "tipo_documento": "INCAPACIDAD_MEDICA",
  "extension": "pdf",
  "tamano_bytes": 245678,
  "mime_type": "application/pdf",
  "hash_md5": "5d41402abc4b2a76b9719d911017c592",
  "hash_sha256": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
  "storage_path": "incapacidades/2026/01/23/990e8400-e29b-41d4-a716-446655440000.pdf",
  "uploaded_by": "usuario@example.com",
  "uploaded_at": "2026-01-23T10:15:00"
}
```

---

### 11.2. Download Documento (Autenticado)
```http
GET /api/v1/documentos/{documento_id}/download
Authorization: Bearer <access_token>
```

**Response 200**: Blob (archivo binario)

**Headers**:
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="incapacidad_medica.pdf"
```

---

### 11.3. Download Documento Público
```http
GET /api/v1/incapacidades/{numero}/documentos/{documento_id}/download
```

**Path Parameters**:
- `numero` (string) - Número de radicación de la incapacidad
- `documento_id` (UUID) - ID del documento

**Restricciones**:
- Solo documentos de tipo `INCAPACIDAD_MEDICA`
- Debe pertenecer a la incapacidad con el número indicado

**Response 200**:
```json
{
  "url": "https://storage.example.com/temp/download?token=...",
  "expires_in": 300,
  "nombre_archivo": "incapacidad_medica.pdf",
  "tipo_documento": "INCAPACIDAD_MEDICA"
}
```

**Response 403**:
```json
{
  "detail": "Este tipo de documento no es público"
}
```

---

### 11.4. Get Download URL (Presigned)
```http
GET /api/v1/documentos/{documento_id}/download-url
Authorization: Bearer <access_token>
```

**Response 200**:
```json
{
  "url": "https://storage.example.com/temp/download?token=...",
  "expires_in": 300,
  "nombre_archivo": "incapacidad_medica.pdf",
  "tipo_documento": "INCAPACIDAD_MEDICA"
}
```

**Uso**: Generar URLs temporales sin descargar el archivo inmediatamente

---

## 14. Health Checks

### 14.1. Health Check Simple
```http
GET /api/v1/health
```

**Response 200**:
```json
{
  "status": "ok",
  "timestamp": "2026-01-23T12:00:00"
}
```

---

### 14.2. Health Check con Base de Datos
```http
GET /api/v1/health/db
```

**Response 200**:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-01-23T12:00:00"
}
```

**Response 503** (si DB no está disponible):
```json
{
  "status": "error",
  "database": "disconnected",
  "error": "Connection to database failed"
}
```

---

## Notas de Implementación

### Seguridad
- Todos los tokens JWT expiran en **15 minutos** (access token)
- Refresh tokens expiran en **7 días**
- Bloqueo automático de cuenta después de **5 intentos fallidos** de login
- Rate limiting: **100 requests/minuto** por usuario autenticado

### Performance
- Respuestas con paginación incluyen máximo **100 registros** por defecto
- Cache de catálogos (CIE-10) en Redis con TTL de **24 horas**
- URLs pre-firmadas expiran en **5 minutos**

### Auditoría
- Todas las operaciones CUD (Create, Update, Delete) generan registros en `auditoria_log`
- Cambios de estado generan registros en `historial_estado`
- Los documentos incluyen hashes MD5 y SHA256 para integridad

---

**Documentación generada automáticamente desde OpenAPI 3.1.0**  
**Última actualización**: 23 de enero de 2026
