# Definición de Endpoints REST API

## 1. Especificación General

- **Protocolo**: HTTPS
- **Base URL**: `https://api.incapacidades.com/api/v1`
- **Formato**: JSON
- **Autenticación**: JWT Bearer Token
- **Versionamiento**: URL path (`/v1`, `/v2`)
- **Rate Limiting**: 100 req/min (usuarios externos), 1000 req/min (internos)

## 2. Convenciones

### 2.1 Códigos de Respuesta HTTP

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 | OK | Operación exitosa |
| 201 | Created | Recurso creado exitosamente |
| 204 | No Content | Operación exitosa sin contenido |
| 400 | Bad Request | Error de validación |
| 401 | Unauthorized | No autenticado |
| 403 | Forbidden | Sin permisos |
| 404 | Not Found | Recurso no encontrado |
| 409 | Conflict | Conflicto (duplicado) |
| 422 | Unprocessable Entity | Error de lógica de negocio |
| 429 | Too Many Requests | Rate limit excedido |
| 500 | Internal Server Error | Error del servidor |

### 2.2 Estructura de Respuesta

**Éxito:**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2026-01-05T10:30:00Z",
    "request_id": "uuid-here"
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Error en validación de datos",
    "details": [
      {
        "field": "email",
        "message": "Email inválido"
      }
    ]
  },
  "meta": {
    "timestamp": "2026-01-05T10:30:00Z",
    "request_id": "uuid-here"
  }
}
```

### 2.3 Paginación

```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8
  }
}
```

Query params: `?page=1&page_size=20&sort_by=created_at&order=desc`

## 3. Módulo de Autenticación

### 3.1 Login

**Endpoint**: `POST /auth/login`

**Descripción**: Autenticar usuario y obtener tokens.

**Request:**
```json
{
  "username": "admin@empresa.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
      "id": "uuid",
      "username": "admin@empresa.com",
      "nombre_completo": "Juan Pérez",
      "rol": "ADMIN",
      "permisos": ["crear_incapacidad", "aprobar_incapacidad"]
    }
  }
}
```

### 3.2 Refresh Token

**Endpoint**: `POST /auth/refresh`

**Headers**: `Authorization: Bearer <refresh_token>`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 900
  }
}
```

### 3.3 Logout

**Endpoint**: `POST /auth/logout`

**Headers**: `Authorization: Bearer <access_token>`

**Response (204)**: No content

### 3.4 Cambiar Contraseña

**Endpoint**: `POST /auth/change-password`

**Request:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!",
  "confirm_password": "NewPassword456!"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Contraseña actualizada exitosamente"
  }
}
```

## 4. Módulo de Empresas

### 4.1 Listar Empresas

**Endpoint**: `GET /empresas`

**Permisos**: `ADMIN`, `AUDITOR`

**Query Params**:
- `page`: número de página (default: 1)
- `page_size`: tamaño de página (default: 20, max: 100)
- `estado`: filtro por estado (ACTIVA, INACTIVA)
- `search`: búsqueda por NIT o razón social

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "nit": "900123456-7",
      "razon_social": "Empresa ABC S.A.S",
      "estado": "ACTIVA",
      "email_contacto": "contacto@empresa.com",
      "telefono": "3001234567",
      "ciudad": "Bogotá",
      "tipo_empresa": "ARL",
      "total_empleados": 150,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

### 4.2 Obtener Empresa

**Endpoint**: `GET /empresas/{empresa_id}`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "nit": "900123456-7",
    "razon_social": "Empresa ABC S.A.S",
    "estado": "ACTIVA",
    "email_contacto": "contacto@empresa.com",
    "telefono": "3001234567",
    "direccion": "Calle 123 #45-67",
    "ciudad": "Bogotá",
    "departamento": "Cundinamarca",
    "tipo_empresa": "ARL",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z",
    "estadisticas": {
      "total_empleados": 150,
      "total_incapacidades": 85,
      "incapacidades_pendientes": 12
    }
  }
}
```

### 4.3 Crear Empresa

**Endpoint**: `POST /empresas`

**Permisos**: `ADMIN`

**Request:**
```json
{
  "nit": "900123456-7",
  "razon_social": "Empresa ABC S.A.S",
  "email_contacto": "contacto@empresa.com",
  "telefono": "3001234567",
  "direccion": "Calle 123 #45-67",
  "ciudad": "Bogotá",
  "departamento": "Cundinamarca",
  "tipo_empresa": "ARL"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "nit": "900123456-7",
    "razon_social": "Empresa ABC S.A.S",
    ...
  }
}
```

