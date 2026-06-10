# Pruebas cURL — Endpoint de Pre-Incapacidades

Comandos `curl` para probar el ciclo completo del endpoint de radicación de pre-incapacidades (ARL).  
Los datos de empleado/empresa corresponden a registros reales de la base de datos de desarrollo.

---

## Prerequisitos

```bash
# Variables de entorno reutilizables
BASE="http://localhost:8010/api/v1"

# PDF de prueba disponible en el repositorio
PDF_INCAPACIDAD="apps/backend/storage/documentos/2026/02/bae677fa-0e2a-45b7-a515-22a47e73afba.pdf"
PDF_HISTORIA="apps/backend/storage/documentos/2026/02/0815e32a-f56e-4b1e-bf7f-74c6697235b2.pdf"

# Token JWT para endpoints internos (obtener del login de Laravel)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhODQ4ZTBlOS01NDk5LTQ0ZTAtOTY2OC0yYTUzMmJkMGU2OGYiLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sIjoiQURNSU4iLCJ0b2tlbl92ZXJzaW9uIjowLCJleHAiOjE3ODExMjI4MDksImlhdCI6MTc4MTEyMTkwOSwidHlwZSI6ImFjY2VzcyJ9.7rbfEzPH0xeBVWhL0VJ-k4gEljJnXVTBq2dAMS6eP5o"
```

---

## 1. Casos Felices — Radicación

### 1.1 Accidente de trabajo — empleado con empresa (TechCorp)

Empleado real: Juan Carlos García Pérez, CC 1234567890, empresa TechCorp Colombia S.A.S. (NIT 800456789-1).  
Diagnóstico: fractura de cúbito (S52.0). Duración: 15 días.

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "juan.garcia@techcorp.co",
      "nombres": "Juan Carlos",
      "apellidos": "García Pérez",
      "telefono": "3001234567"
    },
    "empresa": {
      "nit": "800456789-1",
      "nombre": "TechCorp Colombia S.A.S."
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "1234567890",
      "nombres": "Juan Carlos",
      "apellidos": "García Pérez",
      "email": "juan.garcia@techcorp.co",
      "telefono": "3001234567"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-15",
      "fecha_fin": "2026-06-30",
      "diagnostico_cie10": "S52.0",
      "descripcion_diagnostico": "Fractura de la extremidad superior del cúbito por caída en planta",
      "nombre_medico": "Carlos Mendoza Ruiz",
      "registro_medico": "RM-45678",
      "ips": "Clínica Marly",
      "valor_dia": 150000.00,
      "observaciones": "Accidente ocurrido en línea de producción turno noche"
    }
  }' | jq .
```

**Respuesta esperada (201):**
```json
{
  "id": "<uuid>",
  "numero_radicacion": 202600001,
  "estado": "PENDIENTE",
  "mensaje": "Radicación recibida exitosamente. Será procesada en breve."
}
```

---

### 1.2 Enfermedad laboral — empleado Constructora Edificar

Empleado real: María González Pérez, CC 52123456, empresa Constructora Edificar S.A.S. (NIT 900123456-1).  
Diagnóstico: lumbago (M54.5), común en construcción. Duración: 8 días.

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "maria.gonzalez@edificar.com.co",
      "nombres": "María",
      "apellidos": "González Pérez",
      "telefono": "3101234567"
    },
    "empresa": {
      "nit": "900123456-1",
      "nombre": "Constructora Edificar S.A.S."
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "52123456",
      "nombres": "María",
      "apellidos": "González Pérez",
      "email": "maria.gonzalez@edificar.com.co",
      "telefono": "3101234567"
    },
    "incapacidad": {
      "tipo_enfermedad": "ENFERMEDAD_LABORAL",
      "fecha_inicio": "2026-06-10",
      "fecha_fin": "2026-06-18",
      "diagnostico_cie10": "M54.5",
      "descripcion_diagnostico": "Lumbago crónico por carga repetitiva de materiales",
      "nombre_medico": "Ana Patricia Rojas",
      "registro_medico": "RM-78901",
      "ips": "Centro Médico Compensar"
    }
  }' | jq .
```

