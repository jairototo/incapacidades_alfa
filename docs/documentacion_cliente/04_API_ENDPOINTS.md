# ENDPOINTS API

**Versión**: 1.0  
**Última Actualización**: Junio 2026  
**Propósito**: Documentación completa de todos los endpoints REST de la API

---

## 1. INTRODUCCIÓN

### 1.1 Base URL

```
Desarrollo:    http://localhost:8010/api/v1
Producción:    https://api.aseguradora.com/api/v1
```

### 1.2 Autenticación

Todos los endpoints (excepto `POST /auth/login` y `GET /incapacidades/consultar`) requieren token JWT en header:

```bash
Authorization: Bearer <token_jwt>
```

**Ejemplo**:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     http://localhost:8010/api/v1/incapacidades
```

### 1.3 Formatos

- **Content-Type**: `application/json`
- **Respuesta**: JSON
- **Fechas**: ISO 8601 (`YYYY-MM-DD` o `YYYY-MM-DDTHH:mm:ss.sssZ`)
- **UUID**: Formato estándar (`550e8400-e29b-41d4-a716-446655440000`)

### 1.4 Estados HTTP

| Código | Significado | Ejemplo |
|--------|------------|---------|
| 200 | OK | GET exitoso |
| 201 | Created | POST exitoso (recurso creado) |
| 204 | No Content | DELETE exitoso |
| 400 | Bad Request | Validación fallida |
| 401 | Unauthorized | Token inválido/ausente |
| 403 | Forbidden | Rol insuficiente |
| 404 | Not Found | Recurso no existe |
| 409 | Conflict | Constraintviolation (ej: número radicado único) |
| 500 | Server Error | Error interno |

### 1.5 Paginación

Para endpoints con lista de resultados:

```
?skip=0&limit=20
```

**Respuesta**:
```json
{
  "total": 150,
  "skip": 0,
  "limit": 20,
  "items": [...]
}
```

---

## 2. MÓDULO: AUTENTICACIÓN

### 2.1 Login

**Endpoint**: `POST /auth/login`

**Autenticación**: NO requerida

**Parámetros**:
```json
{
  "email": "usuario@aseguradora.com",
  "password": "contraseña123"
}
```

**Respuesta** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "usuario@aseguradora.com",
    "nombre": "Juan Pérez",
    "rol": "AUDITOR",
    "activo": true
  }
}
```

**Errores**:
- **401 Unauthorized**: Email o contraseña incorrectos
- **423 Locked**: Cuenta bloqueada (5 intentos fallidos)

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8010/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@aseguradora.com",
    "password": "contraseña123"
  }'
```

---

### 2.2 Logout

**Endpoint**: `POST /auth/logout`

**Autenticación**: SÍ (JWT)

**Parámetros**: Ninguno

**Respuesta** (200 OK):
```json
{
  "mensaje": "Logout exitoso"
}
```

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8010/api/v1/auth/logout \
  -H "Authorization: Bearer <token>"
```

---

### 2.3 Refresh Token

**Endpoint**: `POST /auth/refresh`

**Autenticación**: Refresh token en body

**Parámetros**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Respuesta** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errores**:
- **401 Unauthorized**: Refresh token inválido/expirado

---

### 2.4 Cambiar Contraseña

**Endpoint**: `PUT /auth/cambiar-password`

**Autenticación**: SÍ (JWT)

**Parámetros**:
```json
{
  "password_actual": "antigua123",
  "password_nueva": "nueva456"
}
```

**Respuesta** (200 OK):
```json
{
  "mensaje": "Contraseña actualizada exitosamente"
}
```

**Errores**:
- **400 Bad Request**: Contraseña actual incorrecta

---

### 2.5 Logout de Todas las Sesiones

**Endpoint**: `POST /auth/logout-all`

**Autenticación**: SÍ (JWT)

**Parámetros**: Ninguno

**Respuesta** (200 OK):
```json
{
  "mensaje": "Sesiones cerradas"
}
```

---

## 3. MÓDULO: RADICACIÓN (INCAPACIDADES)