### 4.4 Actualizar Empresa

**Endpoint**: `PUT /empresas/{empresa_id}`

**Permisos**: `ADMIN`

**Request:** (campos a actualizar)
```json
{
  "email_contacto": "nuevo@empresa.com",
  "telefono": "3009876543"
}
```

**Response (200):** (empresa actualizada completa)

### 4.5 Importar Empresas (CSV/Excel)

**Endpoint**: `POST /empresas/import`

**Permisos**: `ADMIN`

**Content-Type**: `multipart/form-data`

**Request:**
```
file: empresas.csv
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_procesadas": 100,
    "exitosas": 95,
    "fallidas": 5,
    "errores": [
      {
        "linea": 10,
        "error": "NIT duplicado",
        "datos": { "nit": "900123456" }
      }
    ]
  }
}
```

## 5. Módulo de Empleados

### 5.1 Listar Empleados

**Endpoint**: `GET /empleados`

**Query Params**:
- `empresa_id`: filtro por empresa
- `estado`: ACTIVO, INACTIVO, RETIRADO
- `search`: búsqueda por nombre o documento

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "empresa": {
        "id": "uuid",
        "nit": "900123456-7",
        "razon_social": "Empresa ABC"
      },
      "numero_documento": "1234567890",
      "tipo_documento": "CC",
      "nombres": "Juan Carlos",
      "apellidos": "Pérez García",
      "email": "juan.perez@empresa.com",
      "cargo": "Desarrollador Senior",
      "estado": "ACTIVO",
      "fecha_ingreso": "2023-01-15"
    }
  ],
  "pagination": { ... }
}
```

### 5.2 Obtener Empleado

**Endpoint**: `GET /empleados/{empleado_id}`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "empresa": { ... },
    "numero_documento": "1234567890",
    "tipo_documento": "CC",
    "nombres": "Juan Carlos",
    "apellidos": "Pérez García",
    "email": "juan.perez@empresa.com",
    "telefono": "3001234567",
    "fecha_nacimiento": "1990-05-20",
    "genero": "M",
    "cargo": "Desarrollador Senior",
    "area": "Tecnología",
    "fecha_ingreso": "2023-01-15",
    "salario_base": 5000000,
    "cuenta_bancaria": "1234567890",
    "banco": "Bancolombia",
    "tipo_cuenta": "AHORROS",
    "estado": "ACTIVO",
    "estadisticas": {
      "total_incapacidades": 3,
      "dias_incapacidad_año": 15
    }
  }
}
```

### 5.3 Crear Empleado

**Endpoint**: `POST /empleados`

**Permisos**: `ADMIN`, `EMPRESA`

**Request:**
```json
{
  "empresa_id": "uuid",
  "numero_documento": "1234567890",
  "tipo_documento": "CC",
  "nombres": "Juan Carlos",
  "apellidos": "Pérez García",
  "email": "juan.perez@empresa.com",
  "telefono": "3001234567",
  "fecha_nacimiento": "1990-05-20",
  "genero": "M",
  "cargo": "Desarrollador Senior",
  "area": "Tecnología",
  "fecha_ingreso": "2023-01-15",
  "salario_base": 5000000,
  "cuenta_bancaria": "1234567890",
  "banco": "Bancolombia",
  "tipo_cuenta": "AHORROS"
}
```

**Response (201):** (empleado creado)

### 5.4 Importar Empleados

**Endpoint**: `POST /empleados/import`

**Similar a importar empresas**

## 5.5 Módulo de Afiliados

### 5.5.1 Listar Afiliados

**Endpoint**: `GET /afiliados`

**Descripción**: Listar afiliados con pólizas de salud.

