# Validaciones Completas - Sistema de Gestión de Incapacidades

**Versión**: 2.0  
**Fecha**: Junio 2026  
**Clasificación**: Técnico

---

## Tabla de Contenidos

1. [Validaciones de Solicitud/Radicación](#validaciones-de-solicitudradicación)
2. [Validaciones de Datos Personales](#validaciones-de-datos-personales)
3. [Validaciones de Datos Médicos](#validaciones-de-datos-médicos)
4. [Validaciones de Datos Financieros](#validaciones-de-datos-financieros)
5. [Validaciones de Documentos](#validaciones-de-documentos)
6. [Validaciones de Usuarios](#validaciones-de-usuarios)
7. [Validaciones de Transición de Estado](#validaciones-de-transición-de-estado)

---

## Validaciones de Solicitud/Radicación

### V-RAD-001 - Campos Requeridos en Radicación

| Campo | Tipo | Mínimo | Máximo | Obligatorio | Validación adicional |
|-------|------|--------|--------|------------|----------------------|
| solicitante_nombres | String | 2 | 100 | SÍ | Solo letras, espacios, acentos, guiones |
| solicitante_apellidos | String | 2 | 100 | SÍ | Solo letras, espacios, acentos, guiones |
| solicitante_correo | Email | 6 | 255 | SÍ | RFC 5322, único |
| solicitante_telefono | String | 10 | 20 | NO | Solo dígitos + (+ países) |
| tipo | Enum | - | - | SÍ | ARL, SALUD |
| empresa_nit | String | 10 | 20 | SÍ si ARL | Formato: XXXXXXXXXX-D |
| empleado_tipo_documento | Enum | - | - | SÍ si ARL | CC, CE, TI, PASAPORTE, PEP |
| empleado_numero_documento | String | 5 | 20 | SÍ si ARL | Según tipo |
| afiliado_numero_poliza | String | 5 | 50 | SÍ si SALUD | Alfanumérico único |
| fecha_inicio | Date | - | - | SÍ | <= fecha_fin, <= HOY |
| fecha_fin | Date | - | - | SÍ | >= fecha_inicio, <= HOY |
| diagnostico_cie10 | String | 5 | 10 | SÍ | Formato: A12.3, debe existir en catálogo |
| nombre_medico | String | 3 | 200 | SÍ | Solo alfanuméricos + espacios |
| registro_medico | String | 3 | 50 | SÍ | Formato: RM/TP+ números |

### V-RAD-002 - Validación de Rangos de Fecha

- `fecha_inicio` debe ser <= HOY (no futuro)
- `fecha_fin` debe ser <= HOY
- `fecha_inicio` <= `fecha_fin`
- Diferencia máxima: 365 días (excepto ADMIN override)
- Formato: ISO 8601 (YYYY-MM-DD)

### V-RAD-003 - Cálculo de Días

```
dias_totales = (fecha_fin - fecha_inicio).days + 1

Validación:
- dias_totales >= 1
- dias_totales <= 365
```

### V-RAD-004 - Tipos de Enfermedad Permitidos

Válido solo si `tipo = ARL`:
- ACCIDENTE_TRABAJO
- ENFERMEDAD_LABORAL
- ACCIDENTE_TRAYECTO

---

## Validaciones de Datos Personales

### V-PER-001 - Validación de Nombres y Apellidos

```regex
^[a-zA-ZáéíóúñÁÉÍÓÚÑ\s\-']{2,100}$
```

**Reglas**:
- Caracteres: a-z, A-Z, acentos, espacios, guiones, apóstrofos
- Mínimo: 2 caracteres
- Máximo: 100 caracteres
- NO permitido: números, caracteres especiales (excepto -)

### V-PER-002 - Validación de Email

```regex
^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```

**Reglas**:
- Formato RFC 5322 (simplificado)
- Mínimo: 6 caracteres
- Máximo: 255 caracteres
- Debe ser único en su tabla
- No permitido: espacios, caracteres de control

### V-PER-003 - Validación de Teléfono

```regex
^(\+\d{1,3})?[\d\s\-\(\)]{10,20}$
```

**Reglas**:
- Formato: +57 XXXXXXXXXX o (57) 1 XXXXXXX o 10-20 dígitos
- Permitido: dígitos, espacios, guiones, paréntesis, +
- Mínimo: 10 caracteres
- Máximo: 20 caracteres

### V-PER-004 - Validación de Documento de Identidad

| Tipo | Formato | Mínimo | Máximo | Regex | Ejemplo |
|------|---------|--------|--------|-------|---------|
| CC | Dígitos | 5 | 10 | `^\d{5,10}$` | 1234567890 |
| CE | Dígitos | 6 | 10 | `^\d{6,10}$` | 123456789 |
| TI | Dígitos | 8 | 10 | `^\d{8,10}$` | 12345678 |
| PASAPORTE | Alfanumérico | 6 | 20 | `^[A-Z0-9]{6,20}$` | AB123456 |
| PEP | Dígitos | 6 | 10 | `^\d{6,10}$` | 123456 |

### V-PER-005 - Validación de Género

Valores permitidos:
- M (Masculino)
- F (Femenino)
- O (Otro)

### V-PER-006 - Validación de Fecha de Nacimiento

**Reglas**:
- NO puede ser futura
- NO puede ser anterior a 1920
- Edad mínima: 16 años (para empleados activos)
- Formato: YYYY-MM-DD

---

## Validaciones de Datos Médicos

### V-MED-001 - Validación de Código CIE-10

**Formato**: `^[A-Z]\d{2}[0-9X]$` (estándar colombiano — Resolución 1273 / cuarto carácter; sin punto separador)  
**Ejemplos válidos**:
- M545 (dorsalgia)
- A048 (otras enfermedades intestinales bacterianas)
- A09X (cuarto carácter "X" de relleno, sin subcategoría)

**Validaciones**:
- Debe existir en CATALOGO_CIE10
- CATALOGO_CIE10.activo = true (si no, advertencia)
- Si no existe: ERROR - rechazar radicación

### V-MED-002 - Validación de Registro Médico

**Formato**: `^[A-Z]{2}\d{4,8}$`  
**Ejemplos**:
- RM12345 (Registro Médico)
- TP987654 (Tarjeta Profesional)

**Validaciones**:
- Mínimo: 4 dígitos después de prefijo
- Máximo: 8 dígitos
- Prefijo obligatorio: RM, TP, o similar

### V-MED-003 - Validación de EPS/IPS

**Validaciones**:
- EPS (Entidad Promotora de Salud): máximo 255 caracteres
- IPS (Institución Prestadora): máximo 255 caracteres
- Ambas opcionales pero recomendadas
- Si se proporcionan: deben coincidir con lista de prestadores vigentes (futuro)

### V-MED-004 - Descripción de Diagnóstico

**Validaciones**:
- Opcional pero recomendada
- Máximo: 1000 caracteres
- Sin SQL injection: sanitizar
- Permitir: letras, números, espacios, puntuación básica

---

## Validaciones de Datos Financieros

### V-FIN-001 - Validación de Montos

**Validaciones**:
- `valor_dia`: Numeric(15,2), > 0
- Máximo: 10,000,000 COP
- Mínimo legal: salario mínimo diario (SMLMV / 30)
- Comparación: si valor_día > salario_base empleado: ADVERTENCIA

### V-FIN-002 - Validación de Cálculo de Total

```
valor_total = valor_dia * dias_totales
```

**Validaciones**:
- Verificación: igualdad exacta
- Redondeo: 2 decimales máximo
- Si discrepancia > 1% → ERROR

### V-FIN-003 - Validación de Cuenta Bancaria

**Formato**: `^\d{10,20}$`

**Validaciones**:
- Dígitos únicamente, no espacios
- Mínimo: 10 dígitos
- Máximo: 20 dígitos
- Dígito verificador (si banco lo requiere)

### V-FIN-004 - Validación de Código de Banco

**Validaciones**:
- Código banco: 3 dígitos
- Debe existir en lista de bancos autorizados
- Estado: ACTIVO

**Bancos válidos** (ejemplos):
- 001: Banco de Bogotá
- 002: Banco Occidente
- 007: BBVA Colombia
- 009: Citibanco
- 010: Banco de Crédito
- ... (lista completa en base de datos)

### V-FIN-005 - Validación de Tipo de Cuenta

Valores permitidos:
- AHORROS
- CORRIENTE

---

## Validaciones de Documentos

### V-DOC-001 - Tipos de Documento Permitidos

| Tipo | Descripción | Obligatorio en ARL | Obligatorio en SALUD |
|------|-------------|-------------------|----------------------|
| INCAPACIDAD_MEDICA | Certificado médico firmado | SÍ | SÍ |
| CEDULA | Cédula de identidad | NO | NO |
| HISTORIA_CLINICA | Registros médicos | NO | NO |
| SOPORTE_PAGO | Comprobantes de pago | NO | NO |
| OTROS | Otro tipo de documento | NO | NO |

### V-DOC-002 - Validaciones de Archivo

| Parámetro | Regla |
|-----------|-------|
| Formatos | PDF, JPG, PNG, DOCX, XLSX |
| MIME type | application/pdf, image/jpeg, image/png, application/vnd.openxml* |
| Tamaño individual | <= 10 MB |
| Tamaño total | <= 50 MB |
| Cantidad mínima | 1 (INCAPACIDAD_MEDICA) |

### V-DOC-003 - Validaciones de Contenido

**Validaciones ejecutadas**:
- Magic bytes: verificar que archivo es del tipo declarado
- Virus scan: (si antivirus disponible)
- Extracción de metadatos: verificar que fecha de documento es coherente
- OCR: (futuro) verificar que código CIE-10 en documento coincide

### V-DOC-004 - Validación de Hash

**Proceso**:
1. Calcular SHA256 del archivo
2. Comparar con hash almacenado
3. Detectar duplicados: si SHA256 existe, verificar

**Almacenamiento**:
- hash_md5: 32 caracteres hexadecimales
- hash_sha256: 64 caracteres hexadecimales

---

## Validaciones de Usuarios

### V-USU-001 - Validación de Username

```regex
^[a-z0-9._-]{6,50}$
```

**Reglas**:
- Caracteres: a-z (minúsculas), 0-9, punto (.), guión (-), guión bajo (_)
- Mínimo: 6 caracteres
- Máximo: 50 caracteres
- Debe ser único en USUARIO
- NO permitido: espacios, mayúsculas

### V-USU-002 - Validación de Contraseña

**Criterios**:
- Mínimo: 8 caracteres
- Debe contener: 1 mayúscula (A-Z)
- Debe contener: 1 minúscula (a-z)
- Debe contener: 1 dígito (0-9)
- Debe contener: 1 carácter especial (!@#$%^&*)
- NO puede contener username
- NO puede ser contraseña común (top 10,000)

**Almacenamiento**:
- bcrypt hash (cost factor 12)
- NUNCA en texto plano

### V-USU-003 - Validación de Rol

Valores permitidos:
- ADMIN: Acceso total
- AUDITOR: Auditar incapacidades
- APROBADOR: Aprobar órdenes de pago
- EMPRESA: Usuario de empresa
- EMPLEADO: Usuario empleado
- READONLY: Solo lectura

### V-USU-004 - Validación de Estado de Usuario

Valores permitidos:
- ACTIVO: Puede usar sistema
- INACTIVO: No puede login
- BLOQUEADO: Bloqueado temporal por intentos fallidos

---

## Validaciones de Transición de Estado

### V-EST-001 - Máquina de Estados Válida

**Transiciones permitidas**:
```
RADICADA → EN_AUDITORIA
EN_AUDITORIA → {OBSERVADA, APROBADA, RECHAZADA}
OBSERVADA → EN_AUDITORIA (re-radicación)
APROBADA → EN_PAGO
EN_PAGO → PAGADA
* → CANCELADA (si no PAGADA)
```

**Transiciones NO permitidas** (error):
```
RADICADA → APROBADA (debe pasar por auditoría)
RECHAZADA → * (estado final)
PAGADA → * (estado final)
EN_AUDITORIA → PAGADA (debe pasar por APROBADA)
```

### V-EST-002 - Precondiciones de Transición

| Transición | Precondición | Usuario requerido |
|-----------|-------------|------------------|
| → EN_AUDITORIA | Documentos cargados | AUDITOR |
| → APROBADA | Documentos validados, datos válidos | AUDITOR/APROBADOR |
| → OBSERVADA | Motivo explicado | AUDITOR/APROBADOR |
| → RECHAZADA | Motivo explicado (>20 chars) | AUDITOR/APROBADOR |
| → EN_PAGO | ORDEN_PAGO creada | ADMIN/APROBADOR |
| → PAGADA | ORDEN_PAGO confirmada | APROBADOR |

### V-EST-003 - Validación de Cambios de Entidad

**Para transiciones que modifican datos**:
- Si INCAPACIDAD ya tiene usuarios asignados (radicado_por, auditado_por): NO permitir edición
- Si hay DOCUMENTO: NO permitir cambiar tipo incapacidad
- Si hay HISTORIAL_ESTADO: registrar nuevo cambio (no editar anterior)

---

## Matriz de Validación por Endpoint

| Endpoint | Método | Validaciones clave |
|----------|--------|-------------------|
| POST `/api/v1/incapacidades/radicar` (individual, EMPRESA) | POST | V-RAD-001..004, V-PER-001..006, V-MED-001..004, V-DOC-001..004 |
| POST `/api/v1/incapacidades/radicar-masiva/validar` (Excel, EMPRESA) | POST | V-RAD-001..004, V-MED-001 (formato + existencia CIE-10), por fila |
| POST `/api/v1/incapacidades/radicar-masiva` (lote, EMPRESA) | POST | V-RAD-001..004, V-MED-001..004, V-DOC-001..004, por fila |
| GET `/api/v1/incapacidades/mi-empresa` (consulta, EMPRESA) | GET | `empresa_id` forzado desde el token (RBAC) |
| POST `/api/v1/documentos/upload` | POST | V-DOC-002, V-DOC-003, V-DOC-004 |
| POST `/api/v1/incapacidades/{id}/aprobar` | POST | V-EST-002, validar DOCUMENTO validado=true |
| POST `/api/v1/ordenes-pago` | POST | V-FIN-001..005, V-EST-003 |
| PUT `/api/v1/usuarios/{id}` | PUT | V-USU-003, V-USU-004 |

> **Notas sobre dónde se aplican V-MED-001 y V-RAD-004 (CIE-10 y tipo_enfermedad)**
> tras el refactor del Portal Externo (2026-06):
> - El **formato** CIE-10 (`^[A-Z]\d{2}[0-9X]$`) y `tipo_enfermedad` se validan a
>   nivel de campo en cada fila (código `INVALID_CIE10_FORMAT` / `INVALID_TIPO_ENFERMEDAD`).
> - La **existencia en catálogo** se valida en la radicación: si el código cumple
>   el formato pero no existe en `catalogo_cie10`, se emite `CIE10_NO_EXISTE`
>   (severidad ERROR) y se rechaza la fila/radicación.
> - Solo las incidencias de severidad **ERROR** bloquean; las **WARNING** son
>   advisory (no bloquean la radicación).

---

*Documento sincronizado con especificación de validaciones - Junio 2026*
