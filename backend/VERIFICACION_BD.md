# Guía de Verificación de Base de Datos

## 📋 Resumen

Se han creado scripts para verificar que las migraciones y tablas estén correctamente configuradas en la base de datos.

## 🚀 Aplicar Migración Pendiente

Según el estado actual, tienes una migración pendiente (`db660eb37bd4 - fix metadata reserved name`). Para aplicarla:

```bash
# Desde la carpeta backend/
docker compose exec api alembic upgrade head
```

## 🔍 Scripts de Verificación

### 1. Script Completo de Verificación

**Archivo**: `scripts/verify_database.py`

Este script verifica:
- ✅ Estado de migraciones Alembic (actualizada vs HEAD)
- ✅ Existencia de las 11 tablas esperadas
- ✅ Estructura de tabla `afiliado` (columnas, índices, constraints)
- ✅ Estructura de tabla `incapacidad` (relaciones polimórficas)
- ✅ Constraints críticos (tipo_relacion, estados, etc.)
- ✅ Índices críticos para performance
- ✅ **Prueba funcional del constraint polimórfico** (intenta crear datos inválidos)

**Uso**:

```bash
# Desde Docker (recomendado)
docker compose exec api python scripts/verify_database.py

# O localmente
python scripts/verify_database.py
```

**Salida esperada**:
```
============================================================
       VERIFICACIÓN COMPLETA DE BASE DE DATOS
============================================================
Sistema de Gestión de Incapacidades

──────────────────────────────────────────────────────────
  🔍 Estado de Migraciones Alembic
──────────────────────────────────────────────────────────
  Revisión actual: db660eb37bd4
  Revisión HEAD:   db660eb37bd4
  ✅ Base de datos actualizada

──────────────────────────────────────────────────────────
  📁 Verificación de Tablas
──────────────────────────────────────────────────────────
  ✅ Todas las tablas esperadas existen (11)
     • afiliado           - Afiliados con pólizas (SALUD)
     • alembic_version    - Control de versiones Alembic
     • auditoria_log      - Log de auditoría
     • documento          - Documentos adjuntos
     • empleado           - Empleados de empresas (ARL)
     • empresa            - Empresas afiliadas
     • historial_estado   - Auditoría de estados
     • incapacidad        - Incapacidades ARL/SALUD
     • orden_pago         - Órdenes de pago
     • siniestro          - Siniestros laborales
     • usuario            - Usuarios del sistema

──────────────────────────────────────────────────────────
  📋 Verificación Tabla AFILIADO
──────────────────────────────────────────────────────────
  Columnas: 21 ✅
  Índices: 3
  Foreign Keys: 0
  Check Constraints: 5
  ✅ Constraint estado: Presente
  ✅ Índice numero_poliza: Presente

──────────────────────────────────────────────────────────
  📋 Verificación Tabla INCAPACIDAD
──────────────────────────────────────────────────────────
  Columnas: 30
  Índices: 0
  Foreign Keys: 7 (debe ser ~7)
  Check Constraints: 5
  ✅ Constraint polimórfico (tipo_relacion): True

──────────────────────────────────────────────────────────
  🔒 Verificación de Constraints Críticos
──────────────────────────────────────────────────────────
  ✅ incapacidad.chk_incapacidad_tipo_relacion: True
  ✅ incapacidad.chk_incapacidad_tipo: True
  ✅ afiliado.chk_afiliado_estado: True
  ✅ afiliado.chk_afiliado_tipo_poliza: True

──────────────────────────────────────────────────────────
  🧪 Prueba de Constraint Polimórfico
──────────────────────────────────────────────────────────
  ✅ Constraint polimórfico funciona correctamente
  ℹ️  Error esperado: violates check constraint "chk_incapacidad_tipo_relacion"...

============================================================
              RESUMEN DE VERIFICACIÓN
============================================================

  ✅ Migraciones actualizadas
  ✅ Todas las tablas presentes
  ✅ Tabla afiliado correcta
  ✅ Tabla incapacidad correcta
  ✅ Constraints críticos
  ✅ Índices críticos
  ✅ Constraint polimórfico funciona

  Resultado: 7/7 verificaciones exitosas

  🎉 ¡Base de datos completamente verificada!
```

### 2. Script de Estado de Migraciones

**Archivo**: `scripts/check_migrations.py`

Script más simple que solo verifica el estado de Alembic.

**Uso**:
```bash
docker compose exec api python scripts/check_migrations.py
```

### 3. Script Todo-en-Uno

**Archivo**: `scripts/migrate_and_verify.sh` (Bash)