### 3.1 Radicar Incapacidad

**Endpoint**: `POST /incapacidades/radicar`

**Autenticación**: SÍ (JWT) — Rol: EMPRESA, EMPLEADO, ADMIN

**Parámetros**:
```json
{
  "tipo": "ARL",
  "empleado_id": "550e8400-e29b-41d4-a716-446655440001",
  "empresa_id": "550e8400-e29b-41d4-a716-446655440002",
  "fecha_inicio": "2026-06-01",
  "fecha_fin": "2026-06-15",
  "diagnostico_cie10": "M79.3",
  "descripcion_diagnostico": "Tendinitis crónica mano derecha",
  "nombre_medico": "Dr. Carlos López",
  "registro_medico": "RM-12345",
  "eps": "Famisanar",
  "ips": "Clínica Mayor",
  "valor_dia": 50000.00,
  "documentos_ids": [
    "550e8400-e29b-41d4-a716-446655440010",
    "550e8400-e29b-41d4-a716-446655440011"
  ]
}
```

**Respuesta** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "numero": "202606001234",
  "tipo": "ARL",
  "estado": "RADICADA",
  "empleado_id": "550e8400-e29b-41d4-a716-446655440001",
  "empresa_id": "550e8400-e29b-41d4-a716-446655440002",
  "fecha_inicio": "2026-06-01",
  "fecha_fin": "2026-06-15",
  "dias_totales": 15,
  "valor_total": 750000.00,
  "diagnostico_cie10": "M79.3",
  "creado_en": "2026-06-03T10:30:00Z",
  "actualizado_en": "2026-06-03T10:30:00Z"
}
```

**Errores**:
- **400 Bad Request**: Validación fallida (RN-001 a RN-020)
- **409 Conflict**: Tipo ARL pero sin empleado_id

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8010/api/v1/incapacidades/radicar \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "ARL",
    "empleado_id": "550e8400-e29b-41d4-a716-446655440001",
    ...
  }'
```

---

### 3.2 Obtener Incapacidad por ID

**Endpoint**: `GET /incapacidades/{id}`

**Autenticación**: SÍ (JWT)

**Parámetros de ruta**:
- `id`: UUID de la incapacidad

