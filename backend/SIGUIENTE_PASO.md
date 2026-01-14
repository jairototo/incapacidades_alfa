# ✅ Implementación de Migraciones Alembic - COMPLETADA

## 🎉 ¿Qué se implementó?

Se ha configurado completamente **Alembic** para el proyecto con una migración inicial que incluye:

### Archivos Creados (8)

1. ✅ `alembic.ini` - Configuración principal
2. ✅ `alembic/env.py` - Configuración async para SQLAlchemy 2.0
3. ✅ `alembic/script.py.mako` - Template para migraciones
4. ✅ `alembic/versions/20260106_1000_001_initial_schema.py` - **Migración inicial (600+ líneas)**
5. ✅ `alembic/README.md` - Documentación completa de Alembic
6. ✅ `MIGRACION_INICIAL.md` - Guía paso a paso
7. ✅ `scripts/check_migrations.py` - Script de verificación
8. ✅ `RESUMEN_MIGRACIONES.md` - Resumen técnico completo

### Esquema de Base de Datos

**10 tablas creadas** con ~50 índices optimizados:

1. ✅ `empresa` - Empresas afiliadas
2. ✅ `empleado` - Empleados (para incapacidades ARL)
3. ✅ `afiliado` - **Afiliados con pólizas (para incapacidades SALUD)** ⭐ NUEVO
4. ✅ `usuario` - Usuarios del sistema (RBAC)
5. ✅ `siniestro` - Siniestros laborales
6. ✅ `incapacidad` - **Con soporte polimórfico ARL/SALUD** ⭐ MODIFICADO
7. ✅ `documento` - Documentos adjuntos
8. ✅ `historial_estado` - Auditoría de estados
9. ✅ `orden_pago` - Órdenes de pago
10. ✅ `auditoria_log` - Log de auditoría completo

## 🚀 Próximo Paso: Aplicar la Migración

### Opción 1: Con Docker (Recomendado)

```bash
# 1. Asegurarte de que los servicios estén corriendo
cd /opt/apps/incapacidades_vs/backend
docker compose up -d

# 2. Verificar estado actual
docker compose exec api python scripts/check_migrations.py

# 3. Aplicar la migración
docker compose exec api alembic upgrade head

# 4. Verificar que se aplicó correctamente
docker compose exec api alembic current

# Debería mostrar: 001_initial_schema (head)
```

### Opción 2: Local (si tienes Python configurado)

```bash
# 1. Asegurarte de que PostgreSQL esté corriendo en puerto 5442
# 2. Verificar que DATABASE_URL en .env sea correcto

cd /opt/apps/incapacidades_vs/backend

# 3. Verificar estado
python scripts/check_migrations.py

# 4. Aplicar migración
alembic upgrade head
# O usando Make:
make upgrade-db

# 5. Verificar
alembic current
```

## 🔍 Verificación Post-Migración

### Verificar que las tablas fueron creadas

```bash
# Conectar a PostgreSQL
docker compose exec postgres psql -U incapacidades_user -d incapacidades_db

# O si tienes psql instalado localmente:
psql -h localhost -p 5442 -U incapacidades_user -d incapacidades_db
```

```sql
-- Listar todas las tablas
\dt

-- Deberías ver:
-- empresa, empleado, afiliado, usuario, siniestro, incapacidad,
-- documento, historial_estado, orden_pago, auditoria_log, alembic_version

-- Ver estructura de afiliado (nueva tabla)
\d afiliado

-- Ver estructura de incapacidad (modificada)
\d incapacidad

-- Verificar el constraint polimórfico
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'incapacidad'::regclass 
AND conname = 'chk_incapacidad_tipo_relacion';

-- Debería mostrar el constraint que valida ARL vs SALUD
```

## 📋 Documentación Disponible

### Para aplicar la migración

📄 **[MIGRACION_INICIAL.md](MIGRACION_INICIAL.md)**
- Guía paso a paso para aplicar migraciones
- Comandos de verificación
- Pruebas de integridad con SQL
- Troubleshooting

### Para entender Alembic

📄 **[alembic/README.md](alembic/README.md)**
- Comandos frecuentes de Alembic
- Cómo crear nuevas migraciones
- Best practices
- Troubleshooting

### Detalles técnicos

📄 **[RESUMEN_MIGRACIONES.md](RESUMEN_MIGRACIONES.md)**
- Estadísticas completas (177 columnas, 50 índices)
- Características implementadas
- Validaciones a nivel DB
- Notas técnicas