Ejecuta todo el proceso automáticamente:
1. Verifica estado actual
2. Aplica migraciones pendientes
3. Verifica que se aplicaron
4. Ejecuta verificación completa

**Uso**:
```bash
# Hacer ejecutable (solo la primera vez)
chmod +x scripts/migrate_and_verify.sh

# Ejecutar
./scripts/migrate_and_verify.sh
```

## 📊 Proceso Completo Recomendado

### Opción 1: Paso a paso

```bash
# 1. Ir a la carpeta backend
cd /opt/apps/incapacidades_vs/backend

# 2. Asegurar que los servicios estén corriendo
docker compose up -d

# 3. Aplicar migración pendiente
docker compose exec api alembic upgrade head

# 4. Verificar base de datos
docker compose exec api python scripts/verify_database.py
```

### Opción 2: Automático

```bash
# Ir a backend y ejecutar el script
cd /opt/apps/incapacidades_vs/backend
./scripts/migrate_and_verify.sh
```

## 🔍 Verificaciones Específicas

### Verificar solo tablas

```bash
docker compose exec api psql -U incapacidades_user -d incapacidades_db -c "\dt"
```

### Verificar constraint polimórfico

```bash
docker compose exec api psql -U incapacidades_user -d incapacidades_db -c "
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'incapacidad'::regclass 
  AND conname = 'chk_incapacidad_tipo_relacion';
"
```

### Verificar tabla afiliado

```bash
docker compose exec api psql -U incapacidades_user -d incapacidades_db -c "\d afiliado"
```

### Contar registros

```bash
docker compose exec api psql -U incapacidades_user -d incapacidades_db -c "
SELECT 
    schemaname,
    tablename,
    (SELECT COUNT(*) FROM incapacidad) as incapacidad,
    (SELECT COUNT(*) FROM afiliado) as afiliado,
    (SELECT COUNT(*) FROM empleado) as empleado,
    (SELECT COUNT(*) FROM empresa) as empresa;
" | head -3
```

## ⚠️ Troubleshooting

### La verificación falla en "Base de datos desactualizada"

**Causa**: Hay migraciones pendientes  
**Solución**: 
```bash
docker compose exec api alembic upgrade head
```

### Error: "cannot import name 'X' from 'app.utils.enums'"

**Causa**: Faltan enums en el archivo enums.py  
**Solución**: Ya resuelto en commits anteriores. Si persiste, verifica que tengas:
- `TipoEmpresa`
- `Genero`
- `TipoPoliza`
- `BeneficiarioTipo`
- `TipoDocumentoArchivo`

### Error: "relation does not exist"

**Causa**: La migración no se aplicó  
**Solución**:
```bash
docker compose exec api alembic upgrade head
```

### El constraint polimórfico no funciona

**Síntoma**: La prueba pasa pero debería fallar  
**Verificación**:
```bash
docker compose exec api python -c "
from app.models import Incapacidad
from sqlalchemy import inspect
insp = inspect(Incapacidad)
print([c.name for c in insp.table.constraints if 'tipo_relacion' in c.name])
"
```

## 📝 Notas Importantes

### Sobre el contenedor

- ✅ Nombre correcto: `api` (no `backend`)
- ✅ Todos los comandos usan: `docker compose exec api`
- ✅ El archivo `docker-compose.yml` está en `backend/`

### Sobre las migraciones

- La migración `001_initial_schema` fue creada manualmente
- La migración `db660eb37bd4` fue auto-generada con `alembic revision --autogenerate`
- Ambas deben aplicarse para tener la base de datos completa

### Sobre la verificación

El script `verify_database.py` incluye una **prueba funcional** que intenta insertar datos inválidos para verificar que el constraint polimórfico funciona. Esto es seguro porque:
- Se ejecuta en una transacción
- Se hace rollback inmediatamente
- No deja datos basura en la BD

## 🎯 Próximos Pasos

Después de verificar que todo está correcto:

1. ✅ **Datos de prueba** - Crear scripts de seed (opcional)
2. ✅ **AfiliadoRepository** - Implementar CRUD
3. ✅ **AfiliadoService** - Lógica de negocio
4. ✅ **API Endpoints** - `/api/v1/afiliados`
5. ✅ **Tests** - Unitarios e integración

## 📚 Referencias

- [SIGUIENTE_PASO.md](SIGUIENTE_PASO.md) - Guía general
- [MIGRACION_INICIAL.md](MIGRACION_INICIAL.md) - Guía detallada de migración
- [alembic/README.md](alembic/README.md) - Documentación de Alembic
- [CAMBIOS_ARL_SALUD.md](../CAMBIOS_ARL_SALUD.md) - Cambios arquitectónicos
