# Modelo de Datos - Sistema de Gestión de Incapacidades

## 1. Diagrama de Entidad-Relación

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    EMPRESA      │1       *│   EMPLEADO      │         │    AFILIADO     │
│─────────────────│◄────────┤─────────────────│         │─────────────────│
│ id (PK)         │         │ id (PK)         │         │ id (PK)         │
│ nit             │         │ empresa_id (FK) │         │ numero_poliza   │
│ razon_social    │         │ numero_documento│         │ tipo_poliza     │
│ estado          │         │ tipo_documento  │         │ tipo_documento  │
│ email_contacto  │         │ nombres         │         │ numero_documento│
│ telefono        │         │ apellidos       │         │ nombres         │
│ direccion       │         │ email           │         │ apellidos       │
│ created_at      │         │ telefono        │         │ email           │
│ updated_at      │         │ cargo           │         │ telefono        │
│ sync_source     │         │ fecha_ingreso   │         │ fecha_nacimiento│
│ external_id     │         │ salario_base    │         │ direccion       │
└─────────────────┘         │ estado          │         │ fecha_inicio_pol│
                            │ created_at      │         │ fecha_fin_poliza│
                            │ updated_at      │         │ estado          │
                            │ sync_source     │         │ created_at      │
                            │ external_id     │         │ updated_at      │
                            └─────────────────┘         │ sync_source     │
                                    │1                  │ external_id     │
                                    │                   └─────────────────┘
                                    │*                          │1
                            ┌───────────────────────────────────┤
                            │                                   │*
                            ▼                                   │
                    ┌─────────────────┐                         │
                    │ INCAPACIDAD     │                         │
                ┌───┤─────────────────│◄────────────────────────┘
                │   │ id (PK)         │
                │   │ numero          │
                │   │ empleado_id(FK) │  -- NULL si tipo=SALUD
                │   │ empresa_id (FK) │  -- NULL si tipo=SALUD
                │   │ afiliado_id(FK) │  -- NULL si tipo=ARL
                │   │ siniestro_id(FK)│  -- Solo para ARL
                │   │ solicitante_id  │  -- NUEVO: Quien radica
                │   │ numero_siniestro│
                │   │ tipo            │  -- ARL o SALUD
                │   │ subtipo         │
                │   │ fecha_inicio    │
                │   │ fecha_fin       │
                │   │ dias_totales    │
                │   │ diagnostico_cie10│ -- Validado con CATALOGO_CIE10
                │   │ descripcion_dx  │
                │   │ valor_dia       │
                │   │ valor_total     │
                │   │ estado          │
                │   │ observaciones   │
                │   │ radicado_por_id │
                │   │ auditado_por_id │
                │   │ aprobado_por_id │
                │   │ fecha_radicacion│
                │   │ fecha_auditoria │
                │   │ fecha_aprobacion│
                │   │ created_at      │
                │   │ updated_at      │
                │   └─────────────────┘
                │           │               
                │           │*              ┌──────────────────┐
                │           │               │  SOLICITANTE     │ 
                │           │1              │──────────────────│
                │   ┌─────────────────┐  *  │ id (PK)          │
                │   │   SINIESTRO     │◄────┤ correo (UNIQUE)  │
                │   │─────────────────│     │ nombres          │
                │   │ id (PK)         │     │ apellidos        │
                │   │ numero_siniestro│     │ telefono         │
                │   │ empleado_id(FK) │     │ created_at       │
                │   │ empresa_id (FK) │     │ updated_at       │
                │   │ fecha_siniestro │     └──────────────────┘
                │   │ tipo_siniestro  │             
                │   │ descripcion     │     ┌──────────────────┐
                │   │ parte_cuerpo    │     │ CATALOGO_CIE10   │
                │   │ gravedad        │     │──────────────────│
                │   │ estado          │     │ id (PK)          │
                │   │ created_at      │     │ codigo (UNIQUE)  │
                │   │ updated_at      │     │ descripcion      │
                │   │ sync_source     │     │ created_at       │
                │   │ external_id     │     │ updated_at       │
                │   └─────────────────┘     └──────────────────┘
                │           │1                  ~ 22,000 registros
                │           │                   Full-text search (pg_trgm)
                │           │*
                │   ┌─────────────────┐
                │   │ DOCUMENTO       │
                │   │─────────────────│
                │   │ id (PK)         │
                │   │ incapacidad_id  │
                │   │ tipo_documento  │
                │   │ nombre_archivo  │
                │   │ ruta_storage    │
                │   │ mime_type       │
                │   │ tamanio_bytes   │
                │   │ hash_md5        │
                │   │ uploaded_by_id  │
                │   │ created_at      │
                │   └─────────────────┘
                │
                │           │1
                │           │
                │           │*
                        │   ┌─────────────────┐
                        │   │ HISTORIAL_ESTADO│
                        │   │─────────────────│
                        │   │ id (PK)         │
                        │   │ incapacidad_id  │
                        │   │ estado_anterior │
                        │   │ estado_nuevo    │
                        │   │ observacion     │
                        │   │ cambiado_por_id │
                        │   │ created_at      │
                        │   └─────────────────┘
                        │
                        │           │1
                        │           │
                        │           │*
                        │   ┌─────────────────┐
                        │   │ ORDEN_PAGO      │
                        │   │─────────────────│
                        │   │ id (PK)         │
                        │   │ incapacidad_id  │
                        │   │ numero_orden    │
                        │   │ beneficiario_id │
                        │   │ beneficiario_tipo│
                        │   │ valor_pagar     │
                        │   │ estado_pago     │
                        │   │ fecha_generacion│
                        │   │ fecha_pago      │
                        │   │ metodo_pago     │
                        │   │ referencia_pago │
                        │   │ creado_por_id   │
                        │   │ created_at      │
                        │   │ updated_at      │
                        │   └─────────────────┘
                        │
                        │