**Respuesta** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "numero": "202606001234",
  "tipo": "ARL",
  "estado": "EN_AUDITORIA",
  "empleado": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "nombre": "Juan Pérez",
    "documento": "1234567890",
    "empresa_id": "550e8400-e29b-41d4-a716-446655440002"
  },
  "empresa": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "nombre": "Constructora XYZ",
    "nit": "900123456"
  },
  "documentos": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "nombre": "certificado_medico.pdf",
      "tipo": "CERTIFICADO_MEDICO",
      "tamanio": 245678,
      "hash_md5": "abc123def456...",
      "url_descarga": "https://api.aseguradora.com/api/v1/documentos/550e8400-e29b-41d4-a716-446655440010/descargar"
    }
  ],
  "historial_estado": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440050",
      "estado_anterior": "RADICADA",
      "estado_nuevo": "EN_AUDITORIA",
      "razon": "Auditor asignado",
      "cambiado_por_id": "550e8400-e29b-41d4-a716-446655440005",
      "cambiado_en": "2026-06-03T11:00:00Z"
    }
  ],
  "fecha_inicio": "2026-06-01",
  "fecha_fin": "2026-06-15",
  "diagnostico_cie10": "M79.3",
  "creado_en": "2026-06-03T10:30:00Z"
}
```

**Errores**:
- **404 Not Found**: Incapacidad no existe

---

### 3.3 Listar Incapacidades

**Endpoint**: `GET /incapacidades`

**Autenticación**: SÍ (JWT)

**Query Parameters**:
- `skip`: Offset (default: 0)
- `limit`: Límite de resultados (default: 20, max: 100)
- `estado`: Filtrar por estado (RADICADA, EN_AUDITORIA, APROBADA, PAGADA, RECHAZADA)
- `tipo`: Filtrar por tipo (ARL, SALUD)
- `empresa_id`: Filtrar por empresa (UUID)
- `fecha_inicio_desde`: Filtrar incapacidades desde esta fecha (YYYY-MM-DD)
- `fecha_inicio_hasta`: Filtrar incapacidades hasta esta fecha
- `sort_by`: Campo para ordenar (numero, fecha_inicio, creado_en)
- `sort_order`: ASC o DESC

**Ejemplo URL**:
```
GET /incapacidades?estado=EN_AUDITORIA&skip=0&limit=20&sort_by=fecha_inicio&sort_order=DESC
```

**Respuesta** (200 OK):
```json
{
  "total": 45,
  "skip": 0,
  "limit": 20,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "numero": "202606001234",
      "tipo": "ARL",
      "estado": "EN_AUDITORIA",
      "empleado_nombre": "Juan Pérez",
      "empresa_nombre": "Constructora XYZ",
      "fecha_inicio": "2026-06-01",
      "fecha_fin": "2026-06-15",
      "dias_totales": 15,
      "valor_total": 750000.00,
      "creado_en": "2026-06-03T10:30:00Z"
    },
    ...
  ]
}
```

---

### 3.4 Actualizar Incapacidad

**Endpoint**: `PATCH /incapacidades/{id}`

**Autenticación**: SÍ (JWT) — Rol: ADMIN

**Parámetros**:
```json
{
  "descripcion_diagnostico": "Actualizado",
  "nombre_medico": "Dr. nuevo"
}
```

**Respuesta** (200 OK): Incapacidad actualizada

**Errores**:
- **400 Bad Request**: Campo no puede ser modificado
- **409 Conflict**: Cambio de estado inválido

---

### 3.5 Auditar Incapacidad (Cambiar Estado)

**Endpoint**: `PATCH /incapacidades/{id}/auditar`

**Autenticación**: SÍ (JWT) — Rol: AUDITOR

**Parámetros**:
```json
{
  "nuevo_estado": "APROBADA",
  "observaciones": "Documentación completa y válida"
}
```

**Estados válidos** en respuesta:
- De RADICADA → EN_AUDITORIA
- De EN_AUDITORIA → {OBSERVADA, APROBADA, RECHAZADA}
- De OBSERVADA → EN_AUDITORIA (después de correcciones)

**Respuesta** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "numero": "202606001234",
  "estado": "APROBADA",
  "historial_estado": [
    {
      "estado_anterior": "EN_AUDITORIA",
      "estado_nuevo": "APROBADA",
      "razon": "Documentación completa y válida",
      "cambiado_por": "auditor@aseguradora.com",
      "cambiado_en": "2026-06-03T14:00:00Z"
    }
  ]
}
```

**Errores**:
- **400 Bad Request**: Transición de estado inválida
- **409 Conflict**: No cumple condiciones para cambio

---

### 3.6 Observar Incapacidad

**Endpoint**: `PATCH /incapacidades/{id}/observar`

**Autenticación**: SÍ (JWT) — Rol: AUDITOR

**Parámetros**:
```json
{
  "observaciones": [
    "Certificado médico vencido",
    "Falta firma del empleador"
  ],
  "prioridad": "ALTA"
}
```

**Respuesta** (200 OK): Incapacidad con estado OBSERVADA

---

### 3.7 Rechazar Incapacidad

**Endpoint**: `PATCH /incapacidades/{id}/rechazar`

**Autenticación**: SÍ (JWT) — Rol: AUDITOR, ADMIN

**Parámetros**:
```json
{
  "motivo_rechazo": "Documentación incompleta y no corregible",
  "detalles": "Falta certificado de afiliación"
}
```

**Respuesta** (200 OK): Incapacidad con estado RECHAZADA

---

### 3.8 Consulta Pública (Sin Autenticación)

**Endpoint**: `GET /incapacidades/consultar`

**Autenticación**: NO requerida

**Query Parameters**:
- `numero_radicado`: Número generado al radicar (AAAAMMNNNNNN) — REQUERIDO
- `documento_solicitante`: Documento de quién radicó (opcional, para adicional validación)

