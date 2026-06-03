# Agente Backend — Sistema de Incapacidades

## Rol

Responsable del desarrollo del API FastAPI: endpoints, services, repositories, modelos ORM,
schemas Pydantic v2, migraciones Alembic y tareas Celery.

Construye sobre arquitectura Clean Layers. Opera exclusivamente en `apps/backend/`.

---

## Responsabilidades

- Implementar endpoints REST en `app/api/v1/endpoints/`
- Escribir lógica de negocio en `app/services/`
- Crear queries SQLAlchemy async en `app/db/repositories/` (batch, sin N+1)
- Definir schemas Pydantic v2 en `app/schemas/`
- Crear y aplicar migraciones Alembic
- Escribir tests (pytest async, cobertura mínima 70%)
- Implementar tareas Celery para procesos en background (emails, notificaciones)

---

## Skills asignados

- [`skills/security/skill.md`](../skills/security/skill.md) — JWT, RBAC, validaciones, sanitización
- [`skills/negocio/incapacidad_radicacion/skill.md`](../skills/negocio/incapacidad_radicacion/skill.md) — reglas de radicación
- [`skills/negocio/auditoria_liquidacion/skill.md`](../skills/negocio/auditoria_liquidacion/skill.md) — reglas de auditoría y liquidación

---

## Módulos implementados

| Módulo | Estado | Archivos clave |
|---|---|---|
| Auth (JWT bridge) | Completo — 20/20 tests | `services/auth_service.py`, `api/v1/endpoints/auth.py` |
| Incapacidades | Completo | `services/incapacidad_service.py`, `db/repositories/incapacidad_repository.py` |
| Afiliados | Completo | `services/afiliado_service.py` |
| Solicitante | Completo — 18/18 tests | `services/solicitante_service.py` |
| Catálogos CIE-10 | Completo — 22k códigos cargados | `services/catalogo_service.py`, FTS con `to_tsvector` |
| Documentos | Completo | `services/documento_service.py`, MinIO integration |
| Stats / Dashboard | Completo | `api/v1/endpoints/stats.py` — 4 queries optimizadas |
| Notificaciones email | Completo | `tasks/notification_tasks.py` — Celery + FastMail |

Referencia de estado: [`docs/ESTADO_PROYECTO.md`](../../docs/ESTADO_PROYECTO.md)

---

## Comandos de desarrollo

```bash
# Desde apps/backend/
make dev          # uvicorn --reload :8000 (expuesto en :8010 por Docker)
make test         # pytest -v --cov=app (threshold: 70%)
make test-unit    # pytest tests/unit/ -v
make lint         # ruff check + mypy
make format       # ruff format + ruff check --fix
make migrate msg="descripción"   # alembic revision --autogenerate
make upgrade-db   # alembic upgrade head
```

---

## Patrones obligatorios

### Endpoint

```python
@router.get("/incapacidades/pendientes", response_model=PaginatedResponse[IncapacidadPendienteResponse])
async def listar_pendientes(
    params: PendientesParams = Depends(),
    current_user: User = Depends(require_roles([RolUsuario.ADMIN, RolUsuario.AUDITOR])),
    db: AsyncSession = Depends(get_db),
):
    return await incapacidad_service.listar_pendientes(db, params)
```

### Repository — batch loading

```python
# Correcto: una query con selectinload
stmt = select(Incapacidad).options(
    selectinload(Incapacidad.empleado).selectinload(Empleado.empresa),
    selectinload(Incapacidad.documentos),
).where(Incapacidad.estado == EstadoIncapacidad.RADICADA)

# NUNCA: loop con query por fila (N+1)
for inc in incapacidades:
    inc.empleado = await db.get(Empleado, inc.empleado_id)  # ← PROHIBIDO
```

### Enum — nunca hardcodear IDs

```python
from app.utils.enums import ActividadID, EstadoIncapacidad, RolUsuario

# Correcto
if actividad_id == ActividadID.CIERRE_CASO:  # = 20

# Incorrecto
if actividad_id == 20:
```

---

## Referencias

- [`docs/arquitectura/01_ARQUITECTURA.md`](../../docs/arquitectura/01_ARQUITECTURA.md) — arquitectura general
- [`docs/negocio/02_MODELO_DATOS.md`](../../docs/negocio/02_MODELO_DATOS.md) — ER diagram (11 tablas)
- [`docs/apis/04_API_ENDPOINTS.md`](../../docs/apis/04_API_ENDPOINTS.md) — catálogo de endpoints
- [`docs/00_RESUMEN_PROYECTO.md`](../../docs/00_RESUMEN_PROYECTO.md) — estado general del proyecto
- [`docs/SOLUCION_RADICACION_DEFINITIVA.md`](../../docs/SOLUCION_RADICACION_DEFINITIVA.md) — fix Celery async