**Query Params**:
- `numero_poliza`: filtro por número de póliza
- `tipo_poliza`: INDIVIDUAL, FAMILIAR, COLECTIVA
- `estado`: ACTIVO, INACTIVO, SUSPENDIDO
- `tipo_documento`: CC, CE, etc.
- `numero_documento`: filtro por documento
- `search`: búsqueda por nombre o documento

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "numero_poliza": "POL-2026-001234",
      "tipo_poliza": "INDIVIDUAL",
      "nombres": "María",
      "apellidos": "González",
      "tipo_documento": "CC",
      "numero_documento": "9876543210",
      "email": "maria.gonzalez@email.com",
      "telefono": "3001234567",
      "estado": "ACTIVO",
      "fecha_inicio_poliza": "2025-01-01",
      "fecha_fin_poliza": "2026-12-31"
    }
  ],
  "pagination": { ... }
}
```

### 5.5.2 Obtener Afiliado

**Endpoint**: `GET /afiliados/{afiliado_id}`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "numero_poliza": "POL-2026-001234",
    "tipo_poliza": "INDIVIDUAL",
    "tipo_documento": "CC",
    "numero_documento": "9876543210",
    "nombres": "María",
    "apellidos": "González",
    "email": "maria.gonzalez@email.com",
    "telefono": "3001234567",
    "fecha_nacimiento": "1985-05-15",
    "genero": "F",
    "direccion": "Calle 123 #45-67",
    "ciudad": "Bogotá",
    "departamento": "Cundinamarca",
    "fecha_inicio_poliza": "2025-01-01",
    "fecha_fin_poliza": "2026-12-31",
    "cuenta_bancaria": "1234567890",
    "banco": "Banco XYZ",
    "tipo_cuenta": "AHORROS",
    "estado": "ACTIVO",
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2025-01-01T10:00:00Z"
  }
}
```

### 5.5.3 Crear Afiliado

**Endpoint**: `POST /afiliados`

**Request:**
```json
{
  "numero_poliza": "POL-2026-001234",
  "tipo_poliza": "INDIVIDUAL",
  "tipo_documento": "CC",
  "numero_documento": "9876543210",
  "nombres": "María",
  "apellidos": "González",
  "email": "maria.gonzalez@email.com",
  "telefono": "3001234567",
  "fecha_nacimiento": "1985-05-15",
  "genero": "F",
  "direccion": "Calle 123 #45-67",
  "ciudad": "Bogotá",
  "departamento": "Cundinamarca",
  "fecha_inicio_poliza": "2025-01-01",
  "fecha_fin_poliza": "2026-12-31",
  "cuenta_bancaria": "1234567890",
  "banco": "Banco XYZ",
  "tipo_cuenta": "AHORROS"
}
```

**Response (201):** (afiliado creado)

### 5.5.4 Obtener Incapacidades de Afiliado

**Endpoint**: `GET /afiliados/{afiliado_id}/incapacidades`

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "numero": "INC-202601-SALUD-000001",
      "tipo": "SALUD",
      "fecha_inicio": "2026-01-05",
      "fecha_fin": "2026-01-08",
      "estado": "APROBADA",
      "diagnostico_cie10": "J00"
    }
  ]
}
```

## 6. Módulo de Incapacidades

### 6.1 Listar Incapacidades

**Endpoint**: `GET /incapacidades`

**Query Params**:
- `empresa_id`: filtro por empresa (solo ARL)
- `empleado_id`: filtro por empleado (solo ARL)
- `afiliado_id`: filtro por afiliado (solo SALUD)
- `estado`: RADICADA, EN_AUDITORIA, etc.
- `tipo`: ARL, SALUD
- `fecha_inicio_desde`: filtro de fecha
- `fecha_inicio_hasta`: filtro de fecha
- `search`: búsqueda por número o empleado/afiliado

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "numero": "INC-202601-000001",
      "empleado": {
        "id": "uuid",
        "nombre_completo": "Juan Carlos Pérez",
        "documento": "1234567890"
      },
      "empresa": {
        "id": "uuid",
        "razon_social": "Empresa ABC",
        "nit": "900123456-7"
      },
      "afiliado": null,
      "tipo": "ARL",
      "subtipo": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-01-01",
      "fecha_fin": "2026-01-05",
      "dias_totales": 5,
      "diagnostico_cie10": "J00",
      "descripcion_diagnostico": "Rinofaringitis aguda",
      "valor_total": 500000,
      "estado": "EN_AUDITORIA",
      "prioridad": "NORMAL",
      "fecha_radicacion": "2026-01-05T08:30:00Z",
      "radicado_por": "Juan Pérez",
      "total_documentos": 2
    }
  ],
  "pagination": { ... }
}
```

### 6.2 Obtener Incapacidad

