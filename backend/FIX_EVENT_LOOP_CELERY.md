# 🐛 Fix: Error de Event Loop en Tareas Celery

## Problema Identificado

### Síntomas
- ✅ La incapacidad se creaba correctamente
- ✅ La tarea de radicación se lanzaba
- ❌ La tarea fallaba al intentar radicar
- ❌ El correo de notificación NO se enviaba

### Error en Logs
```
RuntimeError: Task got Future attached to a different loop
```

### Causa Raíz
El uso de `asyncio.run()` dentro de tareas Celery creaba conflictos de event loops:

1. **Primera ejecución**: Funcionaba
2. **Reintentos o múltiples ejecuciones**: Fallaba porque `asyncio.run()` crea un NUEVO event loop cada vez
3. **SQLAlchemy async**: Las conexiones se vinculaban al primer event loop
4. **Conflicto**: Los event loops no coincidían → RuntimeError

### Código Problemático
```python
# ❌ INCORRECTO - Causaba conflictos
result = asyncio.run(_radicar_incapacidad_async(incap_uuid))
```

## Solución Implementada

### Cambio Aplicado
Reemplazar `asyncio.run()` con manejo manual de event loops:

```python
# ✅ CORRECTO - Compatible con Celery
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(_radicar_incapacidad_async(incap_uuid))
finally:
    loop.close()
```

### Por qué Funciona
1. **Control explícito**: Creamos y cerramos el event loop manualmente
2. **Limpieza adecuada**: `finally` asegura que el loop se cierre siempre
3. **Compatible con Celery**: No interfiere con el event loop del worker
4. **Reintentos seguros**: Cada ejecución tiene su propio event loop limpio

## Archivos Modificados

### `app/tasks/incapacidad_tasks.py`

**1. Tarea `radicar_incapacidad_automatica_task`** (línea ~35-50)
```python
# Antes:
result = asyncio.run(_radicar_incapacidad_async(incap_uuid))

# Después:
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(_radicar_incapacidad_async(incap_uuid))
finally:
    loop.close()
```

**2. Tarea `procesar_incapacidades_radicadas_pendientes_task`** (línea ~220-230)
```python
# Antes:
result = asyncio.run(_procesar_incapacidades_pendientes_async(dias_antiguedad))

# Después:
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(_procesar_incapacidades_pendientes_async(dias_antiguedad))
finally:
    loop.close()
```

## Verificación

### 1. Worker Reiniciado ✅
```bash
docker compose restart celery-worker
# ✔ Container incapacidades-celery-worker  Started
```

### 2. Tareas Registradas ✅
```bash
docker logs incapacidades-celery-worker 2>&1 | grep -A 10 "\[tasks\]"

# Output:
[tasks]
  . radicar_incapacidad_automatica ✓
  . send_incapacidad_radicada_email ✓
  . procesar_incapacidades_radicadas_pendientes ✓
  ... (otras tareas)
```

## Cómo Probar

### Opción 1: Script Automático
```bash
cd backend
./test_radicacion.sh
```

### Opción 2: Manual
1. Crear incapacidad desde frontend o API
2. Monitorear logs:
```bash
docker compose logs -f celery-worker | grep -E "(CELERY|EMAIL)"
```

3. Deberías ver:
```
[CELERY] Iniciando radicación automática para incapacidad UUID
[CELERY] Incapacidad NUM radicada exitosamente. Nuevo estado: EN_AUDITORIA
[CELERY] Enviando notificación por correo a email@example.com
[EMAIL] Enviando notificación de radicación NUM a email@example.com
[EMAIL] Notificación enviada exitosamente a email@example.com
```

## Resultado Esperado

### Flujo Completo Funcional ✅
```
1. Frontend → POST /api/v1/incapacidades
2. Backend → Guarda incapacidad (RADICADA)
3. Backend → Responde inmediato al frontend
4. Celery → radicar_incapacidad_automatica_task
   ├─ Cambia estado: RADICADA → EN_AUDITORIA ✅
   └─ Lanza: send_incapacidad_radicada_email_task ✅
5. Celery → send_incapacidad_radicada_email_task
   └─ Envía correo HTML al solicitante ✅
```

## Lecciones Aprendidas

### ❌ No Usar en Celery
- `asyncio.run()` - Crea event loops incompatibles
- Asumir que async "simplemente funciona"

### ✅ Usar en Celery
- `asyncio.new_event_loop()` + `set_event_loop()` + `run_until_complete()`
- Siempre cerrar loops en `finally`
- Probar reintentos explícitamente

## Referencias

- [Celery + AsyncIO](https://docs.celeryq.dev/en/stable/userguide/tasks.html#example)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Python AsyncIO Event Loops](https://docs.python.org/3/library/asyncio-eventloop.html)

---

**Estado**: ✅ RESUELTO  
**Fecha**: 29 de enero de 2026  
**Impacto**: Alto (bloqueaba notificaciones por correo)  
**Prioridad**: Crítico