**Respuesta esperada (201):** `estado: "PENDIENTE"`, nuevo `numero_radicacion` secuencial.

---

### 1.3 Accidente de trayecto — Manufacturas del Norte

Empleado real: Luis Hernández Castro, CC 8765432, empresa Manufacturas del Norte Ltda. (NIT 800987654-2).  
Diagnóstico: traumatismo superficial (T14.0). Incapacidad de 1 día (fecha_inicio = fecha_fin).

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "luis.hernandez@manufnorte.com",
      "nombres": "Luis",
      "apellidos": "Hernández Castro",
      "telefono": "3001112222"
    },
    "empresa": {
      "nit": "800987654-2",
      "nombre": "Manufacturas del Norte Ltda."
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "8765432",
      "nombres": "Luis",
      "apellidos": "Hernández Castro",
      "email": "luis.hernandez@manufnorte.com",
      "telefono": "3001112222"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRAYECTO",
      "fecha_inicio": "2026-06-20",
      "fecha_fin": "2026-06-20",
      "diagnostico_cie10": "T14.0",
      "descripcion_diagnostico": "Traumatismo leve sufrido en trayecto casa-trabajo (bus)",
      "nombre_medico": "Roberto Suárez Cano",
      "registro_medico": "RM-11223"
    }
  }' | jq .
```

**Escenario cubierto:** incapacidad de exactamente 1 día (`dias_totales = 1`), sin IPS ni `valor_dia`.

---

### 1.4 Trabajador independiente — sin empresa

El campo `empresa` se omite completamente. El sistema debe asumir trabajador independiente.  
Empleado ficticio con cédula de extranjería (CE).

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "solicitante.independiente@gmail.com",
      "nombres": "Pedro",
      "apellidos": "Quintero Arias",
      "telefono": "3209876543"
    },
    "empleado": {
      "tipo_documento": "CE",
      "numero_documento": "123456789",
      "nombres": "Pedro",
      "apellidos": "Quintero Arias",
      "email": "solicitante.independiente@gmail.com",
      "telefono": "3209876543"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-12",
      "fecha_fin": "2026-07-12",
      "diagnostico_cie10": "J06.9",
      "descripcion_diagnostico": "Infección respiratoria aguda",
      "nombre_medico": "Sandra Milena Torres",
      "registro_medico": "RM-99887",
      "ips": "Clínica Palermo",
      "observaciones": "Trabajador independiente sin empresa afiliada"
    }
  }' | jq .
```

**Escenario cubierto:** `empresa_nit` y `empresa_nombre` quedan `null` en BD; `dias_totales = 31`.

---

## 2. Subir Documentos

Los siguientes comandos asumen que la radicación anterior retornó `PRE_ID`.  
Ejecutar desde la raíz del repositorio (`/opt/apps/incapacidades_vs`).

```bash
# Guardar el ID de la pre-incapacidad radicada en el paso 1.1
PRE_ID="0956e6e5-9b1b-4a1f-be68-0fc4f090f8e6"
PRE_ID="aa03dcd3-0663-4ed1-ab0f-80d9c8f88eef"
```

### 2.1 Subir incapacidad médica (PDF)

```bash
curl -s -X POST "$BASE/pre-incapacidades/$PRE_ID/documentos" \
  -F "tipo_documento=INCAPACIDAD_MEDICA" \
  -F "file=@$PDF_INCAPACIDAD;type=application/pdf" | jq .
```

**Respuesta esperada (201):**
```json
{
  "id": "<uuid>",
  "tipo_documento": "INCAPACIDAD_MEDICA",
  "nombre_original": "bae677fa-0e2a-45b7-a515-22a47e73afba.pdf",
  "tamanio_bytes": 12345,
  "estado_subida": "OK",
  "created_at": "2026-06-10T..."
}
```

---

### 2.2 Subir historia clínica (segundo PDF)

```bash
curl -s -X POST "$BASE/pre-incapacidades/$PRE_ID/documentos" \
  -F "tipo_documento=HISTORIA_CLINICA" \
  -F "file=@$PDF_HISTORIA;type=application/pdf" | jq .
```

---