**Endpoint**: `GET /incapacidades/{incapacidad_id}`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "numero": "INC-202601-000001",
    "empleado": { ... },
    "empresa": { ... },
    "tipo": "SALUD",
    "subtipo": "ENFERMEDAD_GENERAL",
    "fecha_inicio": "2026-01-01",
    "fecha_fin": "2026-01-05",
    "dias_totales": 5,
    "diagnostico_cie10": "J00",
    "descripcion_diagnostico": "Rinofaringitis aguda",
    "eps": "Compensar EPS",
    "ips": "IPS San Rafael",
    "valor_dia": 100000,
    "valor_total": 500000,
    "estado": "EN_AUDITORIA",
    "observaciones": null,
    "motivo_rechazo": null,
    "radicado_por": {
      "id": "uuid",
      "nombre": "Juan Pérez",
      "rol": "EMPRESA"
    },
    "auditado_por": {
      "id": "uuid",
      "nombre": "María López",
      "rol": "AUDITOR"
    },
    "aprobado_por": null,
    "fecha_radicacion": "2026-01-05T08:30:00Z",
    "fecha_auditoria": "2026-01-05T10:15:00Z",
    "fecha_aprobacion": null,
    "prioridad": "NORMAL",
    "documentos": [
      {
        "id": "uuid",
        "tipo_documento": "INCAPACIDAD_MEDICA",
        "nombre_archivo": "incapacidad_001.pdf",
        "mime_type": "application/pdf",
        "tamanio_bytes": 524288,
        "created_at": "2026-01-05T08:30:00Z",
        "download_url": "/incapacidades/uuid/documentos/uuid/download"
      }
    ],
    "historial": [
      {
        "estado_anterior": "RADICADA",
        "estado_nuevo": "EN_AUDITORIA",
        "observacion": "Iniciando revisión",
        "cambiado_por": "María López",
        "fecha": "2026-01-05T10:15:00Z"
      }
    ],
    "orden_pago": null
  }
}
```

### 6.3 Crear Incapacidad (Radicar)

**Endpoint**: `POST /incapacidades`

**Permisos**: `EMPRESA`, `EMPLEADO`, `ADMIN`, `AFILIADO`

**Request para ARL (Empleado de empresa):**
```json
{
  "tipo": "ARL",
  "empleado_id": "uuid",
  "empresa_id": "uuid",
  "siniestro_id": "uuid",
  "numero_siniestro": "SIN-202601-001",
  "subtipo": "ACCIDENTE_TRABAJO",
  "fecha_inicio": "2026-01-01",
  "fecha_fin": "2026-01-05",
  "diagnostico_cie10": "S61.0",
  "descripcion_diagnostico": "Herida en dedo",
  "eps": "Sura EPS",
  "ips": "IPS San Rafael",
  "observaciones": "Accidente en planta de producción"
}
```

**Request para SALUD (Afiliado con póliza):**
```json
{
  "tipo": "SALUD",
  "afiliado_id": "uuid",
  "subtipo": "ENFERMEDAD_GENERAL",
  "fecha_inicio": "2026-01-01",
  "fecha_fin": "2026-01-05",
  "diagnostico_cie10": "J00",
  "descripcion_diagnostico": "Rinofaringitis aguda",
  "eps": "Compensar EPS",
  "ips": "IPS Central",
  "observaciones": "Incapacidad médica por gripe"
}
```

**Validación**:
- Si `tipo=ARL`: Se requiere `empleado_id` y `empresa_id`
- Si `tipo=SALUD`: Se requiere `afiliado_id`
- No se pueden mezclar: ARL NO puede tener `afiliado_id`, SALUD NO puede tener `empleado_id`

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "numero": "INC-202601-ARL-000001",
    "estado": "RADICADA",
    ...
  }
}
```

### 6.4 Adjuntar Documentos

**Endpoint**: `POST /incapacidades/{incapacidad_id}/documentos`

**Content-Type**: `multipart/form-data`

**Request:**
```
file: incapacidad.pdf
tipo_documento: INCAPACIDAD_MEDICA
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "tipo_documento": "INCAPACIDAD_MEDICA",
    "nombre_archivo": "incapacidad_001.pdf",
    "mime_type": "application/pdf",
    "tamanio_bytes": 524288,
    "created_at": "2026-01-05T08:30:00Z"
  }
}
```

### 6.5 Descargar Documento

**Endpoint**: `GET /incapacidades/{incapacidad_id}/documentos/{documento_id}/download`