### Cambios arquitectónicos

📄 **[../CAMBIOS_ARL_SALUD.md](../CAMBIOS_ARL_SALUD.md)**
- Explicación completa del cambio ARL/SALUD
- Comparación de modelos
- Próximos pasos de implementación

## ⚡ Comandos Rápidos

```bash
# Ver estado de migraciones
alembic current

# Ver historial completo
alembic history --verbose

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Revertir última migración (si algo sale mal)
alembic downgrade -1

# Ver SQL que se ejecutará (sin aplicar)
alembic upgrade head --sql

# Crear nueva migración después de cambiar modelos
alembic revision --autogenerate -m "Descripción del cambio"
```

## 🎯 Después de Aplicar la Migración

### 1. Datos de Prueba (Opcional)

Puedes crear datos de prueba para validar el sistema:

```sql
-- Crear una empresa de ejemplo
INSERT INTO empresa (nit, razon_social, estado) 
VALUES ('900123456-7', 'Empresa Demo SA', 'ACTIVA');

-- Crear un afiliado de ejemplo
INSERT INTO afiliado (
    numero_poliza, tipo_poliza, tipo_documento, numero_documento,
    nombres, apellidos, fecha_inicio_poliza, estado
) VALUES (
    'POL-2026-001', 'INDIVIDUAL', 'CC', '1234567890',
    'Juan', 'Pérez', '2026-01-01', 'ACTIVO'
);

-- Crear un empleado de ejemplo
-- (Necesitas el ID de la empresa creada arriba)
-- ...
```

### 2. Próximos Desarrollos

Según el plan en [CAMBIOS_ARL_SALUD.md](../CAMBIOS_ARL_SALUD.md):

#### Corto Plazo
- 🔲 **AfiliadoRepository** - Implementar CRUD para afiliados
- 🔲 **AfiliadoService** - Lógica de negocio (validar pólizas, estados)
- 🔲 **API Endpoints** - `/api/v1/afiliados` (GET, POST, PUT, DELETE)

#### Medio Plazo
- 🔲 **Actualizar IncapacidadRepository** - Manejar joins polimórficos
- 🔲 **Actualizar IncapacidadService** - Validaciones según tipo
- 🔲 **Actualizar API Incapacidades** - Soportar ARL y SALUD
- 🔲 **Tests** - Unitarios, integración, E2E

## 🆘 ¿Problemas?

### La migración falla

1. Verifica que PostgreSQL esté corriendo:
   ```bash
   docker compose ps
   docker compose logs postgres
   ```

2. Verifica la configuración en `.env`:
   ```bash
   cat .env | grep DATABASE_URL
   ```

3. Intenta conectar manualmente:
   ```bash
   docker compose exec postgres psql -U incapacidades_user -d incapacidades_db -c "\dt"
   ```

### Error "relation already exists"

Las tablas ya existen. Opciones:

```bash
# Marcar como aplicada (si las tablas están bien)
docker compose exec backend alembic stamp head

# O recrear desde cero (CUIDADO: elimina datos)
docker compose exec backend alembic downgrade base
docker compose exec backend alembic upgrade head
```

### Necesitas ayuda

Revisa la documentación:
- [MIGRACION_INICIAL.md](MIGRACION_INICIAL.md) - Sección "Troubleshooting"
- [alembic/README.md](alembic/README.md) - Sección "Troubleshooting"

## ✅ Checklist

Antes de continuar con el siguiente paso:

- [ ] Servicios Docker corriendo (`docker compose ps`)
- [ ] Migración aplicada (`alembic current` = `001_initial_schema`)
- [ ] Tablas verificadas (10 tablas + alembic_version)
- [ ] Constraint polimórfico creado (`chk_incapacidad_tipo_relacion`)
- [ ] Índices creados (~50 índices)

## 📞 Siguiente Paso

Una vez aplicada la migración exitosamente, podemos continuar con:

1. **Repositories** - Implementar AfiliadoRepository
2. **Services** - Implementar AfiliadoService  
3. **API Endpoints** - Crear /api/v1/afiliados
4. **Tests** - Validar todo el flujo

¿Cuál prefieres que implementemos primero?

---

**Estado Actual**: ✅ Migraciones configuradas y listas  
**Siguiente Acción**: Aplicar migración con `alembic upgrade head`  
**Documentación**: 4 archivos de guía disponibles