┌───────────────────┐ │
│     USUARIO       │ │
│───────────────────│ │
│ id (PK)           │1│
│ username          │◄┘
│ email             │
│ password_hash     │
│ nombre_completo   │
│ rol               │
│ estado            │
│ ultimo_acceso     │
│ intentos_fallidos │
│ bloqueado_hasta   │
│ created_at        │
│ updated_at        │
└───────────────────┘
        │1
        │
        │*
┌───────────────────┐
│   AUDITORIA_LOG   │
│───────────────────│
│ id (PK)           │
│ usuario_id (FK)   │
│ accion            │
│ entidad           │
│ entidad_id        │
│ detalles (JSON)   │
│ ip_address        │
│ user_agent        │
│ created_at        │
└───────────────────┘


┌─────────────────┐
│ TIPO_DOCUMENTO  │
│─────────────────│
│ id (PK)         │
│ codigo          │
│ nombre          │
│ descripcion     │
│ obligatorio     │
│ tipo_incapacidad│
│ activo          │
└─────────────────┘

┌─────────────────┐
│ PARAMETRO       │
│─────────────────│
│ id (PK)         │
│ categoria       │
│ clave           │
│ valor           │
│ descripcion     │
│ tipo_dato       │
│ actualizado_por │
│ updated_at      │
└─────────────────┘
```

## 2. Definición de Tablas

### 2.1 Tabla: EMPRESA

Almacena información de las empresas afiliadas.

```sql
CREATE TABLE empresa (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nit VARCHAR(20) UNIQUE NOT NULL,
    razon_social VARCHAR(255) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA',
    email_contacto VARCHAR(255),
    telefono VARCHAR(20),
    direccion TEXT,
    ciudad VARCHAR(100),
    departamento VARCHAR(100),
    tipo_empresa VARCHAR(50), -- ARL, SALUD, MIXTO
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_source VARCHAR(50), -- API, CSV, MANUAL
    external_id VARCHAR(100),
    metadata JSONB,
    
    CONSTRAINT chk_empresa_estado CHECK (estado IN ('ACTIVA', 'INACTIVA', 'SUSPENDIDA'))
);

CREATE INDEX idx_empresa_nit ON empresa(nit);
CREATE INDEX idx_empresa_estado ON empresa(estado);
CREATE INDEX idx_empresa_sync ON empresa(sync_source, external_id);
```

### 2.2 Tabla: EMPLEADO

Registra los empleados de las empresas.

```sql
CREATE TABLE empleado (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    empresa_id UUID NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,
    numero_documento VARCHAR(20) NOT NULL,
    tipo_documento VARCHAR(10) NOT NULL, -- CC, CE, TI, PASAPORTE
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    telefono VARCHAR(20),
    fecha_nacimiento DATE,
    genero VARCHAR(10),
    cargo VARCHAR(100),
    area VARCHAR(100),
    fecha_ingreso DATE NOT NULL,
    fecha_retiro DATE,
    salario_base DECIMAL(15, 2),
    cuenta_bancaria VARCHAR(50),
    banco VARCHAR(100),
    tipo_cuenta VARCHAR(20), -- AHORROS, CORRIENTE
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_source VARCHAR(50),
    external_id VARCHAR(100),
    metadata JSONB,
    
    CONSTRAINT chk_empleado_estado CHECK (estado IN ('ACTIVO', 'INACTIVO', 'RETIRADO')),
    CONSTRAINT chk_empleado_tipo_doc CHECK (tipo_documento IN ('CC', 'CE', 'TI', 'PASAPORTE', 'PEP')),
    CONSTRAINT uq_empleado_doc_empresa UNIQUE (empresa_id, tipo_documento, numero_documento)
);