**Response (200):**
- Content-Type: según mime_type del archivo
- Content-Disposition: attachment
- Stream del archivo

### 6.6 Auditar Incapacidad

**Endpoint**: `POST /incapacidades/{incapacidad_id}/auditar`

**Permisos**: `AUDITOR`, `ADMIN`

**Request:**
```json
{
  "accion": "APROBAR_PARA_PAGO",
  "observaciones": "Documentación completa y válida"
}
```

**Acciones válidas**:
- `SOLICITAR_INFORMACION`: Cambiar a OBSERVADA
- `APROBAR_PARA_PAGO`: Cambiar a APROBADA
- `RECHAZAR`: Cambiar a RECHAZADA

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "estado": "APROBADA",
    "fecha_auditoria": "2026-01-05T14:30:00Z",
    "auditado_por": "María López"
  }
}
```

### 6.7 Responder Observaciones

**Endpoint**: `POST /incapacidades/{incapacidad_id}/responder`

**Permisos**: `EMPRESA`, `EMPLEADO`

**Request:**
```json
{
  "respuesta": "Se adjuntan documentos solicitados"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "estado": "EN_AUDITORIA"
  }
}
```

### 6.8 Generar Orden de Pago

**Endpoint**: `POST /incapacidades/{incapacidad_id}/generar-orden-pago`

**Permisos**: `ADMIN`, `AUDITOR`

**Request:**
```json
{
  "beneficiario_tipo": "EMPLEADO",
  "valor_pagar": 500000,
  "observaciones": "Pago de incapacidad aprobada"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "numero_orden": "OP-202601-000001",
    "incapacidad_id": "uuid",
    "beneficiario_tipo": "EMPLEADO",
    "beneficiario_nombre": "Juan Carlos Pérez",
    "valor_pagar": 500000,
    "estado_pago": "GENERADA",
    "fecha_generacion": "2026-01-05T15:00:00Z"
  }
}
```

### 6.9 Estadísticas de Incapacidades

**Endpoint**: `GET /incapacidades/estadisticas`

**Query Params**:
- `fecha_desde`: filtro de fecha
- `fecha_hasta`: filtro de fecha
- `empresa_id`: filtro por empresa
- `tipo`: ARL, SALUD

**Response (200):**
```json
{
  "success": true,
  "data": {
    "resumen": {
      "total_incapacidades": 150,
      "total_dias": 850,
      "valor_total": 85000000,
      "promedio_dias": 5.67
    },
    "por_estado": {
      "RADICADA": 25,
      "EN_AUDITORIA": 30,
      "OBSERVADA": 10,
      "APROBADA": 60,
      "RECHAZADA": 15,
      "PAGADA": 10
    },
    "por_tipo": {
      "ARL": 45,
      "SALUD": 105
    },
    "por_mes": [
      {
        "mes": "2026-01",
        "total": 25,
        "valor": 2500000
      }
    ],
    "top_empresas": [
      {
        "empresa": "Empresa ABC",
        "nit": "900123456",
        "total": 45,
        "valor": 4500000
      }
    ]
  }
}
```

## 7. Módulo de Órdenes de Pago

### 7.1 Listar Órdenes de Pago

**Endpoint**: `GET /ordenes-pago`

**Query Params**:
- `estado_pago`: filtro por estado
- `empresa_id`: filtro por empresa
- `fecha_desde`, `fecha_hasta`: rango de fechas

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "numero_orden": "OP-202601-000001",
      "incapacidad": {
        "numero": "INC-202601-000001",
        "empleado": "Juan Pérez"
      },
      "beneficiario_nombre": "Juan Carlos Pérez",
      "valor_pagar": 500000,
      "estado_pago": "APROBADA",
      "fecha_generacion": "2026-01-05T15:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

### 7.2 Obtener Orden de Pago

**Endpoint**: `GET /ordenes-pago/{orden_id}`

**Response (200):** (detalles completos)

### 7.3 Aprobar Orden de Pago

**Endpoint**: `POST /ordenes-pago/{orden_id}/aprobar`

**Permisos**: `ADMIN`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "estado_pago": "APROBADA"
  }
}
```

### 7.4 Registrar Pago

**Endpoint**: `POST /ordenes-pago/{orden_id}/registrar-pago`