### 2.3 Subir soporte adicional con tipo_documento inválido → 422

Tipo de documento no está en la lista `[INCAPACIDAD_MEDICA, HISTORIA_CLINICA, SOPORTE_ADICIONAL]`.

```bash
curl -s -X POST "$BASE/pre-incapacidades/$PRE_ID/documentos" \
  -F "tipo_documento=CERTIFICADO_MEDICO" \
  -F "file=@$PDF_INCAPACIDAD;type=application/pdf" | jq .
```

**Respuesta esperada (422):** error de validación indicando tipo no permitido.

---

## 3. Consulta de Estado

### 3.1 Consultar pre-incapacidad existente

```bash
curl -s -X GET "$BASE/pre-incapacidades/$PRE_ID" | jq .
```

**Respuesta esperada (200):** objeto completo con `documentos[]` y `validation_inconsistencias[]`.

---

### 3.2 Consultar ID inexistente → 404

```bash
curl -s -X GET "$BASE/pre-incapacidades/00000000-0000-0000-0000-000000000000" | jq .
```

**Respuesta esperada (404):**
```json
{
  "detail": "Pre-incapacidad 00000000-0000-0000-0000-000000000000 no encontrada"
}
```

---

## 4. Validaciones de Formato — Errores Esperados (422)

### 4.1 fecha_fin anterior a fecha_inicio

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "test@empresa.co",
      "nombres": "Test",
      "apellidos": "Usuario"
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "1234567890",
      "nombres": "Carlos",
      "apellidos": "Rodríguez Jiménez"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-20",
      "fecha_fin": "2026-06-10",
      "diagnostico_cie10": "S52.0",
      "nombre_medico": "Juan Médico",
      "registro_medico": "RM-001"
    }
  }' | jq '.detail[0].msg'
```

**Respuesta esperada:** `"La fecha de fin debe ser mayor o igual a la fecha de inicio"`

---

### 4.2 tipo_documento inválido en empleado

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "test@empresa.co",
      "nombres": "Test"
    },
    "empleado": {
      "tipo_documento": "DNI",
      "numero_documento": "1234567890",
      "nombres": "Carlos",
      "apellidos": "Rodríguez"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-15",
      "fecha_fin": "2026-06-20",
      "diagnostico_cie10": "S52.0",
      "nombre_medico": "Juan Médico",
      "registro_medico": "RM-001"
    }
  }' | jq '.detail[0].msg'
```

**Respuesta esperada:** `"Tipo de documento debe ser uno de: ['CC', 'CE', 'PA', 'TI']"`

---

### 4.3 Código CIE-10 con formato inválido

Formato esperado: letra + 2 dígitos + opcionalmente `.` + 1-2 dígitos (ej. `A00`, `S52.0`).

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "test@empresa.co",
      "nombres": "Test"
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "1234567890",
      "nombres": "Carlos",
      "apellidos": "Rodríguez"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-15",
      "fecha_fin": "2026-06-20",
      "diagnostico_cie10": "LUMBAR",
      "nombre_medico": "Juan Médico",
      "registro_medico": "RM-001"
    }
  }' | jq '.detail[0].msg'
```

**Respuesta esperada:** `"Formato CIE-10 inválido (ej: A00 o A00.1)"`

---

### 4.4 NIT de empresa con formato inválido

Formato esperado: `^\d{6,15}(-\d)?$` (ej. `900123456-1` o `900123456`).

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "test@empresa.co",
      "nombres": "Test"
    },
    "empresa": {
      "nit": "ABC-123-XYZ",
      "nombre": "Empresa Inválida"
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "1234567890",
      "nombres": "Carlos",
      "apellidos": "Rodríguez"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-15",
      "fecha_fin": "2026-06-20",
      "diagnostico_cie10": "S52.0",
      "nombre_medico": "Juan Médico",
      "registro_medico": "RM-001"
    }
  }' | jq '.detail[0].msg'
```

**Respuesta esperada:** `"Formato de NIT inválido (ej: 900123456-1)"`

---

### 4.5 Teléfono del empleado con letras