CREATE INDEX idx_empleado_empresa ON empleado(empresa_id);
CREATE INDEX idx_empleado_documento ON empleado(tipo_documento, numero_documento);
CREATE INDEX idx_empleado_estado ON empleado(estado);
CREATE INDEX idx_empleado_nombre ON empleado(nombres, apellidos);
CREATE INDEX idx_empleado_sync ON empleado(sync_source, external_id);
```

### 2.3 Tabla: AFILIADO

Registra afiliados con pólizas de salud (no son empleados de empresas).

```sql
CREATE TABLE afiliado (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_poliza VARCHAR(50) UNIQUE NOT NULL,
    tipo_poliza VARCHAR(50) NOT NULL, -- INDIVIDUAL, FAMILIAR, COLECTIVA
    tipo_documento VARCHAR(20) NOT NULL,
    numero_documento VARCHAR(20) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(20),
    fecha_nacimiento DATE,
    genero VARCHAR(1), -- M, F, O
    direccion VARCHAR(200),
    ciudad VARCHAR(100),
    departamento VARCHAR(100),
    fecha_inicio_poliza DATE NOT NULL,
    fecha_fin_poliza DATE,
    cuenta_bancaria VARCHAR(50),
    banco VARCHAR(100),
    tipo_cuenta VARCHAR(20), -- AHORROS, CORRIENTE
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_source VARCHAR(50),
    external_id VARCHAR(100),
    metadata JSONB,
    
    CONSTRAINT chk_afiliado_estado CHECK (estado IN ('ACTIVO', 'INACTIVO', 'SUSPENDIDO')),
    CONSTRAINT chk_afiliado_tipo_doc CHECK (tipo_documento IN ('CC', 'CE', 'TI', 'PASAPORTE', 'PEP')),
    CONSTRAINT chk_afiliado_tipo_poliza CHECK (tipo_poliza IN ('INDIVIDUAL', 'FAMILIAR', 'COLECTIVA')),
    CONSTRAINT chk_afiliado_genero CHECK (genero IN ('M', 'F', 'O')),
    CONSTRAINT chk_afiliado_tipo_cuenta CHECK (tipo_cuenta IN ('AHORROS', 'CORRIENTE'))
);

CREATE INDEX idx_afiliado_poliza ON afiliado(numero_poliza);
CREATE INDEX idx_afiliado_documento ON afiliado(tipo_documento, numero_documento);
CREATE INDEX idx_afiliado_estado ON afiliado(estado);
CREATE INDEX idx_afiliado_nombre ON afiliado(nombres, apellidos);
CREATE INDEX idx_afiliado_sync ON afiliado(sync_source, external_id);
```

### 2.4 Tabla: USUARIO

Gestiona usuarios del sistema (internos y externos).

```sql
CREATE TABLE usuario (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(255) NOT NULL,
    rol VARCHAR(50) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    empleado_id UUID REFERENCES empleado(id) ON DELETE SET NULL,
    empresa_id UUID REFERENCES empresa(id) ON DELETE SET NULL,
    ultimo_acceso TIMESTAMP WITH TIME ZONE,
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta TIMESTAMP WITH TIME ZONE,
    token_version INTEGER DEFAULT 0,
    must_change_password BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_usuario_estado CHECK (estado IN ('ACTIVO', 'INACTIVO', 'BLOQUEADO')),
    CONSTRAINT chk_usuario_rol CHECK (rol IN ('ADMIN', 'AUDITOR', 'APROBADOR', 'EMPRESA', 'EMPLEADO', 'READONLY'))
);

