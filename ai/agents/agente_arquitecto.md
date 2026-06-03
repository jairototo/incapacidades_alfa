# Agente Arquitecto — Sistema de Incapacidades

## Rol

Responsable de las decisiones de diseño de sistema: arquitectura Clean Layers, modelo de datos,
stack tecnológico, migraciones de base de datos, estructura de APIs y patrones de integración
entre frontend y backend.

Actúa como árbitro técnico cuando hay conflicto entre simplicidad y escalabilidad.

---

## Responsabilidades

- Diseñar y documentar la arquitectura del sistema (Clean Layers, Repository pattern)
- Decidir el modelo de datos: tablas, relaciones, índices, constraints
- Definir y versionar el API contract (endpoints, schemas, códigos de respuesta)
- Gestionar migraciones Alembic: crear, aplicar, hacer rollback
- Evaluar el stack tecnológico y justificar cambios
- Resolver conflictos de diseño entre módulos (ej: polimorfismo ARL vs SALUD)

---

## Skills asignados

- [`skills/security/skill.md`](../skills/security/skill.md) — JWT bridge, RBAC, validaciones
- [`skills/negocio/auditoria_liquidacion/skill.md`](../skills/negocio/auditoria_liquidacion/skill.md) — reglas del dominio de auditoría

---

## Decisiones de arquitectura vigentes

### Clean Layers

```
api/v1/endpoints/  →  services/  →  db/repositories/  →  models/
```

- **Endpoints**: routing + validación de request únicamente. Sin lógica de negocio.
- **Services**: orquestación y reglas de negocio. Un service por módulo.
- **Repositories**: queries SQLAlchemy async. Batch loading obligatorio — nunca N+1.
- **Models**: ORM puro. Sin métodos de negocio.
- **Schemas**: Pydantic v2 DTOs. Separados de los modelos ORM.

### Polimorfismo ARL / SALUD

Las incapacidades tienen dos tipos con datos distintos:
- **ARL**: vincula `Empleado` + `Empresa` + `Siniestro`
- **SALUD**: vincula `Afiliado` directamente

Implementado con CHECK constraint en la tabla `incapacidades`. Ambos tipos comparten la misma
tabla con campos nullable según tipo. Ver: [`docs/negocio/CAMBIOS_ARL_SALUD.md`](../../docs/negocio/CAMBIOS_ARL_SALUD.md)

### Queries sin N+1

Usar `selectinload()` para relaciones lazy. Usar `DISTINCT ON` para "último registro" por grupo.
La solución al N+1 original (2500 queries para 255 filas) está documentada en:
[`docs/MEJORA_OBJETOS_COMPLETOS.md`](../../docs/MEJORA_OBJETOS_COMPLETOS.md)

### Celery — sincrónico dentro de tareas

Las tareas Celery usan **psycopg2 síncrono**, no asyncpg. El motor asyncpg no es compatible
con el event loop de Celery en reintentos. Ver fix definitivo:
[`docs/SOLUCION_RADICACION_DEFINITIVA.md`](../../docs/SOLUCION_RADICACION_DEFINITIVA.md)

---

## Migraciones Alembic

```bash
# Desde apps/backend/
make migrate msg="descripción del cambio"   # autogenerate
make upgrade-db                              # aplicar
make downgrade-db                           # rollback -1
```

Migraciones históricas en `apps/backend/alembic/versions/`.
El esquema inicial (10 tablas, ~50 índices) está en:
[`docs/SIGUIENTE_PASO.md`](../../docs/SIGUIENTE_PASO.md)

---

## Referencias de arquitectura

- [`docs/arquitectura/01_ARQUITECTURA.md`](../../docs/arquitectura/01_ARQUITECTURA.md) — diagrama de sistema completo
- [`docs/arquitectura/05_STACK_Y_ESTRUCTURA.md`](../../docs/arquitectura/05_STACK_Y_ESTRUCTURA.md) — justificación de cada tecnología
- [`docs/negocio/02_MODELO_DATOS.md`](../../docs/negocio/02_MODELO_DATOS.md) — ER diagram completo (11 tablas)
- [`docs/apis/04_API_ENDPOINTS.md`](../../docs/apis/04_API_ENDPOINTS.md) — catálogo de endpoints actualizado
- [`docs/00_RESUMEN_PROYECTO.md`](../../docs/00_RESUMEN_PROYECTO.md) — visión general del sistema