**Ejemplo**:
```
GET /incapacidades/consultar?numero_radicado=202606001234
```

**Respuesta** (200 OK):
```json
{
  "numero_radicado": "202606001234",
  "estado": "EN_PAGO",
  "tipo": "ARL",
  "fecha_radicacion": "2026-06-03T10:30:00Z",
  "fecha_inicio_incapacidad": "2026-06-01",
  "fecha_fin_incapacidad": "2026-06-15",
  "dias_totales": 15,
  "estado_pago": "EN_PROCESO",
  "mensaje_estado": "Su incapacidad está en proceso de pago. Número de orden: OP-2026-001"
}
```

**Errores**:
- **404 Not Found**: Número radicado no existe
- **400 Bad Request**: Parámetros inválidos

**Ejemplo cURL**:
```bash
curl "http://localhost:8010/api/v1/incapacidades/consultar?numero_radicado=202606001234"
```

---

## 4. MÓDULO: AUDITORÍA

### 4.1 Listar Incapacidades Pendientes de Auditoría

**Endpoint**: `GET /incapacidades?estado=EN_AUDITORIA`

**Autenticación**: SÍ — Rol: AUDITOR

**Respuesta**: Lista filtrada (ver 3.3)

---

### 4.2 Obtener Datos Aprobados (Auditoría)

**Endpoint**: `GET /incapacidades/{id}/datos-aprobados`

**Autenticación**: SÍ — Rol: AUDITOR, ADMIN

**Respuesta** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440200",
  "incapacidad_id": "550e8400-e29b-41d4-a716-446655440100",
  "datos_aprobados": {
    "nombre_beneficiario": "Juan Pérez",
    "documento_beneficiario": "1234567890",
    "valor_aprobado": 750000.00,
    "dias_aprobados": 15,
    "fecha_aprobacion": "2026-06-03T14:00:00Z"
  },
  "aprobado_por": "auditor@aseguradora.com",
  "aprobado_en": "2026-06-03T14:00:00Z"
}
```

---

## 5. MÓDULO: APROBACIÓN Y PAGO

### 5.1 Crear Orden de Pago

**Endpoint**: `POST /ordenes-pago`

**Autenticación**: SÍ — Rol: ADMIN

**Parámetros**:
```json
{
  "incapacidad_id": "550e8400-e29b-41d4-a716-446655440100",
  "monto_total": 750000.00,
  "monto_neto": 675000.00,
  "detalles_descuentos": [
    {
      "concepto": "Impuesto retenido",
      "valor": 75000.00
    }
  ]
}
```

**Respuesta** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440300",
  "numero_orden": "OP-2026-00001",
  "incapacidad_id": "550e8400-e29b-41d4-a716-446655440100",
  "estado": "GENERADA",
  "monto_total": 750000.00,
  "monto_neto": 675000.00,
  "creado_en": "2026-06-03T15:00:00Z"
}
```

---

### 5.2 Aprobar Orden de Pago

**Endpoint**: `PATCH /ordenes-pago/{id}/aprobar`

**Autenticación**: SÍ — Rol: APROBADOR

**Parámetros**:
```json
{
  "observaciones": "Aprobado para pago inmediato"
}
```

**Respuesta** (200 OK): Orden con estado APROBADA

---

### 5.3 Procesar Pago

**Endpoint**: `PATCH /ordenes-pago/{id}/pagar`

**Autenticación**: SÍ — Rol: ADMIN, PAGADOR

**Parámetros**:
```json
{
  "metodo_pago": "TRANSFERENCIA_BANCARIA",
  "banco": "Banco Bogotá",
  "cuenta": "123456789",
  "numero_comprobante": "REF-2026-001"
}
```