La validación exige que el teléfono sea exactamente 10 dígitos numéricos.

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "test@empresa.co",
      "nombres": "Test"
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "1234567890",
      "nombres": "Carlos",
      "apellidos": "Rodríguez",
      "telefono": "300-EMPRESA"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-15",
      "fecha_fin": "2026-06-20",
      "diagnostico_cie10": "S52.0",
      "nombre_medico": "Juan Médico",
      "registro_medico": "RM-001"
    }
  }' | jq '.detail[0].msg'
```

**Respuesta esperada:** `"El teléfono solo debe contener dígitos"`

---

### 4.6 registro_medico con caracteres no permitidos

El regex `^[a-zA-Z0-9\-]+$` no permite puntos ni espacios.

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "test@empresa.co",
      "nombres": "Test"
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "1234567890",
      "nombres": "Carlos",
      "apellidos": "Rodríguez"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-15",
      "fecha_fin": "2026-06-20",
      "diagnostico_cie10": "S52.0",
      "nombre_medico": "Juan Médico",
      "registro_medico": "Dr. Médico 123"
    }
  }' | jq '.detail[0].msg'
```

**Respuesta esperada:** `"El registro médico solo permite letras, números y guiones"`

---

### 4.7 Nombres con caracteres numéricos

Los campos de nombres/apellidos solo permiten letras, espacios y guiones.

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "test@empresa.co",
      "nombres": "Carlos123",
      "apellidos": "Rodríguez"
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "1234567890",
      "nombres": "Carlos",
      "apellidos": "Rodríguez"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-15",
      "fecha_fin": "2026-06-20",
      "diagnostico_cie10": "S52.0",
      "nombre_medico": "Juan Médico",
      "registro_medico": "RM-001"
    }
  }' | jq '.detail[0].msg'
```

**Respuesta esperada:** `"Solo se permiten letras, espacios y guiones"`

---

### 4.8 Campos requeridos faltantes — sin correo del solicitante

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "nombres": "Test"
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "1234567890",
      "nombres": "Carlos",
      "apellidos": "Rodríguez"
    },
    "incapacidad": {
      "tipo_enfermedad": "ACCIDENTE_TRABAJO",
      "fecha_inicio": "2026-06-15",
      "fecha_fin": "2026-06-20",
      "diagnostico_cie10": "S52.0",
      "nombre_medico": "Juan Médico",
      "registro_medico": "RM-001"
    }
  }' | jq '{campo: .detail[0].loc, error: .detail[0].msg}'
```

**Respuesta esperada:** `loc: ["body", "solicitante", "correo"]`, tipo `missing`.

---

### 4.9 tipo_enfermedad inválido

```bash
curl -s -X POST "$BASE/pre-incapacidades/radicar" \
  -H "Content-Type: application/json" \
  -d '{
    "solicitante": {
      "correo": "test@empresa.co",
      "nombres": "Test"
    },
    "empleado": {
      "tipo_documento": "CC",
      "numero_documento": "1234567890",
      "nombres": "Carlos",
      "apellidos": "Rodríguez"
    },
    "incapacidad": {
      "tipo_enfermedad": "ENFERMEDAD_COMUN",
      "fecha_inicio": "2026-06-15",
      "fecha_fin": "2026-06-20",
      "diagnostico_cie10": "S52.0",
      "nombre_medico": "Juan Médico",
      "registro_medico": "RM-001"
    }
  }' | jq '.detail[0].msg'
```

**Respuesta esperada:** `"Tipo de enfermedad debe ser uno de: ['ACCIDENTE_TRABAJO', 'ENFERMEDAD_LABORAL', 'ACCIDENTE_TRAYECTO']"`

> **Nota ARL:** El portal externo solo acepta ARL. El campo `tipo_enfermedad` no incluye `ENFERMEDAD_COMUN` — ese tipo pertenece a SALUD, que no está habilitado en el portal público.

---

## 5. Endpoints Internos (requieren JWT)

Estos endpoints requieren un token JWT emitido por Laravel con `Authorization: Bearer <token>`.

### 5.1 Listar pre-incapacidades pendientes

```bash
curl -s -X GET "$BASE/pre-incapacidades/?estado=PENDIENTE&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.[].numero_radicacion'
```