**Request:**
```json
{
  "fecha_pago": "2026-01-06",
  "metodo_pago": "TRANSFERENCIA",
  "referencia_pago": "TRX123456789"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "estado_pago": "PAGADA",
    "fecha_pago": "2026-01-06T10:00:00Z"
  }
}
```

### 7.5 Exportar Órdenes de Pago

**Endpoint**: `GET /ordenes-pago/export`

**Query Params**:
- `formato`: CSV, EXCEL, PDF
- `fecha_desde`, `fecha_hasta`
- `estado_pago`

**Response (200):**
- Archivo descargable en formato solicitado

## 8. Módulo de Usuarios

### 8.1 Listar Usuarios

**Endpoint**: `GET /usuarios`

**Permisos**: `ADMIN`

**Response (200):** (lista de usuarios)

### 8.2 Crear Usuario

**Endpoint**: `POST /usuarios`

**Permisos**: `ADMIN`

**Request:**
```json
{
  "username": "nuevo.usuario",
  "email": "usuario@empresa.com",
  "password": "SecurePass123!",
  "nombre_completo": "Nuevo Usuario",
  "rol": "AUDITOR",
  "empleado_id": "uuid",
  "empresa_id": null
}
```

**Response (201):** (usuario creado)

### 8.3 Actualizar Usuario

**Endpoint**: `PUT /usuarios/{usuario_id}`

**Permisos**: `ADMIN`

### 8.4 Desactivar Usuario

**Endpoint**: `DELETE /usuarios/{usuario_id}`

**Permisos**: `ADMIN`

**Response (204)**: No content

## 9. Módulo de Integraciones

### 9.1 Sincronizar Empresas desde Sistema Externo

**Endpoint**: `POST /integraciones/sincronizar-empresas`

**Permisos**: `ADMIN`

**Request:**
```json
{
  "origen": "API_RRHH",
  "modo": "INCREMENTAL"
}
```

**Modos**:
- `COMPLETA`: Sincroniza todas las empresas
- `INCREMENTAL`: Solo cambios desde última sincronización

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_procesadas": 50,
    "nuevas": 10,
    "actualizadas": 35,
    "sin_cambios": 5,
    "errores": 0
  }
}
```

### 9.2 Sincronizar Empleados

**Endpoint**: `POST /integraciones/sincronizar-empleados`

**Similar a sincronizar empresas**

### 9.3 Webhook para Notificaciones

**Endpoint**: `POST /integraciones/webhook/siniestros`

**Descripción**: Recibe notificaciones de sistemas externos

**Request:**
```json
{
  "evento": "SINIESTRO_CREADO",
  "data": {
    "siniestro_id": "SIN-123",
    "empleado_documento": "1234567890",
    "fecha_siniestro": "2026-01-05",
    "tipo": "ACCIDENTE_TRABAJO"
  },
  "timestamp": "2026-01-05T10:00:00Z",
  "firma": "hash_seguridad"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Evento procesado exitosamente",
    "procesado_id": "uuid"
  }
}
```

## 10. Módulo de Reportes

### 10.1 Reporte de Incapacidades

**Endpoint**: `GET /reportes/incapacidades`

**Query Params**:
- `fecha_desde`, `fecha_hasta`: rango de fechas
- `empresa_id`: filtro por empresa
- `tipo`: ARL, SALUD
- `formato`: PDF, EXCEL, CSV

**Response (200):**
- Archivo descargable con reporte

### 10.2 Reporte de Auditoría

**Endpoint**: `GET /reportes/auditoria`

**Permisos**: `ADMIN`

**Query Params**:
- `usuario_id`: filtro por usuario
- `fecha_desde`, `fecha_hasta`
- `accion`: tipo de acción auditada

**Response (200):** (archivo de reporte)

## 11. Health Check y Monitoreo

### 11.1 Health Check

**Endpoint**: `GET /health`

**Sin autenticación**

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-05T10:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "storage": "ok"
  }
}
```

### 11.2 Métricas

**Endpoint**: `GET /metrics`

**Formato**: Prometheus

**Response (200):**
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/incapacidades"} 1234
```

## 12. Documentación Interactiva

### 12.1 Swagger UI

**Endpoint**: `GET /docs`

Interfaz interactiva OpenAPI/Swagger

### 12.2 ReDoc

**Endpoint**: `GET /redoc`

Documentación alternativa

### 12.3 OpenAPI Schema

**Endpoint**: `GET /openapi.json`

Esquema OpenAPI 3.0 en JSON