**Respuesta** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440300",
  "numero_orden": "OP-2026-00001",
  "estado": "PAGADA",
  "monto_pagado": 675000.00,
  "fecha_pago": "2026-06-03T16:00:00Z",
  "comprobante": "REF-2026-001"
}
```

---

### 5.4 Listar Órdenes de Pago

**Endpoint**: `GET /ordenes-pago`

**Autenticación**: SÍ

**Query Parameters**:
- `estado`: GENERADA, APROBADA, EN_PROCESO, PAGADA, ANULADA
- `skip`, `limit`: Paginación

---

## 6. MÓDULO: CATÁLOGOS Y REFERENCIA

### 6.1 Obtener Catálogo CIE-10

**Endpoint**: `GET /catalogos/cie10`

**Autenticación**: SÍ

**Query Parameters**:
- `codigo`: Código CIE-10 a buscar (ej: M79.3)
- `descripcion`: Búsqueda por descripción (ej: Tendinitis)
- `skip`, `limit`: Paginación

**Respuesta** (200 OK):
```json
{
  "total": 1,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440400",
      "codigo": "M79.3",
      "descripcion": "Paniculitis, no clasificada en otro lugar",
      "capitulo": "XIII",
      "activo": true
    }
  ]
}
```

---

### 6.2 Obtener Municipios

**Endpoint**: `GET /catalogos/municipios`

**Autenticación**: SÍ

**Query Parameters**:
- `departamento_id`: Filtrar por departamento
- `nombre`: Búsqueda por nombre

**Respuesta** (200 OK):
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440500",
      "nombre": "Bogotá D.C.",
      "codigo_dane": "11001",
      "departamento": "Cundinamarca"
    }
  ]
}
```

---

## 7. MÓDULO: DOCUMENTOS

### 7.1 Subir Documento

**Endpoint**: `POST /documentos/subir`

**Autenticación**: SÍ (JWT)

**Content-Type**: `multipart/form-data`

**Parámetros**:
- `archivo`: Archivo binario (PDF, PNG, JPG — max 10MB)
- `tipo`: CERTIFICADO_MEDICO, SINIESTRO, FOTOCOPIAS, OTRO
- `descripcion`: Descripción libre (opcional)

**Respuesta** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "nombre_original": "certificado_medico.pdf",
  "nombre_almacenado": "550e8400-e29b-41d4-a716-446655440010.pdf",
  "tipo": "CERTIFICADO_MEDICO",
  "tamanio": 245678,
  "hash_md5": "abc123def456ghi789jkl",
  "hash_sha256": "xyzabc123...",
  "url_descarga": "https://api.aseguradora.com/api/v1/documentos/550e8400-e29b-41d4-a716-446655440010/descargar",
  "creado_en": "2026-06-03T10:30:00Z"
}
```

**Errores**:
- **400 Bad Request**: Archivo inválido/demasiado grande
- **415 Unsupported Media Type**: Tipo de archivo no soportado

**Ejemplo cURL**:
```bash
curl -X POST http://localhost:8010/api/v1/documentos/subir \
  -H "Authorization: Bearer <token>" \
  -F "archivo=@certificado_medico.pdf" \
  -F "tipo=CERTIFICADO_MEDICO" \
  -F "descripcion=Certificado de incapacidad médica"
```

---

### 7.2 Descargar Documento

**Endpoint**: `GET /documentos/{id}/descargar`

**Autenticación**: SÍ (JWT)

**Respuesta** (200 OK): Archivo binario con headers:
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="certificado_medico.pdf"
```

---

### 7.3 Obtener URL Presignada (MinIO)

**Endpoint**: `GET /documentos/{id}/url-presignada`

**Autenticación**: SÍ (JWT)

**Query Parameters**:
- `expiracion_minutos`: Minutos que la URL es válida (default: 15)

**Respuesta** (200 OK):
```json
{
  "url": "https://minio.aseguradora.com/incapacidades/550e8400-e29b-41d4-a716-446655440010.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&...",
  "expira_en": 900
}
```

---

### 7.4 Eliminar Documento

**Endpoint**: `DELETE /documentos/{id}`

**Autenticación**: SÍ — Rol: ADMIN, propietario

**Respuesta** (204 No Content)

---

## 8. MÓDULO: EMPRESAS

### 8.1 Crear Empresa

