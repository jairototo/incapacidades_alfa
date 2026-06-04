# Resumen del Modelo de Datos - Sistema de Gestión de Incapacidades

**Versión**: 2.0  
**Fecha de actualización**: Junio 2026  
**Audiencia**: Arquitectos, desarrolladores, analistas de datos

---

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Entidades Principales](#entidades-principales)
3. [Entidades de Soporte](#entidades-de-soporte)
4. [Entidades de Auditoría](#entidades-de-auditoría)
5. [Matriz de Relaciones](#matriz-de-relaciones)
6. [Flujos de Datos Principales](#flujos-de-datos-principales)

---

## Visión General

El modelo de datos del **Sistema de Gestión de Incapacidades** está diseñado para gestionar el ciclo de vida completo de incapacidades médicas en un contexto asegurador dual:

- **Incapacidades ARL** (Administradora de Riesgos Laborales): Gestionan accidentes laborales y enfermedades profesionales
- **Incapacidades SALUD**: Gestionan incapacidades de salud general a través de pólizas

### Características Principales

- **Arquitectura polimórfica**: Soporte para múltiples tipos de entidades con históricos de estado
- **Auditoría completa**: Registro de todos los cambios de estado y operaciones
- **Integridad referencial**: Relaciones explícitas con validaciones de negocio
- **Escalabilidad**: Índices estratégicos y diseño optimizado para consultas complejas
- **Base de datos**: PostgreSQL 15+ con tipos nativos (UUID, JSONB, ENUM)

---

## Entidades Principales

### 1. **USUARIO** (15 campos)

**Propósito**: Gestión de acceso y autenticación del sistema

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único (heredado de BaseModel) |
| username | String(50) | Usuario único para login |
| email | String(255) | Email único del usuario |
| password_hash | String(255) | Hash bcrypt de la contraseña |
| nombre_completo | String(255) | Nombre completo del usuario |
| rol | String(50) | Rol RBAC: ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY |
| estado | String(20) | ACTIVO, INACTIVO, BLOQUEADO |
| empleado_id | UUID FK | Referencia a empleado (si aplica) |
| empresa_id | UUID FK | Referencia a empresa (si aplica) |
| ultimo_acceso | TIMESTAMP | Fecha/hora del último acceso |
| intentos_fallidos | Integer | Contador de intentos fallidos de login (reset a 5 bloqueado) |
| bloqueado_hasta | TIMESTAMP | Fecha/hora de desbloqueobloqueado después de 5 intentos |
| token_version | Integer | Versión actual de token (para invalidación en masa) |
| must_change_password | Boolean | Flag para forzar cambio de contraseña |
| created_at | TIMESTAMP | Fecha de creación (heredada) |
| updated_at | TIMESTAMP | Fecha última actualización (heredada) |

**Relaciones**:
- N:1 → EMPLEADO (usuario puede ser empleado)
- N:1 → EMPRESA (usuario puede pertenecer a empresa)
- 1:N → INCAPACIDAD (radicadas, auditadas, aprobadas)
- 1:N → DOCUMENTO (documentos subidos)
- 1:N → HISTORIAL_ESTADO (cambios de estado realizados)
- 1:N → AUDITORIA_LOG (acciones de auditoría)
- 1:N → REFRESH_TOKEN (tokens activos)

---

### 2. **EMPRESA** (11 campos)

**Propósito**: Registro de empresas aseguradoras ARL/SALUD

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| nit | String(20) | NIT de la empresa (único, indexado) |
| razon_social | String(255) | Nombre legal de la empresa |
| email_contacto | String(255) | Email de contacto principal |
| telefono | String(20) | Teléfono de contacto |
| direccion | Text | Dirección física |
| ciudad | String(100) | Ciudad de la empresa |
| departamento | String(100) | Departamento/Estado |
| tipo_empresa | String(50) | ARL, SALUD, MIXTO |
| estado | String(20) | ACTIVA, INACTIVA, SUSPENDIDA |
| sync_source | String(50) | Origen: API, CSV, EXCEL, MANUAL |
| external_id | String(100) | ID externo de sincronización |
| metadata_ | JSONB | Datos adicionales en formato JSON |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha última actualización |

**Relaciones**:
- 1:N → EMPLEADO (empleados de la empresa)
- 1:N → INCAPACIDAD (incapacidades ARL)
- 1:N → SINIESTRO (siniestros laborales)
- 1:N → USUARIO (usuarios de la empresa)

---

### 3. **EMPLEADO** (16 campos)

**Propósito**: Registro de empleados de empresas ARL

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| empresa_id | UUID FK | Referencia a empresa (obligatoria, cascada) |
| numero_documento | String(20) | Número de documento del empleado |
| tipo_documento | String(10) | CC, CE, TI, PASAPORTE, PEP |
| nombres | String(100) | Nombres del empleado |
| apellidos | String(100) | Apellidos del empleado |
| email | String(255) | Email del empleado |
| telefono | String(20) | Teléfono de contacto |
| fecha_nacimiento | Date | Fecha de nacimiento |
| genero | String(10) | M, F, O (masculino, femenino, otro) |
| cargo | String(100) | Cargo del empleado |
| area | String(100) | Área/Departamento del empleado |
| fecha_ingreso | Date | Fecha de ingreso a la empresa |
| fecha_retiro | Date | Fecha de retiro (NULL si activo) |
| salario_base | Numeric(15,2) | Salario base mensual |
| cuenta_bancaria | String(50) | Número de cuenta bancaria |
| banco | String(100) | Nombre del banco |
| tipo_cuenta | String(20) | AHORROS, CORRIENTE |
| estado | String(20) | ACTIVO, INACTIVO, RETIRADO |
| sync_source | String(50) | Origen de sincronización |
| external_id | String(100) | ID externo |
| metadata_ | JSONB | Datos adicionales |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha última actualización |

**Relaciones**:
- N:1 → EMPRESA (empresa a la que pertenece)
- 1:N → INCAPACIDAD (incapacidades ARL del empleado)
- 1:N → SINIESTRO (siniestros laborales del empleado)
- 0:1 → USUARIO (usuario asociado si existe)

---

### 4. **AFILIADO** (18 campos)

**Propósito**: Registro de afiliados de pólizas de salud

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| numero_poliza | String(50) | Número de póliza (único, indexado) |
| tipo_poliza | String(50) | INDIVIDUAL, FAMILIAR, COLECTIVA |
| tipo_documento | String(20) | CC, CE, TI, PASAPORTE, PEP |
| numero_documento | String(20) | Número de documento (indexado) |
| nombres | String(100) | Nombres del afiliado |
| apellidos | String(100) | Apellidos del afiliado |
| fecha_nacimiento | Date | Fecha de nacimiento |
| genero | String(1) | M, F, O |
| email | String(100) | Email del afiliado |
| telefono | String(20) | Teléfono de contacto |
| direccion | String(200) | Dirección física |
| ciudad | String(100) | Ciudad de residencia |
| departamento | String(100) | Departamento de residencia |
| fecha_inicio_poliza | Date | Inicio de vigencia de póliza |
| fecha_fin_poliza | Date | Fin de vigencia (NULL si vigente) |
| cuenta_bancaria | String(50) | Número de cuenta para pagos |
| banco | String(100) | Banco de cuenta |
| tipo_cuenta | String(20) | AHORROS, CORRIENTE |
| estado | String(20) | ACTIVO, INACTIVO, SUSPENDIDO |
| sync_source | String(50) | Origen de sincronización |
| external_id | String(100) | ID externo |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha última actualización |

**Relaciones**:
- 1:N → INCAPACIDAD (incapacidades SALUD del afiliado)

---

### 5. **INCAPACIDAD** (32 campos)

**Propósito**: Registro central de incapacidades (ARL o SALUD)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| numero | String(50) | Número único de incapacidad |
| tipo | String(10) | ARL, SALUD (enum) |
| empleado_id | UUID FK | Para ARL: referencia a empleado (NULL para SALUD) |
| empresa_id | UUID FK | Para ARL: referencia a empresa (NULL para SALUD) |
| afiliado_id | UUID FK | Para SALUD: referencia a afiliado (NULL para ARL) |
| solicitante_id | UUID FK | Persona que radica la incapacidad |
| siniestro_id | UUID FK | Para ARL: accidente laboral relacionado (opcional) |
| numero_siniestro | String(50) | Número del siniestro |
| subtipo | String(50) | Subtipo específico de incapacidad |
| fecha_inicio | Date | Primer día de incapacidad |
| fecha_fin | Date | Último día de incapacidad |
| dias_totales | Integer | Días de incapacidad |
| diagnostico_cie10 | String(10) | Código CIE-10 del diagnóstico |
| descripcion_diagnostico | Text | Descripción médica del diagnóstico |
| nombre_medico | String(200) | Nombre del médico tratante |
| registro_medico | String(50) | Registro profesional del médico |
| eps | String(255) | EPS (Entidad Promotora de Salud) |
| ips | String(255) | IPS (Institución Prestadora de Salud) |
| valor_dia | Numeric(15,2) | Valor diario a pagar |
| valor_total | Numeric(15,2) | Valor total de la incapacidad |
| estado | String(50) | Estado en workflow: RADICADA, EN_AUDITORIA, etc. |
| observaciones | Text | Observaciones generales |
| motivo_rechazo | Text | Motivo si fue rechazada |
| prioridad | String(20) | BAJA, NORMAL, ALTA, URGENTE |
| radicado_por_id | UUID FK | Usuario que radicó |
| auditado_por_id | UUID FK | Usuario que auditó |
| aprobado_por_id | UUID FK | Usuario que aprobó |
| fecha_radicacion | TIMESTAMP | Fecha/hora de radicación |
| fecha_auditoria | TIMESTAMP | Fecha/hora de auditoría |
| fecha_aprobacion | TIMESTAMP | Fecha/hora de aprobación |
| fecha_rechazo | TIMESTAMP | Fecha/hora de rechazo |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha última actualización |

**Restricciones de integridad**:
- CHECK: ARL debe tener empleado_id y empresa_id, NO afiliado_id
- CHECK: SALUD debe tener afiliado_id, NO empleado_id ni empresa_id

**Relaciones**:
- N:1 → EMPLEADO (para ARL)
- N:1 → EMPRESA (para ARL)
- N:1 → AFILIADO (para SALUD)
- N:1 → SOLICITANTE (quien radica)
- N:1 → SINIESTRO (accidente laboral, opcional para ARL)
- 1:N → DOCUMENTO (archivos adjuntos)
- 1:N → HISTORIAL_ESTADO (registro de cambios)
- 1:N → ORDEN_PAGO (órdenes de pago generadas)

---

### 6. **SINIESTRO** (19 campos)

**Propósito**: Registro de accidentes laborales ARL

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| numero_siniestro | String(50) | Número único del siniestro |
| empleado_id | UUID FK | Empleado afectado |
| empresa_id | UUID FK | Empresa de la ARL |
| fecha_siniestro | Date | Fecha del accidente |
| hora_siniestro | Time | Hora del accidente |
| tipo_siniestro | String(50) | ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, ACCIDENTE_TRAYECTO |
| descripcion | Text | Descripción detallada del accidente |
| lugar_ocurrencia | String(255) | Lugar donde ocurrió |
| parte_cuerpo_afectada | String(100) | Parte del cuerpo lesionada |
| naturaleza_lesion | String(100) | Tipo de lesión (fractura, quemadura, etc.) |
| agente_causante | String(255) | Agente que causó la lesión |
| gravedad | String(20) | LEVE, MODERADO, GRAVE, MORTAL |
| testigos | Text | Nombres de testigos |
| requirio_hospitalizacion | Boolean | Si requirió hospitalización |
| dias_estimados_incapacidad | Integer | Días estimados de incapacidad |
| estado | String(50) | REPORTADO, EN_INVESTIGACION, CERRADO, ANULADO |
| fecha_reporte | TIMESTAMP | Fecha de reporte |
| reportado_por | String(255) | Persona que reportó |
| observaciones | Text | Observaciones adicionales |
| sync_source | String(50) | Origen de sincronización |
| external_id | String(100) | ID externo |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha última actualización |

**Relaciones**:
- N:1 → EMPLEADO (empleado afectado)
- N:1 → EMPRESA (empresa ARL)
- 1:N → INCAPACIDAD (incapacidades relacionadas)
- 1:N → HISTORIAL_ESTADO (cambios de estado)

---

### 7. **ORDEN_PAGO** (18 campos)

**Propósito**: Gestión de órdenes de pago para beneficiarios

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| numero_orden | String(50) | Número único de orden (indexado) |
| incapacidad_id | UUID FK | Incapacidad a la que corresponde el pago |
| beneficiario_tipo | String(20) | EMPLEADO, EMPRESA, IPS, AFILIADO |
| beneficiario_id | UUID | ID del beneficiario |
| beneficiario_nombre | String(255) | Nombre del beneficiario |
| beneficiario_documento | String(50) | Documento del beneficiario |
| cuenta_bancaria | String(50) | Cuenta del beneficiario |
| banco | String(100) | Banco del beneficiario |
| tipo_cuenta | String(20) | AHORROS, CORRIENTE |
| valor_pagar | Numeric(15,2) | Monto a pagar |
| estado_pago | String(30) | GENERADA, APROBADA, EN_PROCESO, PAGADA, RECHAZADA, ANULADA |
| fecha_generacion | TIMESTAMP | Fecha de generación |
| fecha_pago | TIMESTAMP | Fecha en que se realizó el pago |
| fecha_anulacion | TIMESTAMP | Fecha de anulación (si aplica) |
| metodo_pago | String(50) | TRANSFERENCIA, CHEQUE, EFECTIVO |
| referencia_pago | String(100) | Referencia de la transacción |
| comprobante_ruta | String(500) | Ruta del comprobante de pago |
| motivo_anulacion | Text | Motivo si fue anulada |
| creado_por_id | UUID FK | Usuario que creó la orden |
| aprobado_por_id | UUID FK | Usuario que aprobó |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha última actualización |

**Relaciones**:
- N:1 → INCAPACIDAD (incapacidad a pagar)
- N:1 → USUARIO (creador de la orden)
- N:1 → USUARIO (aprobador de la orden)

---

## Entidades de Soporte

### 8. **DOCUMENTO** (14 campos)

**Propósito**: Almacenamiento de metadatos de archivos adjuntos

Campos: incapacidad_id (FK), tipo_documento, nombre_archivo, nombre_original, ruta_storage, bucket, mime_type, tamanio_bytes, hash_md5, hash_sha256, uploaded_by_id (FK), validado, observacion_validacion, timestamps

**Relaciones**: N:1 → INCAPACIDAD, N:1 → USUARIO

---

### 9. **PRE_INCAPACIDAD** (25 campos)

**Propósito**: Almacenamiento plano de radicaciones pendientes de procesamiento

**Descripción**: Tabla temporal para incapacidades radicadas desde portal externo. Los registros se procesan mediante job/tarea programada y se convierten en INCAPACIDAD reales.

Campos: numero_radicacion (secuencia única), estado (PENDIENTE|PROCESADA|RECHAZADA|ERROR), solicitante_* (datos planos), empresa_* (datos planos), empleado_* (datos planos), tipo, fecha_inicio, fecha_fin, etc.

---

### 10. **PRE_DOCUMENTO** (10 campos)

**Propósito**: Metadatos de archivos adjuntos a PRE_INCAPACIDAD

Relación con PRE_INCAPACIDAD para procesamiento posterior.

---

### 11. **SOLICITANTE** (5 campos)

**Propósito**: Registro de personas que radican incapacidades

Campos: correo (único), nombres, apellidos, telefono

**Relaciones**: 1:N → INCAPACIDAD

---

### 12. **CATALOGO_CIE10** (3 campos)

**Propósito**: Catálogo de códigos CIE-10 para diagnósticos

Campos: codigo (String, único), descripcion, activo

---

### 13. **REFRESH_TOKEN** (6 campos)

**Propósito**: Gestión de tokens JWT para renovación de sesiones

Campos: usuario_id (FK), token_hash (SHA256), expires_at, revoked_at, created_at, ip_address

---

## Entidades de Auditoría

### 14. **HISTORIAL_ESTADO** (9 campos - Polimórfico)

**Propósito**: Registro polimórfico de cambios de estado para múltiples entidades

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| entity_type | String(50) | Tipo de entidad: 'incapacidad', 'siniestro', 'orden_pago' |
| entity_id | UUID | ID de la entidad (indexado) |
| estado_anterior | String(50) | Estado previo |
| estado_nuevo | String(50) | Nuevo estado |
| observacion | Text | Observaciones del cambio |
| fecha_cambio | TIMESTAMP | Fecha/hora del cambio (indexada) |
| cambiado_por_id | UUID FK | Usuario que realizó el cambio |
| created_at | TIMESTAMP | Fecha de creación |

**Índice compuesto**: `ix_historial_entity(entity_type, entity_id)` para búsquedas eficientes

---

### 15. **AUDITORIA_LOG** (12 campos)

**Propósito**: Log detallado de todas las acciones del sistema

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| usuario_id | UUID FK | Usuario que realizó la acción |
| accion | String(50) | CREATE, UPDATE, DELETE, LOGIN, CAMBIO_ESTADO, etc. |
| entidad | String(50) | Tipo de entidad afectada |
| entidad_id | UUID | ID de la entidad afectada |
| detalles | JSONB | Información detallada de la acción |
| ip_address | INET | IP de la solicitud |
| user_agent | Text | User-Agent del navegador |
| request_id | String(100) | ID único de la solicitud |
| created_at | TIMESTAMP | Fecha/hora de la acción |
| updated_at | TIMESTAMP | Fecha de actualización |

---

### 16. **AUDITORIA_DATOS_APROBADOS** (8 campos)

**Propósito**: Captura de datos de incapacidad en el momento de aprobación

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| incapacidad_id | UUID FK | Incapacidad aprobada |
| datos_capturados | JSONB | Snapshot JSON de todos los datos |
| aprobado_por_id | UUID FK | Usuario que aprobó |
| fecha_aprobacion | TIMESTAMP | Fecha de aprobación |
| observacion | Text | Observaciones |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha de actualización |

---

### 17. **ALEMBIC_VERSION** (2 campos)

**Propósito**: Control de versiones de migraciones de base de datos

Campos: version_num (String, PK), utc_dttm (TIMESTAMP)

---

## Matriz de Relaciones

```
USUARIO
├─ 0..1 EMPLEADO (usuario puede ser empleado)
├─ 0..1 EMPRESA (usuario puede pertenecer a empresa)
├─ N DOCUMENTO (usuario sube documentos)
├─ N HISTORIAL_ESTADO (usuario realiza cambios)
├─ N AUDITORIA_LOG (acciones de usuario)
└─ N REFRESH_TOKEN (tokens activos)

EMPRESA
├─ N EMPLEADO (empleados de empresa)
├─ N INCAPACIDAD (incapacidades ARL)
├─ N SINIESTRO (siniestros laborales)
└─ N USUARIO (usuarios de empresa)

EMPLEADO
├─ 1 EMPRESA (obligatoria, cascada)
├─ N INCAPACIDAD (incapacidades del empleado)
├─ N SINIESTRO (accidentes del empleado)
└─ 0..1 USUARIO (usuario asociado)

AFILIADO
└─ N INCAPACIDAD (incapacidades del afiliado)

INCAPACIDAD
├─ 0..1 EMPLEADO (ARL solamente)
├─ 0..1 EMPRESA (ARL solamente)
├─ 0..1 AFILIADO (SALUD solamente)
├─ 0..1 SINIESTRO (accidente laboral)
├─ 0..1 SOLICITANTE (quien radica)
├─ N DOCUMENTO (archivos adjuntos)
├─ N HISTORIAL_ESTADO (registro de cambios)
└─ N ORDEN_PAGO (órdenes de pago)

SINIESTRO
├─ 1 EMPLEADO (obligatoria)
├─ 1 EMPRESA (obligatoria)
└─ N INCAPACIDAD (incapacidades relacionadas)

ORDEN_PAGO
├─ 1 INCAPACIDAD (obligatoria)
├─ 0..1 USUARIO (creador)
└─ 0..1 USUARIO (aprobador)

SOLICITANTE
└─ N INCAPACIDAD

DOCUMENTO
├─ 1 INCAPACIDAD (obligatoria, cascada)
└─ 0..1 USUARIO (quien subió)

PRE_INCAPACIDAD
└─ N PRE_DOCUMENTO

HISTORIAL_ESTADO (polimórfico)
└─ 0..1 USUARIO (cambiado_por)

AUDITORIA_LOG
└─ 0..1 USUARIO (quien realizó acción)
```

---

## Flujos de Datos Principales

### Flujo de Radicación (ARL)

```
1. Portal Externo (React) → POST /api/v1/incapacidades/consulta
2. Datos almacenados en PRE_INCAPACIDAD + PRE_DOCUMENTO
3. Job Programado → Procesa y valida
4. Crea INCAPACIDAD + DOCUMENTO
5. HISTORIAL_ESTADO registra: RADICADA
6. AUDITORIA_LOG registra CREATE
7. Sistema Interno → INCAPACIDAD visible para AUDITOR
```

### Flujo de Auditoría

```
1. AUDITOR accede INCAPACIDAD en estado RADICADA
2. Revisa DOCUMENTO y datos
3. AUDITOR decide: APROBADA, OBSERVADA o RECHAZADA
4. Sistema transiciona estado
5. HISTORIAL_ESTADO registra cambio + observación
6. AUDITORIA_LOG registra CAMBIO_ESTADO
7. Si APROBADA → AUDITORIA_DATOS_APROBADOS captura snapshot
8. Si RECHAZADA → AUDITORIA_LOG registra motivo
```

### Flujo de Aprobación y Pago

```
1. INCAPACIDAD estado APROBADA
2. ADMIN genera ORDEN_PAGO
3. ORDEN_PAGO estado GENERADA
4. APROBADOR revisa y aprueba
5. ORDEN_PAGO estado APROBADA
6. Sistema de pagos procesa
7. ORDEN_PAGO estado PAGADA
8. INCAPACIDAD estado EN_PAGO → PAGADA
9. HISTORIAL_ESTADO registra transiciones
```

---

## Estadísticas del Modelo

| Métrica | Valor |
|---------|-------|
| Total de tablas | 17 |
| Entidades principales | 7 (Usuario, Empresa, Empleado, Afiliado, Incapacidad, Siniestro, Orden Pago) |
| Entidades de soporte | 6 |
| Entidades de auditoría | 4 |
| Relaciones 1:N | 18+ |
| Relaciones N:M | 0 |
| Entidades polimórficas | 1 (HistorialEstado) |
| Campos JSONB | 3 |
| Enums PostgreSQL | 12+ |
| Índices | 30+ (PK + FK + especializado) |

---

## Notas Importantes

1. **Tipo de base de datos**: PostgreSQL 15+ con soporte nativo para UUID, JSONB, ENUM
2. **ORM**: SQLAlchemy 2.0 async con tipos mapeados (Mapped, mapped_column)
3. **Integridad referencial**: Relaciones con ON DELETE CASCADE donde aplica
4. **Auditoría**: Campos timestamp (created_at, updated_at) heredados de BaseModel en todas las tablas
5. **Optimización**: Índices en foreign keys y campos de búsqueda frecuente (email, nit, numero_documento, numero_incapacidad)
6. **Escalabilidad**: Estructura de pre-radicación permite procesamiento asíncrono

---

**Documento preparado para audiencia técnica y de negocio**
