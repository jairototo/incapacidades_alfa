# Guía Rápida: Aplicación de Migraciones

Esta guía te ayudará a aplicar las migraciones de base de datos para el sistema de incapacidades.

## ⚡ Inicio Rápido

### 1. Verificar Estado

```bash
cd backend
python scripts/check_migrations.py
```

### 2. Aplicar Migraciones

#### Con Docker (Recomendado)

```bash
# Asegúrate de que los contenedores estén corriendo
docker compose up -d

# Aplicar migraciones
docker compose exec api alembic upgrade head

# Verificar estado
docker compose exec api alembic current
```

#### Sin Docker (Desarrollo Local)

```bash
# Asegúrate de que PostgreSQL esté corriendo
# y que DATABASE_URL esté configurado en .env

# Aplicar migraciones
alembic upgrade head

# O usando Make
make upgrade-db
```

## 📋 Detalles de la Migración Inicial

La migración `001_initial_schema` crea:

### Tablas Creadas (10)

1. ✅ **empresa** - Empresas afiliadas
2. ✅ **empleado** - Empleados de empresas (ARL)
3. ✅ **afiliado** - Afiliados con pólizas (SALUD) ⭐ NUEVO
4. ✅ **usuario** - Usuarios del sistema
5. ✅ **siniestro** - Siniestros laborales
6. ✅ **incapacidad** - Incapacidades ARL/SALUD ⭐
7. ✅ **documento** - Documentos adjuntos
8. ✅ **historial_estado** - Auditoría de estados
9. ✅ **orden_pago** - Órdenes de pago
10. ✅ **auditoria_log** - Log de auditoría

### Características Importantes

#### Soporte Polimórfico

La tabla `incapacidad` soporta dos tipos:

**ARL** (Riesgos Laborales):
- ✅ Requiere `empleado_id` y `empresa_id`
- ✅ Puede tener `siniestro_id` (opcional)
- ✅ Beneficiario: Empleado o Empresa

**SALUD** (Pólizas de Salud):
- ✅ Requiere `afiliado_id`
- ❌ NO tiene `empleado_id`, `empresa_id` ni `siniestro_id`
- ✅ Beneficiario: Afiliado

#### Constraint Crítico de Integridad

```sql
CHECK (
  (tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL) 
  OR 
  (tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)
)
```

Este constraint garantiza que:
- Las incapacidades ARL siempre tienen empleado y empresa
- Las incapacidades SALUD siempre tienen afiliado
- Nunca se mezclan ambos tipos

## 🔍 Verificación Post-Migración

### 1. Verificar que las tablas fueron creadas

```sql
-- Conectar a PostgreSQL
psql -h localhost -p 5442 -U incapacidades_user -d incapacidades_db

-- Listar tablas
\dt

-- Deberías ver:
-- empresa, empleado, afiliado, usuario, siniestro, incapacidad,
-- documento, historial_estado, orden_pago, auditoria_log, alembic_version
```

### 2. Verificar tabla afiliado

```sql
\d afiliado

-- Debe tener:
-- - id (UUID, PK)
-- - numero_poliza (VARCHAR(50), UNIQUE)
-- - tipo_poliza (VARCHAR(50))
-- - tipo_documento, numero_documento
-- - nombres, apellidos, email, telefono
-- - fecha_nacimiento, genero
-- - direccion, ciudad, departamento
-- - fecha_inicio_poliza, fecha_fin_poliza (DATES)
-- - cuenta_bancaria, banco, tipo_cuenta
-- - estado (VARCHAR(20))
-- - created_at, updated_at (TIMESTAMPS)
-- - sync_source, external_id, metadata (JSONB)
```

### 3. Verificar tabla incapacidad

```sql
\d incapacidad

-- Verificar campos polimórficos:
-- - empleado_id (UUID, NULL) -- Para ARL
-- - empresa_id (UUID, NULL)  -- Para ARL
-- - afiliado_id (UUID, NULL) -- Para SALUD
-- - siniestro_id (UUID, NULL) -- Solo ARL
-- - tipo (VARCHAR(20)) -- 'ARL' o 'SALUD'
```

### 4. Verificar constraints

```sql
-- Ver constraints de incapacidad
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'incapacidad'::regclass;

-- Debe incluir:
-- - chk_incapacidad_tipo_relacion (el constraint polimórfico)
-- - chk_incapacidad_tipo (tipo IN ('ARL', 'SALUD'))
-- - chk_incapacidad_estado
-- - chk_incapacidad_fechas
```

### 5. Verificar índices