**Endpoint**: `POST /empresas`

**Autenticación**: SÍ — Rol: ADMIN

**Parámetros**:
```json
{
  "nombre": "Constructora XYZ S.A.",
  "nit": "900123456",
  "direccion": "Cra 50 #12-34, Bogotá",
  "telefono": "+57-1-1234567",
  "email": "contacto@constructora.com",
  "tipo_afiliacion": "ARL",
  "poliza_numero": "POL-ARL-123456"
}
```

**Respuesta** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "nombre": "Constructora XYZ S.A.",
  "nit": "900123456",
  ...
}
```

---

### 8.2 Listar Empresas

**Endpoint**: `GET /empresas`

**Autenticación**: SÍ

**Query Parameters**:
- `nombre`: Búsqueda por nombre
- `nit`: Búsqueda por NIT
- `skip`, `limit`: Paginación

---

### 8.3 Obtener Empresa por ID

**Endpoint**: `GET /empresas/{id}`

**Autenticación**: SÍ

---

## 9. MÓDULO: EMPLEADOS

### 9.1 Crear Empleado

**Endpoint**: `POST /empleados`

**Autenticación**: SÍ — Rol: ADMIN, EMPRESA

**Parámetros**:
```json
{
  "empresa_id": "550e8400-e29b-41d4-a716-446655440002",
  "nombre": "Juan Pérez González",
  "documento": "1234567890",
  "email": "juan.perez@email.com",
  "cargo": "Supervisor de obra",
  "salario": 2500000.00,
  "tipo_contrato": "INDEFINIDO"
}
```

**Respuesta** (201 Created)

---

### 9.2 Listar Empleados

**Endpoint**: `GET /empleados`

**Query Parameters**:
- `empresa_id`: Filtrar por empresa
- `nombre`: Búsqueda por nombre
- `documento`: Búsqueda por documento
- `skip`, `limit`

---

### 9.3 Importación Masiva de Empleados

**Endpoint**: `POST /empleados/importar`

**Content-Type**: `multipart/form-data`

**Parámetros**:
- `archivo`: CSV con columnas: nombre, documento, cargo, salario, email
- `empresa_id`: UUID de la empresa

**Respuesta** (202 Accepted):
```json
{
  "tarea_id": "550e8400-e29b-41d4-a716-446655440600",
  "total_registros": 150,
  "estado": "EN_PROCESO",
  "url_monitor": "/api/v1/tareas/550e8400-e29b-41d4-a716-446655440600"
}
```

---

## 10. MÓDULO: AFILIADOS

### 10.1 Crear Afiliado

**Endpoint**: `POST /afiliados`

**Autenticación**: SÍ — Rol: ADMIN

**Parámetros**:
```json
{
  "nombre": "María González López",
  "documento": "0987654321",
  "email": "maria.gonzalez@email.com",
  "poliza_numero": "POL-SALUD-789456",
  "eps": "Famisanar",
  "tipo_afiliado": "TITULAR"
}
```

**Respuesta** (201 Created)

---

### 10.2 Listar Afiliados

**Endpoint**: `GET /afiliados`

**Query Parameters**:
- `poliza_numero`: Filtrar por póliza
- `eps`: Filtrar por EPS
- `documento`: Búsqueda por documento
- `skip`, `limit`

---

## 11. MÓDULO: USUARIOS (ADMINISTRACIÓN)

### 11.1 Listar Usuarios

**Endpoint**: `GET /usuarios`

**Autenticación**: SÍ — Rol: ADMIN

**Query Parameters**:
- `rol`: Filtrar por rol
- `activo`: true/false
- `email`: Búsqueda

---

### 11.2 Crear Usuario

**Endpoint**: `POST /usuarios`

**Autenticación**: SÍ — Rol: ADMIN

**Parámetros**:
```json
{
  "email": "nuevo.usuario@aseguradora.com",
  "nombre": "Nuevo Usuario",
  "rol": "AUDITOR",
  "password_temporal": "TempPass123!",
  "activo": true
}
```

**Respuesta** (201 Created): Usuario creado

---

### 11.3 Bloquear/Desbloquear Usuario

**Endpoint**: `PATCH /usuarios/{id}/bloquear`

**Autenticación**: SÍ — Rol: ADMIN

**Parámetros**:
```json
{
  "bloqueado": true,
  "motivo": "Demasiados intentos fallidos"
}
```

---

### 11.4 Resetear Contraseña

**Endpoint**: `PATCH /usuarios/{id}/resetear-password`

**Autenticación**: SÍ — Rol: ADMIN

**Respuesta**:
```json
{
  "password_temporal": "NewTemp123!",
  "mensaje": "Contraseña temporal generada. El usuario debe cambiarla en el próximo login."
}
```

---

## 12. MÓDULO: HISTORIAL DE ESTADOS

### 12.1 Obtener Historial de Estados

**Endpoint**: `GET /historial-estado?entidad_tipo=INCAPACIDAD&entidad_id={id}`

**Autenticación**: SÍ

**Query Parameters**:
- `entidad_tipo`: INCAPACIDAD, ORDEN_PAGO, SINIESTRO
- `entidad_id`: UUID de la entidad
- `skip`, `limit`: Paginación

**Respuesta** (200 OK):
```json
{
  "total": 5,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440050",
      "estado_anterior": "RADICADA",
      "estado_nuevo": "EN_AUDITORIA",
      "razon": "Auditor asignado",
      "cambiado_por": "auditor@aseguradora.com",
      "cambiado_en": "2026-06-03T11:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440051",
      "estado_anterior": "EN_AUDITORIA",
      "estado_nuevo": "APROBADA",
      "razon": "Documentación completa y válida",
      "cambiado_por": "auditor@aseguradora.com",
      "cambiado_en": "2026-06-03T14:00:00Z"
    }
  ]
}
```

---

## 13. CÓDIGOS DE ERROR

### 13.1 Errores Comunes

| Código | Error | Solución |
|--------|-------|----------|
| 401 | Unauthorized | Verifica token JWT, puede estar expirado |
| 403 | Forbidden | Tu rol no tiene permiso, contacta admin |
| 400 | Bad Request | Revisa parámetros, formato de datos |
| 409 | Conflict | Recurso ya existe o está en estado inválido |
| 404 | Not Found | Recurso no existe |
| 500 | Internal Server Error | Error en servidor, reporta a soporte |

### 13.2 Estructura de Errores

```json
{
  "detail": "Descripción del error",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-06-03T10:30:00Z",
  "path": "/api/v1/incapacidades/radicar",
  "method": "POST"
}
```

---

## 14. EJEMPLOS COMPLETOS DE FLUJOS

### 14.1 Flujo Completo: Radicación de Incapacidad

```bash
# 1. Login
curl -X POST http://localhost:8010/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@aseguradora.com","password":"xxx"}'

# Response: {access_token: "...", refresh_token: "..."}

# 2. Subir documento
curl -X POST http://localhost:8010/api/v1/documentos/subir \
  -H "Authorization: Bearer <access_token>" \
  -F "archivo=@certificado.pdf" \
  -F "tipo=CERTIFICADO_MEDICO"

# Response: {id: "550e8400-...", ...}

# 3. Radicar incapacidad
curl -X POST http://localhost:8010/api/v1/incapacidades/radicar \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "ARL",
    "empleado_id": "...",
    "empresa_id": "...",
    "fecha_inicio": "2026-06-01",
    "fecha_fin": "2026-06-15",
    "diagnostico_cie10": "M79.3",
    "documentos_ids": ["550e8400-..."]
  }'

# Response: {numero: "202606001234", id: "...", estado: "RADICADA"}

# 4. Consultar públicamente
curl "http://localhost:8010/api/v1/incapacidades/consultar?numero_radicado=202606001234"

# Response: {numero_radicado: "202606001234", estado: "RADICADA", ...}
```

---

**Total de Endpoints**: 50+ endpoints cubriendo todos los módulos del sistema

**Última revisión**: Junio 2026
