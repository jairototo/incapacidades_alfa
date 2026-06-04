# Diccionario de Datos Completo - Sistema de Gestión de Incapacidades

**Versión**: 2.0  
**Fecha**: Junio 2026  
**Base de Datos**: PostgreSQL 15+  
**ORM**: SQLAlchemy 2.0 Async

---

## Tabla de Contenidos

- [USUARIO](#tabla-usuario)
- [REFRESH_TOKEN](#tabla-refresh_token)
- [EMPRESA](#tabla-empresa)
- [EMPLEADO](#tabla-empleado)
- [AFILIADO](#tabla-afiliado)
- [INCAPACIDAD](#tabla-incapacidad)
- [SINIESTRO](#tabla-siniestro)
- [SOLICITANTE](#tabla-solicitante)
- [DOCUMENTO](#tabla-documento)
- [PRE_INCAPACIDAD](#tabla-pre_incapacidad)
- [PRE_DOCUMENTO](#tabla-pre_documento)
- [ORDEN_PAGO](#tabla-orden_pago)
- [HISTORIAL_ESTADO](#tabla-historial_estado)
- [AUDITORIA_LOG](#tabla-auditoria_log)
- [AUDITORIA_DATOS_APROBADOS](#tabla-auditoria_datos_aprobados)
- [CATALOGO_CIE10](#tabla-catalogo_cie10)
- [ALEMBIC_VERSION](#tabla-alembic_version)

---

## TABLA: USUARIO

**Descripción**: Gestión centralizada de usuarios del sistema con control de acceso, autenticación y seguridad.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_usuario_username` sobre `username` (UNIQUE)
- `ix_usuario_email` sobre `email` (UNIQUE)
- `ix_usuario_rol` sobre `rol`
- `ix_usuario_empresa_id` sobre `empresa_id`

### Columnas

| # | Nombre | Tipo PostgreSQL | Tamaño | Nulo | Único | Índice | Descripción |
|---|--------|-----------------|--------|------|-------|--------|------------|
| 1 | id | UUID | 16B | NO | SÍ | PK | Identificador único auto-generado (v4) |
| 2 | username | VARCHAR(50) | 50B | NO | SÍ | SÍ | Nombre de usuario único para login |
| 3 | email | VARCHAR(255) | 255B | NO | SÍ | SÍ | Correo electrónico único |
| 4 | password_hash | VARCHAR(255) | 255B | NO | - | - | Hash bcrypt de la contraseña (mín. 60 chars) |
| 5 | nombre_completo | VARCHAR(255) | 255B | NO | - | - | Nombre completo del usuario |
| 6 | rol | VARCHAR(50) | 50B | NO | - | SÍ | RBAC: ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY |
| 7 | estado | VARCHAR(20) | 20B | NO | - | - | ACTIVO, INACTIVO, BLOQUEADO (default: ACTIVO) |
| 8 | empleado_id | UUID | 16B | SÍ | - | - | FK → EMPLEADO (si usuario es empleado) |
| 9 | empresa_id | UUID | 16B | SÍ | - | SÍ | FK → EMPRESA (si usuario pertenece a empresa) |
| 10 | ultimo_acceso | TIMESTAMP(TZ) | 8B | SÍ | - | - | Fecha/hora del último login exitoso |
| 11 | intentos_fallidos | INTEGER | 4B | NO | - | - | Contador de intentos fallidos (reset a 0 en login exitoso) |
| 12 | bloqueado_hasta | TIMESTAMP(TZ) | 8B | SÍ | - | - | Fecha/hora hasta que usuario está bloqueado (5+ intentos = 30 min) |
| 13 | token_version | INTEGER | 4B | NO | - | - | Versión de token (para invalidación en masa; default: 0) |
| 14 | must_change_password | BOOLEAN | 1B | NO | - | - | Flag para forzar cambio de contraseña en próximo login |
| 15 | created_at | TIMESTAMP(TZ) | 8B | NO | - | - | Fecha/hora de creación del usuario (default: NOW) |
| 16 | updated_at | TIMESTAMP(TZ) | 8B | NO | - | - | Fecha/hora de última actualización |

### Validaciones

- `username`: Alfanumérico + guiones bajos, 6-50 caracteres
- `email`: Formato válido de email, 8-255 caracteres
- `password_hash`: Generado con bcrypt (cost factor 12)
- `rol`: Debe estar en enumeración {ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY}
- `estado`: Debe estar en enumeración {ACTIVO, INACTIVO, BLOQUEADO}
- Si `empleado_id` → `empresa_id` debe ser NULL (usuario es empleado, no empresa)
- Si `empresa_id` y NO `empleado_id` → usuario es representante de empresa

### Relaciones

- FK `empleado_id` → EMPLEADO.id (ON DELETE SET NULL)
- FK `empresa_id` → EMPRESA.id (ON DELETE SET NULL)

### Ejemplo de Registro

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "jgarcia",
  "email": "juan.garcia@empresa.com",
  "password_hash": "$2b$12$...",
  "nombre_completo": "Juan García López",
  "rol": "AUDITOR",
  "estado": "ACTIVO",
  "empleado_id": null,
  "empresa_id": "123e4567-e89b-12d3-a456-426614174000",
  "ultimo_acceso": "2026-06-03T14:30:15+00:00",
  "intentos_fallidos": 0,
  "bloqueado_hasta": null,
  "token_version": 2,
  "must_change_password": false,
  "created_at": "2026-01-15T08:00:00+00:00",
  "updated_at": "2026-06-03T14:30:15+00:00"
}
```

---

## TABLA: REFRESH_TOKEN

**Descripción**: Gestión de tokens JWT para renovación de sesiones sin revalidar credenciales.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_refresh_token_usuario_id` sobre `usuario_id`
- `ix_refresh_token_token_hash` sobre `token_hash`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | usuario_id | UUID FK | NO | Referencia al usuario propietario del token |
| 3 | token_hash | VARCHAR(64) | NO | Hash SHA256 del token completo (para seguridad) |
| 4 | expires_at | TIMESTAMP(TZ) | NO | Fecha de expiración (típicamente +7 días) |
| 5 | revoked_at | TIMESTAMP(TZ) | SÍ | Fecha de revocación manual (NULL si activo) |
| 6 | ip_address | INET | SÍ | IP desde donde se solicitó el token |
| 7 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 8 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

### Validaciones

- Token válido solo si `revoked_at IS NULL` y `NOW() < expires_at`
- Se revoca automáticamente al cambiar contraseña o logout

---

## TABLA: EMPRESA

**Descripción**: Registro de empresas aseguradoras ARL y SALUD afiliadas al sistema.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_empresa_nit` sobre `nit` (UNIQUE)
- `ix_empresa_estado` sobre `estado`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Único | Descripción |
|---|--------|-----------------|------|-------|------------|
| 1 | id | UUID | NO | SÍ | Identificador único |
| 2 | nit | VARCHAR(20) | NO | SÍ | NIT de empresa (formato: 123456789-1) |
| 3 | razon_social | VARCHAR(255) | NO | - | Nombre legal de la empresa |
| 4 | email_contacto | VARCHAR(255) | SÍ | - | Email de contacto principal |
| 5 | telefono | VARCHAR(20) | SÍ | - | Teléfono de contacto |
| 6 | direccion | TEXT | SÍ | - | Dirección física completa |
| 7 | ciudad | VARCHAR(100) | SÍ | - | Ciudad de domicilio |
| 8 | departamento | VARCHAR(100) | SÍ | - | Departamento/Estado |
| 9 | tipo_empresa | VARCHAR(50) | SÍ | - | ARL, SALUD, MIXTO |
| 10 | estado | VARCHAR(20) | NO | - | ACTIVA, INACTIVA, SUSPENDIDA (default: ACTIVA) |
| 11 | sync_source | VARCHAR(50) | SÍ | - | API, CSV, EXCEL, MANUAL |
| 12 | external_id | VARCHAR(100) | SÍ | - | ID externo de sincronización |
| 13 | metadata_ | JSONB | SÍ | - | Datos adicionales (contactos alternos, políticas, etc.) |
| 14 | created_at | TIMESTAMP(TZ) | NO | - | Fecha de creación |
| 15 | updated_at | TIMESTAMP(TZ) | NO | - | Fecha de última actualización |

### Ejemplo Metadata

```json
{
  "contacto_alterno": "maria.rodriguez@empresa.com",
  "politica_reembolso": "48_horas",
  "documentos_requeridos": ["cedula", "incapacidad_medica"],
  "version_integracion": "2.1"
}
```

---

## TABLA: EMPLEADO

**Descripción**: Registro de empleados vinculados a empresas ARL para radicación de incapacidades laborales.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_empleado_empresa_id` sobre `empresa_id`
- `ix_empleado_numero_documento` sobre `numero_documento` (compuesto con empresa_id para unicidad)
- `ix_empleado_estado` sobre `estado`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | empresa_id | UUID FK | NO | Referencia a empresa (obligatoria, cascada en delete) |
| 3 | numero_documento | VARCHAR(20) | NO | Número de ID (CC, CE, TI, etc.) |
| 4 | tipo_documento | VARCHAR(10) | NO | CC, CE, TI, PASAPORTE, PEP |
| 5 | nombres | VARCHAR(100) | NO | Nombres del empleado |
| 6 | apellidos | VARCHAR(100) | NO | Apellidos del empleado |
| 7 | email | VARCHAR(255) | SÍ | Email corporativo o personal |
| 8 | telefono | VARCHAR(20) | SÍ | Teléfono de contacto |
| 9 | fecha_nacimiento | DATE | SÍ | Fecha de nacimiento (para cálculos de edad) |
| 10 | genero | VARCHAR(10) | SÍ | M, F, O (otro) |
| 11 | cargo | VARCHAR(100) | SÍ | Cargo o posición laboral |
| 12 | area | VARCHAR(100) | SÍ | Área/Departamento |
| 13 | fecha_ingreso | DATE | NO | Fecha de ingreso a empresa |
| 14 | fecha_retiro | DATE | SÍ | Fecha de retiro (NULL si activo) |
| 15 | salario_base | NUMERIC(15,2) | SÍ | Salario mensual en COP |
| 16 | cuenta_bancaria | VARCHAR(50) | SÍ | Número de cuenta para pagos |
| 17 | banco | VARCHAR(100) | SÍ | Nombre del banco |
| 18 | tipo_cuenta | VARCHAR(20) | SÍ | AHORROS, CORRIENTE |
| 19 | estado | VARCHAR(20) | NO | ACTIVO, INACTIVO, RETIRADO (default: ACTIVO) |
| 20 | sync_source | VARCHAR(50) | SÍ | API, CSV, EXCEL, MANUAL |
| 21 | external_id | VARCHAR(100) | SÍ | ID externo de sincronización |
| 22 | metadata_ | JSONB | SÍ | Datos adicionales (centro_costo, jefe_directo, etc.) |
| 23 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 24 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

### Validaciones

- `numero_documento`: Debe ser único por empresa
- `email`: Si se proporciona, debe ser válido
- `fecha_ingreso`: NO puede ser posterior a HOY
- `fecha_retiro`: Si se proporciona, debe ser >= fecha_ingreso
- `salario_base`: Si se proporciona, debe ser > 0
- `estado`: ACTIVO si fecha_retiro IS NULL

---

## TABLA: AFILIADO

**Descripción**: Registro de asegurados de pólizas de salud para incapacidades no laborales.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_afiliado_numero_poliza` sobre `numero_poliza` (UNIQUE)
- `ix_afiliado_numero_documento` sobre `numero_documento`
- `ix_afiliado_external_id` sobre `external_id`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | numero_poliza | VARCHAR(50) | NO | Número de póliza (único, indexado) |
| 3 | tipo_poliza | VARCHAR(50) | NO | INDIVIDUAL, FAMILIAR, COLECTIVA |
| 4 | tipo_documento | VARCHAR(20) | NO | CC, CE, TI, PASAPORTE, PEP |
| 5 | numero_documento | VARCHAR(20) | NO | Número de documento de identidad |
| 6 | nombres | VARCHAR(100) | NO | Nombres del afiliado |
| 7 | apellidos | VARCHAR(100) | NO | Apellidos del afiliado |
| 8 | fecha_nacimiento | DATE | SÍ | Fecha de nacimiento |
| 9 | genero | VARCHAR(1) | SÍ | M, F, O |
| 10 | email | VARCHAR(100) | SÍ | Correo electrónico |
| 11 | telefono | VARCHAR(20) | SÍ | Teléfono de contacto |
| 12 | direccion | VARCHAR(200) | SÍ | Dirección de residencia |
| 13 | ciudad | VARCHAR(100) | SÍ | Ciudad |
| 14 | departamento | VARCHAR(100) | SÍ | Departamento |
| 15 | fecha_inicio_poliza | DATE | NO | Inicio de vigencia |
| 16 | fecha_fin_poliza | DATE | SÍ | Fin de vigencia (NULL si vigente) |
| 17 | cuenta_bancaria | VARCHAR(50) | SÍ | Cuenta para pagos |
| 18 | banco | VARCHAR(100) | SÍ | Nombre del banco |
| 19 | tipo_cuenta | VARCHAR(20) | SÍ | AHORROS, CORRIENTE |
| 20 | estado | VARCHAR(20) | NO | ACTIVO, INACTIVO, SUSPENDIDO (default: ACTIVO) |
| 21 | sync_source | VARCHAR(50) | SÍ | API, CSV, EXCEL, MANUAL |
| 22 | external_id | VARCHAR(100) | SÍ | ID externo |
| 23 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 24 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

### Validaciones

- `numero_poliza`: Alfanumérico único
- `numero_documento`: Único dentro de tipo_documento
- `fecha_fin_poliza`: Si se proporciona, >= fecha_inicio_poliza
- Afiliado está **vigente** si `fecha_fin_poliza IS NULL` o `fecha_fin_poliza > HOY`

---

## TABLA: INCAPACIDAD

**Descripción**: Entidad central que registra incapacidades ARL o SALUD con workflow de estados y auditoría completa.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_incapacidad_numero` sobre `numero` (UNIQUE)
- `ix_incapacidad_tipo` sobre `tipo`
- `ix_incapacidad_estado` sobre `estado`
- `ix_incapacidad_empleado_id` sobre `empleado_id`
- `ix_incapacidad_afiliado_id` sobre `afiliado_id`
- `ix_incapacidad_empresa_id` sobre `empresa_id`
- `ix_incapacidad_solicitante_id` sobre `solicitante_id`

**Restricciones CHECK**:
```sql
CHECK (
  (tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL)
  OR
  (tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)
)
```

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | numero | VARCHAR(50) | NO | Número único de incapacidad (formato: INC-2026-000001) |
| 3 | tipo | ENUM | NO | ARL, SALUD |
| 4 | empleado_id | UUID FK | SÍ | Para ARL: referencia a empleado (NULL para SALUD) |
| 5 | empresa_id | UUID FK | SÍ | Para ARL: referencia a empresa (NULL para SALUD) |
| 6 | afiliado_id | UUID FK | SÍ | Para SALUD: referencia a afiliado (NULL para ARL) |
| 7 | solicitante_id | UUID FK | SÍ | Persona que radica la incapacidad |
| 8 | siniestro_id | UUID FK | SÍ | Para ARL: accidente laboral relacionado (opcional) |
| 9 | numero_siniestro | VARCHAR(50) | SÍ | Número del siniestro (denormalizado) |
| 10 | subtipo | VARCHAR(50) | SÍ | Subtipo específico (ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, etc.) |
| 11 | fecha_inicio | DATE | NO | Primer día de incapacidad |
| 12 | fecha_fin | DATE | NO | Último día de incapacidad |
| 13 | dias_totales | INTEGER | NO | Días de incapacidad (calculado: fecha_fin - fecha_inicio + 1) |
| 14 | diagnostico_cie10 | VARCHAR(10) | SÍ | Código CIE-10 (FK a CATALOGO_CIE10) |
| 15 | descripcion_diagnostico | TEXT | SÍ | Descripción clínica detallada |
| 16 | nombre_medico | VARCHAR(200) | SÍ | Nombre completo del médico tratante |
| 17 | registro_medico | VARCHAR(50) | SÍ | Registro profesional (RM, TP, etc.) |
| 18 | eps | VARCHAR(255) | SÍ | Entidad Promotora de Salud |
| 19 | ips | VARCHAR(255) | SÍ | Institución Prestadora de Salud |
| 20 | valor_dia | NUMERIC(15,2) | SÍ | Valor diario a pagar en COP |
| 21 | valor_total | NUMERIC(15,2) | SÍ | valor_dia * dias_totales |
| 22 | estado | ENUM | NO | RADICADA, EN_AUDITORIA, OBSERVADA, APROBADA, APROBADA_PARCIALMENTE, RECHAZADA, EN_PAGO, EN_PAGO_PARCIAL, PAGADA, PAGADA_PARCIALMENTE, CANCELADA (default: RADICADA) |
| 23 | observaciones | TEXT | SÍ | Observaciones generales del proceso |
| 24 | motivo_rechazo | TEXT | SÍ | Si estado=RECHAZADA, motivo del rechazo |
| 25 | prioridad | ENUM | NO | BAJA, NORMAL, ALTA, URGENTE (default: NORMAL) |
| 26 | radicado_por_id | UUID FK | SÍ | Usuario que radicó (denormalizado) |
| 27 | auditado_por_id | UUID FK | SÍ | Usuario que auditó (denormalizado) |
| 28 | aprobado_por_id | UUID FK | SÍ | Usuario que aprobó (denormalizado) |
| 29 | fecha_radicacion | TIMESTAMP(TZ) | NO | Fecha/hora de radicación |
| 30 | fecha_auditoria | TIMESTAMP(TZ) | SÍ | Fecha/hora de auditoría |
| 31 | fecha_aprobacion | TIMESTAMP(TZ) | SÍ | Fecha/hora de aprobación |
| 32 | fecha_rechazo | TIMESTAMP(TZ) | SÍ | Fecha/hora de rechazo |
| 33 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 34 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

### Máquina de Estados

```
RADICADA
    ↓ (AUDITOR)
EN_AUDITORIA
    ├→ OBSERVADA (AUDITOR/APROBADOR + solicita correcciones)
    │       ↓ (Solicitante corrige)
    │   EN_AUDITORIA (ciclo)
    │
    ├→ APROBADA (AUDITOR/APROBADOR)
    │       ↓ (ADMIN genera ORDEN_PAGO)
    │   EN_PAGO
    │       ↓ (Sistema de pagos)
    │   PAGADA
    │
    └→ RECHAZADA (AUDITOR/APROBADOR + motivo)

Estados parciales (futuro):
    APROBADA_PARCIALMENTE (parte del monto)
    EN_PAGO_PARCIAL
    PAGADA_PARCIALMENTE
    
CANCELADA (cancelación manual por ADMIN)
```

---

## TABLA: SINIESTRO

**Descripción**: Registro de accidentes laborales ARL que originan incapacidades.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_siniestro_numero` sobre `numero_siniestro` (UNIQUE)
- `ix_siniestro_empleado_id` sobre `empleado_id`
- `ix_siniestro_empresa_id` sobre `empresa_id`
- `ix_siniestro_estado` sobre `estado`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | numero_siniestro | VARCHAR(50) | NO | Número único (formato: SIN-2026-000001) |
| 3 | empleado_id | UUID FK | NO | Empleado accidentado (obligatorio) |
| 4 | empresa_id | UUID FK | NO | Empresa ARL (obligatorio) |
| 5 | fecha_siniestro | DATE | NO | Fecha del accidente |
| 6 | hora_siniestro | TIME | SÍ | Hora del accidente |
| 7 | tipo_siniestro | ENUM | NO | ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, ACCIDENTE_TRAYECTO |
| 8 | descripcion | TEXT | NO | Descripción detallada del accidente |
| 9 | lugar_ocurrencia | VARCHAR(255) | SÍ | Lugar del accidente (zona, oficina, calle, etc.) |
| 10 | parte_cuerpo_afectada | VARCHAR(100) | SÍ | Parte lesionada (mano, pierna, cabeza, etc.) |
| 11 | naturaleza_lesion | VARCHAR(100) | SÍ | Tipo (fractura, quemadura, contusión, herida, etc.) |
| 12 | agente_causante | VARCHAR(255) | SÍ | Elemento causante (máquina, sustancia química, etc.) |
| 13 | gravedad | ENUM | NO | LEVE, MODERADO, GRAVE, MORTAL (default: LEVE) |
| 14 | testigos | TEXT | SÍ | Nombres de personas que presenciaron el accidente |
| 15 | requirio_hospitalizacion | BOOLEAN | NO | Flag si fue hospitalizado (default: false) |
| 16 | dias_estimados_incapacidad | INTEGER | SÍ | Estimación inicial |
| 17 | estado | ENUM | NO | REPORTADO, EN_INVESTIGACION, CERRADO, ANULADO (default: REPORTADO) |
| 18 | fecha_reporte | TIMESTAMP(TZ) | NO | Fecha/hora del reporte |
| 19 | reportado_por | VARCHAR(255) | SÍ | Nombre del reportante |
| 20 | observaciones | TEXT | SÍ | Observaciones adicionales |
| 21 | sync_source | ENUM | SÍ | API, CSV, EXCEL, MANUAL |
| 22 | external_id | VARCHAR(100) | SÍ | ID externo |
| 23 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 24 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

---

## TABLA: SOLICITANTE

**Descripción**: Registro de personas que radican incapacidades (pueden ser empleados, familiares, o representantes).

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_solicitante_correo` sobre `correo` (UNIQUE)

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | correo | VARCHAR(100) | NO | Email único del solicitante |
| 3 | nombres | VARCHAR(100) | NO | Nombres |
| 4 | apellidos | VARCHAR(100) | NO | Apellidos |
| 5 | telefono | VARCHAR(20) | SÍ | Teléfono de contacto |
| 6 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 7 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

---

## TABLA: DOCUMENTO

**Descripción**: Metadatos de archivos adjuntos a incapacidades con validación de integridad.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_documento_incapacidad_id` sobre `incapacidad_id`
- `ix_documento_tipo` sobre `tipo_documento`
- `ix_documento_hash_sha256` sobre `hash_sha256`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | incapacidad_id | UUID FK | NO | Referencia a incapacidad (obligatoria, cascada) |
| 3 | tipo_documento | VARCHAR(50) | NO | INCAPACIDAD_MEDICA, CEDULA, HISTORIA_CLINICA, SOPORTE_PAGO, OTROS |
| 4 | nombre_archivo | VARCHAR(255) | NO | Nombre almacenado en storage |
| 5 | nombre_original | VARCHAR(255) | NO | Nombre original del archivo subido |
| 6 | ruta_storage | VARCHAR(500) | NO | Ruta dentro del bucket (ej: incapacidades/2026/06/abc123.pdf) |
| 7 | bucket | VARCHAR(100) | NO | Nombre del bucket MinIO/S3 |
| 8 | mime_type | VARCHAR(100) | NO | Tipo MIME (application/pdf, image/png, etc.) |
| 9 | tamanio_bytes | BIGINT | NO | Tamaño en bytes |
| 10 | hash_md5 | VARCHAR(32) | SÍ | Hash MD5 del archivo |
| 11 | hash_sha256 | VARCHAR(64) | SÍ | Hash SHA256 para validación de integridad |
| 12 | uploaded_by_id | UUID FK | SÍ | Usuario que subió el archivo |
| 13 | validado | BOOLEAN | NO | Flag de validación por equipo legal (default: false) |
| 14 | observacion_validacion | TEXT | SÍ | Observaciones de validación |
| 15 | created_at | TIMESTAMP(TZ) | NO | Fecha de carga |
| 16 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

---

## TABLA: PRE_INCAPACIDAD

**Descripción**: Almacenamiento temporal de radicaciones del portal externo pendientes de procesamiento.

**Clave Primaria**: `id` (UUID)

**Secuencias**:
- `pre_incapacidad_numero_seq` (start: 202600001, increment: 1)

**Índices**:
- `ix_pre_incapacidad_numero_radicacion` sobre `numero_radicacion` (UNIQUE)
- `ix_pre_incapacidad_estado` sobre `estado`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | numero_radicacion | INTEGER | NO | Número secuencial legible único (ej: 202600042) |
| 3 | estado | VARCHAR(20) | NO | PENDIENTE, PROCESADA, RECHAZADA, ERROR (default: PENDIENTE) |
| 4 | solicitante_correo | VARCHAR(255) | NO | Email del solicitante (datos planos) |
| 5 | solicitante_nombres | VARCHAR(200) | NO | Nombres (datos planos) |
| 6 | solicitante_apellidos | VARCHAR(200) | SÍ | Apellidos (datos planos) |
| 7 | solicitante_telefono | VARCHAR(20) | SÍ | Teléfono (datos planos) |
| 8 | empresa_nit | VARCHAR(20) | SÍ | NIT de empresa o NULL si independiente |
| 9 | empresa_nombre | VARCHAR(255) | SÍ | Nombre de empresa (datos planos) |
| 10 | empleado_tipo_documento | VARCHAR(10) | NO | CC, CE, TI, etc. |
| 11 | empleado_numero_documento | VARCHAR(20) | NO | Número de documento |
| 12 | empleado_nombres | VARCHAR(200) | NO | Nombres del empleado |
| 13 | empleado_apellidos | VARCHAR(200) | SÍ | Apellidos del empleado |
| 14 | empleado_email | VARCHAR(255) | SÍ | Email del empleado |
| 15 | empleado_telefono | VARCHAR(20) | SÍ | Teléfono del empleado |
| 16 | tipo | VARCHAR(10) | NO | ARL, SALUD (default: ARL) |
| 17 | tipo_enfermedad | VARCHAR(50) | NO | ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, ACCIDENTE_TRAYECTO |
| 18 | fecha_inicio | DATE | NO | Primer día de incapacidad |
| 19 | fecha_fin | DATE | NO | Último día de incapacidad |
| 20 | dias_totales | INTEGER | NO | Calculado: fecha_fin - fecha_inicio + 1 |
| 21 | diagnostico_cie10 | VARCHAR(10) | NO | Código CIE-10 |
| 22 | descripcion_diagnostico | TEXT | SÍ | Descripción clínica |
| 23 | nombre_medico | VARCHAR(200) | NO | Nombre del médico |
| 24 | registro_medico | VARCHAR(50) | NO | Registro profesional |
| 25 | ips | VARCHAR(255) | SÍ | IPS de atención |
| 26 | valor_dia | NUMERIC(14,2) | SÍ | Valor diario propuesto |
| 27 | observaciones | TEXT | SÍ | Observaciones del solicitante |
| 28 | error_procesamiento | TEXT | SÍ | Detalles del error si estado=ERROR |
| 29 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 30 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

### Flujo de Procesamiento

```
PENDIENTE
    ↓ (Job ejecuta validación)
    ├→ PROCESADA (éxito: crea INCAPACIDAD real)
    ├→ RECHAZADA (validación fallida, negocio decide rechazar)
    └→ ERROR (excepción técnica, retry posible)
```

---

## TABLA: PRE_DOCUMENTO

**Descripción**: Metadatos de archivos adjuntos a PRE_INCAPACIDAD.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_pre_documento_pre_incapacidad_id` sobre `pre_incapacidad_id`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | pre_incapacidad_id | UUID FK | NO | Referencia a PRE_INCAPACIDAD |
| 3 | tipo_documento | VARCHAR(50) | NO | INCAPACIDAD_MEDICA, CEDULA, etc. |
| 4 | nombre_archivo | VARCHAR(255) | NO | Nombre almacenado |
| 5 | nombre_original | VARCHAR(255) | NO | Nombre original |
| 6 | ruta_storage | VARCHAR(500) | NO | Ruta en bucket |
| 7 | bucket | VARCHAR(100) | NO | Nombre de bucket |
| 8 | mime_type | VARCHAR(100) | NO | Tipo MIME |
| 9 | tamanio_bytes | BIGINT | NO | Tamaño en bytes |
| 10 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |

---

## TABLA: ORDEN_PAGO

**Descripción**: Órdenes de pago generadas desde incapacidades aprobadas.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_orden_pago_numero` sobre `numero_orden` (UNIQUE)
- `ix_orden_pago_incapacidad_id` sobre `incapacidad_id`
- `ix_orden_pago_estado` sobre `estado_pago`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | numero_orden | VARCHAR(50) | NO | Número único de orden |
| 3 | incapacidad_id | UUID FK | NO | Referencia a incapacidad |
| 4 | beneficiario_tipo | VARCHAR(20) | NO | EMPLEADO, EMPRESA, IPS, AFILIADO |
| 5 | beneficiario_id | UUID | NO | ID del beneficiario |
| 6 | beneficiario_nombre | VARCHAR(255) | NO | Nombre completo |
| 7 | beneficiario_documento | VARCHAR(50) | NO | Documento de identidad |
| 8 | cuenta_bancaria | VARCHAR(50) | SÍ | Número de cuenta |
| 9 | banco | VARCHAR(100) | SÍ | Nombre del banco |
| 10 | tipo_cuenta | VARCHAR(20) | SÍ | AHORROS, CORRIENTE |
| 11 | valor_pagar | NUMERIC(15,2) | NO | Monto en COP |
| 12 | estado_pago | VARCHAR(30) | NO | Estados posibles (ver máquina de estados) |
| 13 | fecha_generacion | TIMESTAMP(TZ) | NO | Fecha de creación |
| 14 | fecha_pago | TIMESTAMP(TZ) | SÍ | Fecha del pago ejecutado |
| 15 | fecha_anulacion | TIMESTAMP(TZ) | SÍ | Fecha de anulación |
| 16 | metodo_pago | VARCHAR(50) | SÍ | TRANSFERENCIA, CHEQUE, EFECTIVO |
| 17 | referencia_pago | VARCHAR(100) | SÍ | Referencia de transacción |
| 18 | comprobante_ruta | VARCHAR(500) | SÍ | Ruta del comprobante |
| 19 | motivo_anulacion | TEXT | SÍ | Razón de anulación |
| 20 | creado_por_id | UUID FK | SÍ | Usuario que creó |
| 21 | aprobado_por_id | UUID FK | SÍ | Usuario que aprobó |
| 22 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 23 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

### Máquina de Estados

```
GENERADA (sistema crea automáticamente)
    ↓ (APROBADOR revisa)
    APROBADA
    ↓ (Sistema de pagos procesa)
    EN_PROCESO
    ├→ PAGADA (éxito)
    └→ ANULADA (error en transacción)

O directamente:
GENERADA
    ├→ RECHAZADA (APROBADOR rechaza)
    └→ ANULADA (ADMIN cancela)
```

---

## TABLA: HISTORIAL_ESTADO

**Descripción**: Registro polimórfico de cambios de estado para múltiples entidades (Incapacidad, Siniestro, OrdenPago).

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_historial_entity(entity_type, entity_id)` (compuesto)
- `ix_historial_fecha_cambio` sobre `fecha_cambio`
- `ix_historial_cambiado_por_id` sobre `cambiado_por_id`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | entity_type | VARCHAR(50) | NO | 'incapacidad', 'siniestro', 'orden_pago', etc. |
| 3 | entity_id | UUID | NO | ID de la entidad (no es FK, polimórfico) |
| 4 | estado_anterior | VARCHAR(50) | SÍ | Estado previo (NULL si cambio inicial) |
| 5 | estado_nuevo | VARCHAR(50) | NO | Nuevo estado |
| 6 | observacion | TEXT | SÍ | Motivo o descripción del cambio |
| 7 | fecha_cambio | TIMESTAMP(TZ) | NO | Fecha/hora del cambio |
| 8 | cambiado_por_id | UUID FK | SÍ | Usuario que realizó el cambio |
| 9 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |

### Ejemplo de Uso

```json
{
  "entity_type": "incapacidad",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "estado_anterior": "RADICADA",
  "estado_nuevo": "EN_AUDITORIA",
  "observacion": "Iniciada auditoría por Juan García",
  "fecha_cambio": "2026-06-03T14:30:00+00:00",
  "cambiado_por_id": "550e8400-e29b-41d4-a716-446655440111"
}
```

---

## TABLA: AUDITORIA_LOG

**Descripción**: Log de auditoría detallado de todas las acciones del sistema.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_auditoria_log_usuario_id` sobre `usuario_id`
- `ix_auditoria_log_accion` sobre `accion`
- `ix_auditoria_log_created_at` sobre `created_at`

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | usuario_id | UUID FK | SÍ | Usuario que realizó la acción |
| 3 | accion | VARCHAR(50) | NO | CREATE, UPDATE, DELETE, LOGIN, CAMBIO_ESTADO, UPLOAD_FILE, EXPORT_DATA, etc. |
| 4 | entidad | VARCHAR(50) | NO | Tipo de entidad: 'incapacidad', 'usuario', 'documento', etc. |
| 5 | entidad_id | UUID | SÍ | ID de la entidad afectada |
| 6 | detalles | JSONB | SÍ | Información completa de la acción (valores anteriores/nuevos) |
| 7 | ip_address | INET | SÍ | IP del cliente |
| 8 | user_agent | TEXT | SÍ | User-Agent del navegador |
| 9 | request_id | VARCHAR(100) | SÍ | ID único de la solicitud para trazabilidad |
| 10 | created_at | TIMESTAMP(TZ) | NO | Fecha/hora de la acción |
| 11 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

### Ejemplo de Detalles JSONB

```json
{
  "campo_actualizado": "estado",
  "valor_anterior": "RADICADA",
  "valor_nuevo": "EN_AUDITORIA",
  "ip_request": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "endpoint": "POST /api/v1/incapacidades/123/auditar"
}
```

---

## TABLA: AUDITORIA_DATOS_APROBADOS

**Descripción**: Captura de snapshot de datos de incapacidad en el momento de aprobación para auditoría y trazabilidad.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_auditoria_datos_incapacidad_id` sobre `incapacidad_id` (UNIQUE)

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | incapacidad_id | UUID FK | NO | Referencia a incapacidad (UNIQUE) |
| 3 | datos_capturados | JSONB | NO | Snapshot completo de todos los datos de la incapacidad |
| 4 | aprobado_por_id | UUID FK | SÍ | Usuario que aprobó |
| 5 | fecha_aprobacion | TIMESTAMP(TZ) | NO | Fecha/hora de la aprobación |
| 6 | observacion | TEXT | SÍ | Observaciones del aprobador |
| 7 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 8 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

### Estructura de datos_capturados (JSONB)

```json
{
  "numero": "INC-2026-000001",
  "tipo": "ARL",
  "empleado": {
    "id": "...",
    "nombres": "Juan",
    "apellidos": "García",
    "numero_documento": "1234567890"
  },
  "empresa": {
    "id": "...",
    "nit": "900123456-7",
    "razon_social": "Empresa XYZ"
  },
  "incapacidad": {
    "fecha_inicio": "2026-06-01",
    "fecha_fin": "2026-06-10",
    "dias_totales": 10,
    "diagnostico_cie10": "M54.5",
    "valor_dia": 150000,
    "valor_total": 1500000
  },
  "documentos": [
    {
      "tipo": "INCAPACIDAD_MEDICA",
      "nombre": "incapacidad_firma.pdf",
      "hash_sha256": "abc123def456..."
    }
  ]
}
```

---

## TABLA: CATALOGO_CIE10

**Descripción**: Catálogo de códigos CIE-10 para validación y referencia de diagnósticos.

**Clave Primaria**: `id` (UUID)

**Índices**:
- `ix_catalogo_cie10_codigo` sobre `codigo` (UNIQUE)

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | id | UUID | NO | Identificador único |
| 2 | codigo | VARCHAR(10) | NO | Código CIE-10 (ej: M54.5) |
| 3 | descripcion | TEXT | NO | Descripción del diagnóstico |
| 4 | activo | BOOLEAN | NO | Si está disponible para seleccionar (default: true) |
| 5 | created_at | TIMESTAMP(TZ) | NO | Fecha de creación |
| 6 | updated_at | TIMESTAMP(TZ) | NO | Fecha de última actualización |

---

## TABLA: ALEMBIC_VERSION

**Descripción**: Control de versiones de migraciones de base de datos (generada automáticamente por Alembic).

**Clave Primaria**: `version_num` (String)

### Columnas

| # | Nombre | Tipo PostgreSQL | Nulo | Descripción |
|---|--------|-----------------|------|------------|
| 1 | version_num | VARCHAR(32) | NO | Identificador de la migración (hash) |
| 2 | utc_dttm | TIMESTAMP | NO | Fecha/hora de aplicación |

---

## Notas Globales sobre el Modelo

### Convenciones Aplicadas

1. **Tipos de dato**:
   - UUID v4 para todas las claves primarias
   - TIMESTAMP(TZ) para todas las fechas (con zona horaria UTC)
   - NUMERIC(15,2) para moneda (2 decimales)
   - JSONB para datos flexibles

2. **Auditoría**:
   - Todas las tablas heredan `created_at` y `updated_at` de BaseModel
   - Cambios importantes se registran en HISTORIAL_ESTADO y AUDITORIA_LOG

3. **Integridad**:
   - Relaciones FK con ON DELETE CASCADE donde es lógico (DOCUMENTO → INCAPACIDAD)
   - ON DELETE SET NULL para relaciones opcionales (USUARIO → EMPLEADO)

4. **Performance**:
   - Índices en FK y campos de búsqueda frecuente
   - Índices compuestos para consultas polimórficas

---

*Este diccionario se mantiene en sincronización con el código de modelos en `apps/backend/app/models/`*