```sql
-- Ver índices de incapacidad
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'incapacidad';

-- Debe incluir:
-- - idx_incapacidad_empleado
-- - idx_incapacidad_empresa
-- - idx_incapacidad_afiliado (NUEVO)
-- - idx_incapacidad_tipo
-- - idx_incapacidad_estado
```

### 6. Verificar índices de afiliado

```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'afiliado';

-- Debe incluir:
-- - idx_afiliado_poliza (numero_poliza)
-- - idx_afiliado_documento
-- - idx_afiliado_estado
-- - idx_afiliado_nombre
```

## 🧪 Pruebas de Integridad

### Prueba 1: Crear Afiliado

```sql
INSERT INTO afiliado (
    numero_poliza, tipo_poliza, tipo_documento, numero_documento,
    nombres, apellidos, fecha_inicio_poliza, estado
) VALUES (
    'POL-2026-001', 'INDIVIDUAL', 'CC', '1234567890',
    'Juan', 'Pérez', '2026-01-01', 'ACTIVO'
);

-- Debe funcionar correctamente
```

### Prueba 2: Crear Incapacidad SALUD (requiere afiliado)

```sql
-- Primero obtener el ID del afiliado creado
SELECT id FROM afiliado WHERE numero_poliza = 'POL-2026-001';

-- Crear incapacidad SALUD
INSERT INTO incapacidad (
    numero, tipo, afiliado_id, fecha_inicio, fecha_fin, dias_totales
) VALUES (
    'INC-SALUD-001', 'SALUD', '<afiliado_id>', '2026-01-10', '2026-01-15', 5
);

-- Debe funcionar correctamente
```

### Prueba 3: Intentar crear SALUD con empleado (debe fallar)

```sql
-- Esto DEBE FALLAR por el constraint
INSERT INTO incapacidad (
    numero, tipo, empleado_id, empresa_id, afiliado_id, 
    fecha_inicio, fecha_fin, dias_totales
) VALUES (
    'INC-BAD-001', 'SALUD', '<some_uuid>', '<some_uuid>', '<afiliado_id>',
    '2026-01-10', '2026-01-15', 5
);

-- Error esperado: violación del constraint chk_incapacidad_tipo_relacion
```

### Prueba 4: Verificar FKs en cascada

```sql
-- Eliminar un afiliado debe eliminar sus incapacidades
DELETE FROM afiliado WHERE numero_poliza = 'POL-2026-001';

-- Las incapacidades asociadas deben eliminarse automáticamente (CASCADE)
SELECT COUNT(*) FROM incapacidad WHERE afiliado_id = '<afiliado_id>';
-- Debe retornar 0
```

## 🔧 Troubleshooting

### Error: "relation already exists"

Esto significa que las tablas ya existen. Opciones:

```bash
# Opción 1: Marcar como aplicada (si las tablas están correctas)
alembic stamp head

# Opción 2: Recrear base de datos
alembic downgrade base
alembic upgrade head
```

### Error: "Can't locate revision"

```bash
# Verificar historial
alembic history

# Marcar como base
alembic stamp base

# Aplicar migraciones
alembic upgrade head
```

### Error de conexión a PostgreSQL

```bash
# Verificar que el contenedor esté corriendo
docker compose ps

# Ver logs de PostgreSQL
docker compose logs postgres

# Verificar variables de entorno
cat .env | grep DATABASE_URL
```

### Base de datos no inicializada

```bash
# Verificar que PostgreSQL acepte conexiones
psql -h localhost -p 5442 -U incapacidades_user -d incapacidades_db -c "\dt"

# Si no existe la base de datos, el contenedor debe crearla automáticamente
# al iniciarse. Verifica docker-compose.yml
```

## 📚 Próximos Pasos

Después de aplicar las migraciones:

1. ✅ **Datos de prueba** - Crear scripts para poblar datos iniciales
2. ✅ **Repositories** - Implementar AfiliadoRepository
3. ✅ **Services** - Implementar AfiliadoService
4. ✅ **API Endpoints** - Crear /api/v1/afiliados
5. ✅ **Tests** - Crear tests para Afiliado y validaciones polimórficas

## 🔗 Referencias

- [CAMBIOS_ARL_SALUD.md](../CAMBIOS_ARL_SALUD.md) - Documentación completa de cambios
- [alembic/README.md](alembic/README.md) - Documentación de Alembic
- [docs/02_MODELO_DATOS.md](../docs/02_MODELO_DATOS.md) - Modelo de datos actualizado
- [docs/03_API_ENDPOINTS.md](../docs/03_API_ENDPOINTS.md) - Endpoints actualizados