**Respuesta esperada (200):** array de objetos `PreIncapacidadListItem` con conteo de errores/warnings.

---

### 5.2 Promover manualmente a incapacidad

Requiere que la pre-incapacidad no tenga errores de validación pendientes.

```bash
curl -s -X POST "$BASE/pre-incapacidades/$PRE_ID/promover" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq .
```

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "pre_incapacidad_id": "<uuid>",
  "incapacidad_id": "<uuid>",
  "errors": 0,
  "warnings": 2,
  "message": "Incapacidad creada exitosamente"
}
```

**Respuesta con errores de validación (200):**
```json
{
  "success": false,
  "pre_incapacidad_id": "<uuid>",
  "incapacidad_id": null,
  "errors": 1,
  "warnings": 0,
  "message": "Validación fallida"
}
```

---

### 5.3 Devolver al solicitante con motivo

El motivo debe tener al menos 20 caracteres.

```bash
curl -s -X POST "$BASE/pre-incapacidades/$PRE_ID/devolver" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "La incapacidad médica adjunta no tiene la firma del médico tratante. Por favor reenvíe el documento con la firma y sello del galeno que expidió la incapacidad."
  }' | jq .
```

**Respuesta esperada (200):**
```json
{
  "id": "<uuid>",
  "estado": "DEVUELTA",
  "motivo_devolucion": "La incapacidad médica adjunta...",
  "email_enviado": true
}
```

---

### 5.4 Devolver con motivo demasiado corto → 422

```bash
curl -s -X POST "$BASE/pre-incapacidades/$PRE_ID/devolver" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"motivo": "Falta documento"}' | jq '.detail[0].msg'
```

**Respuesta esperada:** error indicando que el motivo debe tener mínimo 20 caracteres.

---

## Resumen de cobertura

| # | Endpoint | Escenario | Código HTTP |
|---|----------|-----------|-------------|
| 1.1 | `POST /radicar` | Accidente trabajo + empresa conocida (TechCorp) | 201 |
| 1.2 | `POST /radicar` | Enfermedad laboral (Constructora Edificar) | 201 |
| 1.3 | `POST /radicar` | Accidente trayecto, 1 día (Manufacturas Norte) | 201 |
| 1.4 | `POST /radicar` | Trabajador independiente sin empresa, tipo CE | 201 |
| 2.1 | `POST /{id}/documentos` | Subir INCAPACIDAD_MEDICA (PDF) | 201 |
| 2.2 | `POST /{id}/documentos` | Subir HISTORIA_CLINICA (PDF) | 201 |
| 2.3 | `POST /{id}/documentos` | tipo_documento inválido (CERTIFICADO_MEDICO) | 422 |
| 3.1 | `GET /{id}` | Consulta de estado exitosa | 200 |
| 3.2 | `GET /{id}` | ID inexistente | 404 |
| 4.1 | `POST /radicar` | fecha_fin < fecha_inicio | 422 |
| 4.2 | `POST /radicar` | tipo_documento empleado = DNI | 422 |
| 4.3 | `POST /radicar` | CIE-10 = "LUMBAR" (formato inválido) | 422 |
| 4.4 | `POST /radicar` | NIT = "ABC-123-XYZ" | 422 |
| 4.5 | `POST /radicar` | Teléfono con letras ("300-EMPRESA") | 422 |
| 4.6 | `POST /radicar` | registro_medico con punto y espacio | 422 |
| 4.7 | `POST /radicar` | Nombres con dígitos ("Carlos123") | 422 |
| 4.8 | `POST /radicar` | Campo requerido faltante (correo) | 422 |
| 4.9 | `POST /radicar` | tipo_enfermedad SALUD no permitido | 422 |
| 5.1 | `GET /` *(JWT)* | Listar pendientes paginado | 200 |
| 5.2 | `POST /{id}/promover` *(JWT)* | Promoción manual exitosa / con errores | 200 |
| 5.3 | `POST /{id}/devolver` *(JWT)* | Devolver con motivo completo | 200 |
| 5.4 | `POST /{id}/devolver` *(JWT)* | Motivo demasiado corto | 422 |