CREATE INDEX idx_usuario_username ON usuario(username);
CREATE INDEX idx_usuario_email ON usuario(email);
CREATE INDEX idx_usuario_rol ON usuario(rol);
CREATE INDEX idx_usuario_empresa ON usuario(empresa_id);
```

### 2.5 Tabla: SOLICITANTE

Almacena datos de personas que radican incapacidades (independiente de empleados/afiliados).

```sql
CREATE TABLE solicitante (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correo VARCHAR(100) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_solicitante_correo CHECK (correo ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'),
    CONSTRAINT chk_solicitante_nombres CHECK (nombres ~* '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,100}$'),
    CONSTRAINT chk_solicitante_apellidos CHECK (apellidos ~* '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,100}$'),
    CONSTRAINT chk_solicitante_telefono CHECK (telefono IS NULL OR telefono ~* '^\d{7,20}$')
);

CREATE UNIQUE INDEX idx_solicitante_correo ON solicitante(correo);
CREATE INDEX idx_solicitante_correo_search ON solicitante(correo varchar_pattern_ops);

-- Trigger para actualizar updated_at
CREATE TRIGGER update_solicitante_updated_at
    BEFORE UPDATE ON solicitante
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Relación con Incapacidad**:
- Un solicitante puede radicar múltiples incapacidades
- El campo `solicitante_id` en incapacidad es opcional (puede ser NULL para radicaciones internas)

### 2.6 Tabla: CATALOGO_CIE10

Catálogo oficial de códigos CIE-10 (Clasificación Internacional de Enfermedades, 10ª revisión).

```sql
CREATE TABLE catalogo_cie10 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(10) UNIQUE NOT NULL,
    descripcion VARCHAR(500) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_cie10_codigo CHECK (codigo ~* '^[A-Z]\d{3}(\.\d{1,2})?$')
);

CREATE UNIQUE INDEX idx_catalogo_cie10_codigo ON catalogo_cie10(codigo);

-- Índice GIN para full-text search en descripción
CREATE INDEX idx_catalogo_cie10_descripcion_gin 
ON catalogo_cie10 USING GIN (to_tsvector('spanish', descripcion));

-- Índice trigram para búsqueda parcial (requiere extensión pg_trgm)
CREATE INDEX idx_catalogo_cie10_descripcion_trgm 
ON catalogo_cie10 USING GIN (descripcion gin_trgm_ops);

-- Trigger para actualizar updated_at
CREATE TRIGGER update_catalogo_cie10_updated_at
    BEFORE UPDATE ON catalogo_cie10
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Extensión PostgreSQL Requerida**:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

**Datos**:
- Aproximadamente 22,000 códigos CIE-10
- Carga inicial mediante script `seed_cie10.py`
- Formato: código (ej: "A00", "A00.0") + descripción

### 2.7 Tabla: INCAPACIDAD

Tabla principal de incapacidades (ARL y SALUD).

**Nota importante**: 
- Incapacidades **ARL**: Requieren `empleado_id` y `empresa_id`, pueden tener `siniestro_id`
- Incapacidades **SALUD**: Requieren `afiliado_id`, NO tienen empleado/empresa/siniestro

```sql
CREATE TABLE incapacidad (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero VARCHAR(50) UNIQUE NOT NULL,
    -- Relaciones condicionales según tipo
    empleado_id UUID REFERENCES empleado(id), -- NULL si tipo=SALUD
    empresa_id UUID REFERENCES empresa(id), -- NULL si tipo=SALUD
    afiliado_id UUID REFERENCES afiliado(id), -- NULL si tipo=ARL
    siniestro_id UUID REFERENCES siniestro(id), -- Solo para ARL
    numero_siniestro VARCHAR(50), -- Solo para ARL: referencia al número de siniestro
    solicitante_id UUID REFERENCES solicitante(id) ON DELETE SET NULL, -- NUEVO: Persona que radica
    tipo VARCHAR(20) NOT NULL, -- ARL, SALUD
    subtipo VARCHAR(50), -- ENFERMEDAD_GENERAL, ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, etc.
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    dias_totales INTEGER NOT NULL,
    diagnostico_cie10 VARCHAR(10), -- Código CIE-10 (valida con catalogo_cie10)
    descripcion_diagnostico TEXT,
    eps VARCHAR(255),
    ips VARCHAR(255),
    valor_dia DECIMAL(15, 2),
    valor_total DECIMAL(15, 2),
    estado VARCHAR(30) NOT NULL DEFAULT 'RADICADA',
    observaciones TEXT,
    motivo_rechazo TEXT,
    radicado_por_id UUID REFERENCES usuario(id),
    auditado_por_id UUID REFERENCES usuario(id),
    aprobado_por_id UUID REFERENCES usuario(id),
    fecha_radicacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_auditoria TIMESTAMP WITH TIME ZONE,
    fecha_aprobacion TIMESTAMP WITH TIME ZONE,
    fecha_rechazo TIMESTAMP WITH TIME ZONE,
    prioridad VARCHAR(20) DEFAULT 'NORMAL',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    CONSTRAINT chk_incapacidad_tipo CHECK (tipo IN ('ARL', 'SALUD')),
    CONSTRAINT chk_incapacidad_estado CHECK (estado IN (
        'RADICADA', 'EN_AUDITORIA', 'OBSERVADA', 'APROBADA', 
        'RECHAZADA', 'EN_PAGO', 'PAGADA', 'CANCELADA'
    )),
    CONSTRAINT chk_incapacidad_prioridad CHECK (prioridad IN ('BAJA', 'NORMAL', 'ALTA', 'URGENTE')),
    CONSTRAINT chk_incapacidad_fechas CHECK (fecha_fin >= fecha_inicio),
    -- Validar relación correcta según tipo
    CONSTRAINT chk_incapacidad_tipo_relacion CHECK (
        (tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL) OR
        (tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)
    )
);

CREATE INDEX idx_incapacidad_numero ON incapacidad(numero);
CREATE INDEX idx_incapacidad_empleado ON incapacidad(empleado_id);
CREATE INDEX idx_incapacidad_empresa ON incapacidad(empresa_id);
CREATE INDEX idx_incapacidad_afiliado ON incapacidad(afiliado_id);
CREATE INDEX idx_incapacidad_siniestro ON incapacidad(siniestro_id);
CREATE INDEX idx_incapacidad_numero_siniestro ON incapacidad(numero_siniestro);
CREATE INDEX idx_incapacidad_solicitante ON incapacidad(solicitante_id);
CREATE INDEX idx_incapacidad_estado ON incapacidad(estado);
CREATE INDEX idx_incapacidad_tipo ON incapacidad(tipo);
CREATE INDEX idx_incapacidad_fecha_radicacion ON incapacidad(fecha_radicacion);
CREATE INDEX idx_incapacidad_fecha_inicio ON incapacidad(fecha_inicio);
CREATE INDEX idx_incapacidad_auditado_por ON incapacidad(auditado_por_id);
```

### 2.8 Tabla: DOCUMENTO

Almacena referencias a documentos adjuntos.

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_documento_tipo CHECK (tipo_documento IN (
        'INCAPACIDAD_MEDICA', 'CEDULA', 'HISTORIA_CLINICA', 
        'SOPORTE_PAGO', 'OTROS'
    ))
);

CREATE INDEX idx_documento_incapacidad ON documento(incapacidad_id);
CREATE INDEX idx_documento_tipo ON documento(tipo_documento);
CREATE INDEX idx_documento_hash ON documento(hash_sha256);
```

### 2.9 Tabla: SINIESTRO

Registra los siniestros laborales (accidentes de trabajo) reportados.

```sql
CREATE TABLE siniestro (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_siniestro VARCHAR(50) UNIQUE NOT NULL,
    empleado_id UUID NOT NULL REFERENCES empleado(id),
    empresa_id UUID NOT NULL REFERENCES empresa(id),
    fecha_siniestro DATE NOT NULL,
    hora_siniestro TIME,
    tipo_siniestro VARCHAR(50) NOT NULL, -- ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, ACCIDENTE_TRAYECTO
    descripcion TEXT NOT NULL,
    lugar_ocurrencia VARCHAR(255),
    parte_cuerpo_afectada VARCHAR(100), -- Cabeza, Tórax, Extremidades, etc.
    naturaleza_lesion VARCHAR(100), -- Fractura, Contusión, Herida, etc.
    agente_causante VARCHAR(255), -- Máquina, herramienta, sustancia, etc.
    gravedad VARCHAR(20) DEFAULT 'LEVE', -- LEVE, MODERADO, GRAVE, MORTAL
    testigos TEXT, -- Nombres de testigos
    requirio_hospitalizacion BOOLEAN DEFAULT FALSE,
    dias_estimados_incapacidad INTEGER,
    estado VARCHAR(20) NOT NULL DEFAULT 'REPORTADO', -- REPORTADO, EN_INVESTIGACION, CERRADO
    fecha_reporte TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reportado_por VARCHAR(255),
    observaciones TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_source VARCHAR(50), -- API, CSV, MANUAL
    external_id VARCHAR(100), -- ID del sistema externo
    metadata JSONB,
    
    CONSTRAINT chk_siniestro_tipo CHECK (tipo_siniestro IN (
        'ACCIDENTE_TRABAJO', 'ENFERMEDAD_LABORAL', 'ACCIDENTE_TRAYECTO'
    )),
    CONSTRAINT chk_siniestro_gravedad CHECK (gravedad IN (
        'LEVE', 'MODERADO', 'GRAVE', 'MORTAL'
    )),
    CONSTRAINT chk_siniestro_estado CHECK (estado IN (
        'REPORTADO', 'EN_INVESTIGACION', 'CERRADO', 'ANULADO'
    ))
);

CREATE INDEX idx_siniestro_numero ON siniestro(numero_siniestro);
CREATE INDEX idx_siniestro_empleado ON siniestro(empleado_id);
CREATE INDEX idx_siniestro_empresa ON siniestro(empresa_id);
CREATE INDEX idx_siniestro_fecha ON siniestro(fecha_siniestro);
CREATE INDEX idx_siniestro_tipo ON siniestro(tipo_siniestro);
CREATE INDEX idx_siniestro_estado ON siniestro(estado);
CREATE INDEX idx_siniestro_sync ON siniestro(sync_source, external_id);
```

### 2.10 Tabla: HISTORIAL_ESTADO

Auditoría de cambios de estado.

```sql
CREATE TABLE historial_estado (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incapacidad_id UUID NOT NULL REFERENCES incapacidad(id) ON DELETE CASCADE,
    estado_anterior VARCHAR(30),
    estado_nuevo VARCHAR(30) NOT NULL,
    observacion TEXT,
    cambiado_por_id UUID REFERENCES usuario(id),
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_historial_incapacidad ON historial_estado(incapacidad_id);
CREATE INDEX idx_historial_created_at ON historial_estado(created_at DESC);
```

### 2.11 Tabla: ORDEN_PAGO

Órdenes de pago generadas.

```sql
CREATE TABLE orden_pago (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_orden VARCHAR(50) UNIQUE NOT NULL,
    incapacidad_id UUID NOT NULL REFERENCES incapacidad(id),
    beneficiario_tipo VARCHAR(20) NOT NULL, -- EMPLEADO, EMPRESA
    beneficiario_id UUID NOT NULL,
    beneficiario_nombre VARCHAR(255) NOT NULL,
    beneficiario_documento VARCHAR(50) NOT NULL,
    cuenta_bancaria VARCHAR(50),
    banco VARCHAR(100),
    tipo_cuenta VARCHAR(20),
    valor_pagar DECIMAL(15, 2) NOT NULL,
    estado_pago VARCHAR(30) NOT NULL DEFAULT 'GENERADA',
    fecha_generacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_pago TIMESTAMP WITH TIME ZONE,
    fecha_anulacion TIMESTAMP WITH TIME ZONE,
    metodo_pago VARCHAR(50),
    referencia_pago VARCHAR(100),
    comprobante_ruta VARCHAR(500),
    motivo_anulacion TEXT,
    creado_por_id UUID REFERENCES usuario(id),
    aprobado_por_id UUID REFERENCES usuario(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_orden_beneficiario_tipo CHECK (beneficiario_tipo IN ('EMPLEADO', 'EMPRESA', 'IPS')),
    CONSTRAINT chk_orden_estado CHECK (estado_pago IN (
        'GENERADA', 'APROBADA', 'EN_PROCESO', 'PAGADA', 'RECHAZADA', 'ANULADA'
    ))
);

CREATE INDEX idx_orden_numero ON orden_pago(numero_orden);
CREATE INDEX idx_orden_incapacidad ON orden_pago(incapacidad_id);
CREATE INDEX idx_orden_estado ON orden_pago(estado_pago);
CREATE INDEX idx_orden_beneficiario ON orden_pago(beneficiario_id);
CREATE INDEX idx_orden_fecha_generacion ON orden_pago(fecha_generacion);
```

### 2.12 Tabla: AUDITORIA_LOG

Log de auditoría completo.

```sql
CREATE TABLE auditoria_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuario(id),
    accion VARCHAR(50) NOT NULL,
    entidad VARCHAR(50) NOT NULL,
    entidad_id UUID,
    detalles JSONB,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auditoria_usuario ON auditoria_log(usuario_id);
CREATE INDEX idx_auditoria_entidad ON auditoria_log(entidad, entidad_id);
CREATE INDEX idx_auditoria_accion ON auditoria_log(accion);
CREATE INDEX idx_auditoria_created_at ON auditoria_log(created_at DESC);
CREATE INDEX idx_auditoria_detalles ON auditoria_log USING gin(detalles);
```

### 2.13 Tabla: TIPO_DOCUMENTO (Catálogo)

Define tipos de documentos requeridos.

```sql
CREATE TABLE tipo_documento_catalogo (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    obligatorio BOOLEAN DEFAULT FALSE,
    tipo_incapacidad VARCHAR(20), -- ARL, SALUD, AMBOS
    extensiones_permitidas VARCHAR[] DEFAULT ARRAY['pdf', 'jpg', 'png'],
    tamanio_max_mb INTEGER DEFAULT 10,
    activo BOOLEAN DEFAULT TRUE,
    orden INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tipo_doc_codigo ON tipo_documento_catalogo(codigo);
CREATE INDEX idx_tipo_doc_activo ON tipo_documento_catalogo(activo);
```

### 2.14 Tabla: PARAMETRO (Configuración)

Parámetros configurables del sistema.

```sql
CREATE TABLE parametro (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    categoria VARCHAR(50) NOT NULL,
    clave VARCHAR(100) NOT NULL,
    valor TEXT NOT NULL,
    descripcion TEXT,
    tipo_dato VARCHAR(20) DEFAULT 'STRING', -- STRING, INTEGER, DECIMAL, BOOLEAN, JSON
    editable BOOLEAN DEFAULT TRUE,
    actualizado_por_id UUID REFERENCES usuario(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_parametro_categoria_clave UNIQUE (categoria, clave)
);

CREATE INDEX idx_parametro_categoria ON parametro(categoria);
```

## 3. Relaciones y Cardinalidad

- **EMPRESA → EMPLEADO**: 1:N (Una empresa tiene múltiples empleados)
- **EMPRESA → SINIESTRO**: 1:N (Una empresa puede tener múltiples siniestros)
- **EMPLEADO → SINIESTRO**: 1:N (Un empleado puede tener múltiples siniestros)
- **EMPLEADO → INCAPACIDAD**: 1:N (Un empleado puede tener múltiples incapacidades)
- **EMPRESA → INCAPACIDAD**: 1:N (Una empresa tiene múltiples incapacidades)
- **SINIESTRO → INCAPACIDAD**: 1:N (Un siniestro puede generar múltiples incapacidades)
- **INCAPACIDAD → DOCUMENTO**: 1:N (Una incapacidad tiene múltiples documentos)
- **INCAPACIDAD → HISTORIAL_ESTADO**: 1:N (Trazabilidad completa)
- **INCAPACIDAD → ORDEN_PAGO**: 1:N (Puede generar múltiples órdenes)
- **USUARIO → AUDITORIA_LOG**: 1:N (Registro de todas las acciones)

## 4. Secuencias y Triggers

### 4.1 Generación Automática de Número de Incapacidad

```sql
CREATE SEQUENCE seq_incapacidad_numero START 100000;

CREATE OR REPLACE FUNCTION generar_numero_incapacidad()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.numero IS NULL THEN
        NEW.numero := 'INC-' || TO_CHAR(CURRENT_DATE, 'YYYYMM') || '-' || 
                      LPAD(nextval('seq_incapacidad_numero')::TEXT, 6, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_generar_numero_incapacidad
    BEFORE INSERT ON incapacidad
    FOR EACH ROW
    EXECUTE FUNCTION generar_numero_incapacidad();
```

### 4.2 Actualización Automática de updated_at

```sql
CREATE OR REPLACE FUNCTION actualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_empresa_updated_at
    BEFORE UPDATE ON empresa
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_updated_at();

CREATE TRIGGER trigger_empleado_updated_at
    BEFORE UPDATE ON empleado
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_updated_at();

CREATE TRIGGER trigger_usuario_updated_at
    BEFORE UPDATE ON usuario
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_updated_at();

CREATE TRIGGER trigger_incapacidad_updated_at
    BEFORE UPDATE ON incapacidad
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_updated_at();
```

### 4.3 Registro Automático en Historial de Estados

```sql
CREATE OR REPLACE FUNCTION registrar_cambio_estado()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.estado IS DISTINCT FROM OLD.estado THEN
        INSERT INTO historial_estado (
            incapacidad_id, 
            estado_anterior, 
            estado_nuevo,
            cambiado_por_id
        ) VALUES (
            NEW.id,
            OLD.estado,
            NEW.estado,
            NEW.auditado_por_id
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_registrar_cambio_estado
    AFTER UPDATE ON incapacidad
    FOR EACH ROW
    EXECUTE FUNCTION registrar_cambio_estado();
```

### 4.4 Registro Automático en Historial al momento de radicar una incapacidad
```sql
CREATE OR REPLACE FUNCTION registrar_radicacion_incapacidad()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO historial_estado (
        incapacidad_id, 
        estado_anterior, 
        estado_nuevo,
        cambiado_por_id
    ) VALUES (
        NEW.id,
        NULL,
        NEW.estado,
        NEW.radicado_por_id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_registrar_radicacion_incapacidad
    AFTER INSERT ON incapacidad
    FOR EACH ROW
    EXECUTE FUNCTION registrar_radicacion_incapacidad();
```

## 5. Vistas Útiles

### 5.1 Vista: Incapacidades con Información Completa

```sql
CREATE OR REPLACE VIEW v_incapacidades_completas AS
SELECT 
    i.id,
    i.numero,
    i.tipo,
    i.estado,
    i.fecha_inicio,
    i.fecha_fin,
    i.dias_totales,
    i.valor_total,
    i.fecha_radicacion,
    
    -- Información del empleado
    e.numero_documento as empleado_documento,
    e.tipo_documento as empleado_tipo_doc,
    e.nombres || ' ' || e.apellidos as empleado_nombre_completo,
    e.email as empleado_email,
    
    -- Información de la empresa
    emp.nit as empresa_nit,
    emp.razon_social as empresa_nombre,
    emp.email_contacto as empresa_email,
    
    -- Información de usuarios
    u_radicado.nombre_completo as radicado_por,
    u_auditado.nombre_completo as auditado_por,
    u_aprobado.nombre_completo as aprobado_por,
    
    -- Conteo de documentos
    (SELECT COUNT(*) FROM documento d WHERE d.incapacidad_id = i.id) as total_documentos,
    
    -- Estado de pago
    (SELECT estado_pago FROM orden_pago op 
     WHERE op.incapacidad_id = i.id 
     ORDER BY created_at DESC LIMIT 1) as ultimo_estado_pago
     
FROM incapacidad i
INNER JOIN empleado e ON i.empleado_id = e.id
INNER JOIN empresa emp ON i.empresa_id = emp.id
LEFT JOIN usuario u_radicado ON i.radicado_por_id = u_radicado.id
LEFT JOIN usuario u_auditado ON i.auditado_por_id = u_auditado.id
LEFT JOIN usuario u_aprobado ON i.aprobado_por_id = u_aprobado.id;
```

### 5.2 Vista: Estadísticas por Empresa

```sql
CREATE OR REPLACE VIEW v_estadisticas_empresa AS
SELECT 
    emp.id,
    emp.nit,
    emp.razon_social,
    COUNT(DISTINCT e.id) as total_empleados,
    COUNT(DISTINCT i.id) as total_incapacidades,
    COUNT(DISTINCT i.id) FILTER (WHERE i.estado = 'RADICADA') as incap_radicadas,
    COUNT(DISTINCT i.id) FILTER (WHERE i.estado = 'EN_AUDITORIA') as incap_en_auditoria,
    COUNT(DISTINCT i.id) FILTER (WHERE i.estado = 'APROBADA') as incap_aprobadas,
    COUNT(DISTINCT i.id) FILTER (WHERE i.estado = 'RECHAZADA') as incap_rechazadas,
    COALESCE(SUM(i.valor_total) FILTER (WHERE i.estado = 'APROBADA'), 0) as valor_total_aprobado
FROM empresa emp
LEFT JOIN empleado e ON emp.id = e.empresa_id
LEFT JOIN incapacidad i ON e.id = i.empleado_id
GROUP BY emp.id, emp.nit, emp.razon_social;
```

## 6. Índices de Rendimiento

```sql
-- Búsqueda full-text en incapacidades
CREATE INDEX idx_incapacidad_fulltext ON incapacidad 
USING gin(to_tsvector('spanish', 
    COALESCE(descripcion_diagnostico, '') || ' ' || 
    COALESCE(observaciones, '')
));

-- Búsqueda por rango de fechas (particionado)
CREATE INDEX idx_incapacidad_fecha_inicio_btree ON incapacidad 
USING btree(fecha_inicio);

-- Índice compuesto para queries frecuentes
CREATE INDEX idx_incapacidad_empresa_estado_fecha ON incapacidad(empresa_id, estado, fecha_radicacion DESC);

-- JSON indexes para metadata
CREATE INDEX idx_incapacidad_metadata ON incapacidad USING gin(metadata);
CREATE INDEX idx_empresa_metadata ON empresa USING gin(metadata);
```

## 7. Particionamiento (Escalabilidad)

Para grandes volúmenes, particionar por fecha:

```sql
-- Crear tabla particionada
CREATE TABLE incapacidad_partitioned (
    LIKE incapacidad INCLUDING ALL
) PARTITION BY RANGE (fecha_radicacion);

-- Crear particiones por año
CREATE TABLE incapacidad_2024 PARTITION OF incapacidad_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE incapacidad_2025 PARTITION OF incapacidad_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE incapacidad_2026 PARTITION OF incapacidad_partitioned
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
```

## 8. Políticas de Retención

```sql
-- Archivar incapacidades de más de 5 años
CREATE TABLE incapacidad_archivo (LIKE incapacidad INCLUDING ALL);

-- Procedimiento de archivado
CREATE OR REPLACE FUNCTION archivar_incapacidades_antiguas()
RETURNS INTEGER AS $$
DECLARE
    registros_archivados INTEGER;
BEGIN
    WITH archivadas AS (
        DELETE FROM incapacidad
        WHERE fecha_radicacion < CURRENT_DATE - INTERVAL '5 years'
        AND estado IN ('PAGADA', 'RECHAZADA', 'CANCELADA')
        RETURNING *
    )
    INSERT INTO incapacidad_archivo
    SELECT * FROM archivadas;
    
    GET DIAGNOSTICS registros_archivados = ROW_COUNT;
    RETURN registros_archivados;
END;
$$ LANGUAGE plpgsql;
```
