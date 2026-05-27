# Migraciones Alembic - Sistema de Incapacidades

Este directorio contiene las migraciones de base de datos usando Alembic para el sistema de gestión de incapacidades.

## Configuración

- **Alembic**: 1.13.1
- **SQLAlchemy**: 2.0.25 (async)
- **Database**: PostgreSQL 15+

## Estructura

```
alembic/
├── versions/           # Archivos de migración
│   └── 20260106_1000_001_initial_schema.py
├── env.py             # Configuración del entorno (async)
└── script.py.mako     # Template para nuevas migraciones
```

## Uso

### Ver estado actual

```bash
# Ver revisión actual
alembic current

# Ver historial de migraciones
alembic history

# Ver migraciones pendientes
alembic history --verbose
```

### Aplicar migraciones

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Aplicar una migración específica
alembic upgrade <revision>

# Aplicar siguiente migración
alembic upgrade +1
```

### Revertir migraciones

```bash
# Revertir última migración
alembic downgrade -1

# Revertir a una revisión específica
alembic downgrade <revision>

# Revertir todas las migraciones
alembic downgrade base
```

### Crear nuevas migraciones

```bash
# Auto-generar migración basada en cambios de modelos
alembic revision --autogenerate -m "Descripción del cambio"

# Crear migración vacía
alembic revision -m "Descripción del cambio"
```

## Migración Inicial (001_initial_schema)

La migración inicial crea el esquema completo del sistema con soporte para:

### Tablas Principales

1. **empresa** - Empresas afiliadas al sistema
2. **empleado** - Empleados de las empresas (para incapacidades ARL)
3. **afiliado** - Afiliados con pólizas (para incapacidades SALUD) ⭐ NUEVO
4. **usuario** - Usuarios del sistema con RBAC
5. **siniestro** - Siniestros laborales (solo ARL)
6. **incapacidad** - Incapacidades con soporte polimórfico ARL/SALUD ⭐
7. **documento** - Documentos adjuntos
8. **historial_estado** - Auditoría de cambios de estado
9. **orden_pago** - Órdenes de pago generadas
10. **auditoria_log** - Log completo de auditoría

### Características Importantes

#### Soporte Polimórfico ARL/SALUD

La tabla `incapacidad` soporta dos tipos:

- **ARL**: Incapacidades laborales
  - Requiere: `empleado_id`, `empresa_id`
  - Opcional: `siniestro_id`
  - Beneficiario: Empleado o Empresa

- **SALUD**: Incapacidades de salud
  - Requiere: `afiliado_id`
  - No tiene: `empleado_id`, `empresa_id`, `siniestro_id`
  - Beneficiario: Afiliado

#### Constraint Crítico

```sql
CHECK (
  (tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL) OR
  (tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)
)
```

Este constraint garantiza la integridad referencial según el tipo de incapacidad.

### Índices Creados

La migración crea ~50 índices optimizados para:
- Búsquedas por documento (NIT, cédula, número de póliza)
- Filtros por estado
- Rangos de fechas
- Búsquedas full-text (JSONB con GIN)
- Foreign keys para joins eficientes

### Extensiones PostgreSQL

- **uuid-ossp**: Generación de UUIDs v4

## Uso con Docker

Cuando trabajas con Docker, debes ejecutar las migraciones dentro del contenedor:

```bash
# Aplicar migraciones
docker compose exec api alembic upgrade head

# Ver estado
docker compose exec api alembic current

# Crear nueva migración
docker compose exec api alembic revision --autogenerate -m "Descripción"
```

## Makefile Shortcuts

El Makefile del proyecto incluye atajos:

```bash
# Aplicar migraciones
make migrate-up

# Crear nueva migración
make migrate msg="Descripción del cambio"

# Revertir última migración
make migrate-down
```

## Notas Importantes

### Async Support

El archivo `env.py` está configurado para usar SQLAlchemy async:
- Usa `async_engine_from_config`
- Ejecuta migraciones con `await connection.run_sync()`
- Compatible con AsyncSession

### Auto-generación

Alembic puede detectar automáticamente:
- ✅ Nuevas tablas
- ✅ Nuevas columnas
- ✅ Cambios de tipo
- ✅ Nuevos índices
- ✅ Nuevos constraints
- ⚠️ **NO detecta**: Cambios de nombre (aparecen como drop + create)

### Best Practices

1. **Siempre revisar** las migraciones auto-generadas antes de aplicar
2. **Backup** de la base de datos antes de migraciones en producción
3. **Probar** migraciones en ambiente de desarrollo primero
4. **Documentar** cambios complejos en el docstring de la migración
5. **No modificar** migraciones ya aplicadas (crear nuevas)

## Troubleshooting

### Error: "Can't locate revision identified by 'head'"

```bash
# Marcar base de datos como actualizada
alembic stamp head
```

### Error: "Target database is not up to date"

```bash
# Ver migraciones pendientes
alembic history
alembic upgrade head
```

### Error: "FAILED: Multiple head revisions are present"

```bash
# Fusionar revisiones
alembic merge heads -m "Merge multiple heads"
```

### Recrear base de datos

```bash
# Revertir todo
alembic downgrade base

# Volver a aplicar
alembic upgrade head
```

## Recursos

- [Documentación Alembic](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
