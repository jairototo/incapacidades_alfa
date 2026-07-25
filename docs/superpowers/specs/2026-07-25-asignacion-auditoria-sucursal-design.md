# Asignación de Auditoría por Sucursal — Design Spec

> **Context source:** `docs/superpowers/plans/2026-06-23-workflow-estados-liquidacion.md` (that plan is background context only, not to be executed). This spec covers a follow-up requirement: automatic auditor assignment, keyed by the sucursal of the siniestro, when an ARL/SALUD incapacidad enters `EN_AUDITORIA`.

## Goal

Today, `enqueue_auditoria_incapacidad` fires a Celery task that runs `auditoria_service.auditar_incapacidad()`, which evaluates business rules and transitions `RADICADA → EN_AUDITORIA`, but never assigns a specific auditor. This spec adds:

1. Automatic auditor assignment at that transition, based on the sucursal of the relevant siniestro, with workload-based load balancing among auditors at the same sucursal.
2. A fallback `auditor_default` auditor for cases where no qualifying siniestro can be found (all SALUD cases, and any ARL case without an active, date-matching siniestro).
3. A filter in the bandeja de pendientes de auditoría by assigned auditor.
4. An administrative module (Gestión de Auditores) to create/edit/deactivate auditors, assign them to sucursales, and see a report of how many incapacidades are currently assigned to each.

Reassignment of already-assigned incapacidades between auditors is **explicitly out of scope** for this spec (flagged in the source requirements as "pendiente aplicación").

## Non-goals

- Porting the Excel's legacy per-person / odd-even-siniestro-number / "San Diego" routing rules (see Clarifications, C1). We implement the simplified sucursal + load-balance model the requirements describe, not the historical manual routing table.
- Any reassignment UI/endpoint for incapacidades already assigned to an auditor.
- Multi-sucursal auditors (each auditor maps to exactly one sucursal, matching the source Excel).

## Clarifications resolved during brainstorming

| # | Question | Resolution |
|---|----------|------------|
| C1 | Date condition for selecting the "active" siniestro relative to `incapacidad.fecha_inicio` | `fecha_siniestro <= fecha_inicio` (siniestro on or before the incapacidad start — the literal "posterior" in the source requirement was a wording slip; this is the only direction consistent with `PRIMER_DIA_NO_PAGABLE`, which assumes `fecha_inicio == fecha_siniestro` is a normal case, and with prórroga incapacidades, whose `fecha_inicio` is always later than the original siniestro). |
| C2 | `auditor_default` doesn't exist in the live DB (verified directly) despite the requirement asserting it does | Create it as part of this work, via the same seed script as the other fictitious auditors. |
| C3 | Semantics of the "acumulado" counter used for load-balancing | Active/open workload — increments on assignment, decrements when the case leaves the auditor's active states (`EN_AUDITORIA`/`PENDIENTE`/`CREACION_SINIESTRO`) into a terminal-from-auditor state (`LIQUIDACION`/`LIQUIDACION_PARCIAL`/`GLOSADA`), and re-increments if a liquidator devolution sends it back to `EN_AUDITORIA`. Chosen over a lifetime-cumulative counter because a cumulative counter stops reflecting real workload over time and permanently favors the newest auditor. |
| C4 | Email domain for the 7 fictitious auditor accounts (must differ from the real names/emails in the Excel) | `@segurosalfa-test.com.co` |

## 1. Data model changes

One Alembic migration, three additive nullable/defaulted columns (no backfill needed — no production data exists yet):

```python
# usuario
sucursal: Mapped[Optional[SucursalSiniestro]] = mapped_column(
    String(50), nullable=True,
    comment="Sucursal asignada (solo aplica a rol=AUDITOR); determina qué incapacidades ARL puede recibir",
)
incapacidades_asignadas_activas: Mapped[int] = mapped_column(
    Integer, nullable=False, server_default="0",
    comment="Contador de incapacidades actualmente asignadas y abiertas (para balanceo de carga); no es acumulado histórico",
)

# incapacidad
auditor_asignado_id: Mapped[Optional[UUID]] = mapped_column(
    PGUUID(as_uuid=True), ForeignKey("usuario.id"), nullable=True,
    comment="Auditor asignado automáticamente al entrar a EN_AUDITORIA, según sucursal del siniestro y balanceo de carga",
)
```

`Incapacidad` gets an `auditor_asignado: Mapped[Optional["Usuario"]] = relationship(...)` alongside the existing `auditado_por` relationship — the two stay distinct:
- `auditor_asignado_id` — set at assignment time (queue routing), never cleared while the case is open.
- `auditado_por_id` — unchanged; still set only when an auditor actually performs an audit action.

`SucursalSiniestro` (already defined in `app/utils/enums.py`) is reused as-is for `usuario.sucursal` — no new enum.

## 2. Assignment algorithm

New module `app/services/auditor_assignment_service.py` (pure-ish, testable in isolation), called from `auditoria_service.auditar_incapacidad()` right after the state transition to `EN_AUDITORIA` and before commit.

```
async def asignar_auditor(db, incapacidad: Incapacidad) -> Usuario:
    siniestro = await _find_siniestro_activo(db, incapacidad)   # None for SALUD or no match
    if siniestro is not None and siniestro.sucursal is not None:
        auditor = await _pick_by_sucursal(db, siniestro.sucursal)
    else:
        auditor = None
    if auditor is None:
        auditor = await _get_auditor_default(db)
    incapacidad.auditor_asignado_id = auditor.id
    auditor.incapacidades_asignadas_activas += 1
    db.add(auditor)
    return auditor
```

**`_find_siniestro_activo`**: for ARL incapacidades only (SALUD has no siniestro), query `Siniestro` where `empleado_id == incapacidad.empleado_id`, `estado IN (REPORTADO, EN_INVESTIGACION)`, `fecha_siniestro <= incapacidad.fecha_inicio`, ordered by `fecha_siniestro DESC` (most recent qualifying one), `LIMIT 1`. If `incapacidad.siniestro_id` is already set (post `CREACION_SINIESTRO` flow) that siniestro is used directly instead of re-searching, since it's already the authoritative link.

**`_pick_by_sucursal`**: query `Usuario` where `rol == AUDITOR`, `estado == ACTIVO`, `sucursal == siniestro.sucursal`, order by `incapacidades_asignadas_activas ASC, id ASC`, `LIMIT 1`. Returns `None` if no auditor is configured for that sucursal (falls through to default).

**`_get_auditor_default`**: `Usuario` where `username == "auditor_default"`.

**Decrement hook**: in `incapacidad_service.auditar_incapacidad()`, wherever `nuevo_estado` resolves to `LIQUIDACION`, `LIQUIDACION_PARCIAL`, or `GLOSADA` and the incapacidad has an `auditor_asignado_id`, decrement that auditor's `incapacidades_asignadas_activas` (floor at 0). Wherever a liquidator devolution sets `nuevo_estado = EN_AUDITORIA` from `LIQUIDACION`/`LIQUIDACION_PARCIAL`, re-increment the same assigned auditor (no re-run of the assignment algorithm — the auditor stays the same).

This all runs inside the existing async session/transaction of `auditar_incapacidad`/`auditar_incapacidad` (service), so it commits atomically with the state change — no separate task or race condition.

## 3. Seed data — fictitious auditor users

`scripts/seed_auditores.py`, following the existing `scripts/seed_admin.py` convention (standalone idempotent script using `pwd_context.hash`, `must_change_password=True`, skip-if-exists by username):

| username | nombre_completo | email | sucursal |
|---|---|---|---|
| auditor.cali | (fictitious name) | ...@segurosalfa-test.com.co | Cali |
| auditor.medellin | (fictitious name) | ...@segurosalfa-test.com.co | Medellín |
| auditor.cartagena | (fictitious name) | ...@segurosalfa-test.com.co | Cartagena |
| auditor.bogota1..4 | (fictitious names, 4 accounts) | ...@segurosalfa-test.com.co | Bogotá |
| auditor_default | Auditor por Defecto | auditor.default@segurosalfa-test.com.co | *(null)* |

All `rol=AUDITOR`, `estado=ACTIVO`, `incapacidades_asignadas_activas=0`. Names/emails are invented, deliberately different from the real names in the Excel (per the source requirement — those are real people who don't have system accounts yet).

## 4. Bandeja de pendientes filter

- `incapacidad_repository.listar_pendientes(..., auditor_asignado_id: Optional[UUID] = None)` — adds `Incapacidad.auditor_asignado_id == auditor_asignado_id` to the `WHERE` clause when provided. Eager-load `selectinload(Incapacidad.auditor_asignado)` alongside the existing `empleado`/`empresa` loads (no N+1).
- `incapacidad_service.listar_pendientes()` and the `GET /incapacidades/pendientes` endpoint pass through the new optional query param.
- Response schema: add `auditor_asignado: Optional[UsuarioSimple]` next to the existing `auditado_por` field.
- Frontend `FiltersBar.tsx`: new "Auditor asignado" `<Select>`, options from `GET /usuarios?rol=AUDITOR&estado=ACTIVO`. `IncapacidadesTable.tsx` / `PendientesPage.tsx` show the assigned auditor's name as a column/badge.

## 5. Admin module — Gestión de Auditores

No new backend CRUD service — extends the existing `usuario_service`/`usuarios.py` (create, list, update, deactivate already exist and are ADMIN-gated):

- `UsuarioCreate` / `UsuarioUpdate` / `UsuarioResponse` / `UsuarioListItem` schemas gain `sucursal: Optional[SucursalSiniestro]`.
- New endpoint `GET /usuarios/reporte-auditores` (ADMIN-only): returns, per auditor, `{username, nombre_completo, sucursal, incapacidades_asignadas_activas}` — a straight read of the counter column, no extra aggregation query needed since it's kept live by the assignment/decrement hooks.
- Frontend: new route `pages/admin/AuditoresPage.tsx`, ADMIN-only (guarded the same way other role-gated routes are in `router/index.tsx`):
  - Table of `AUDITOR` users: nombre, email, sucursal, carga activa.
  - Create/edit modal: nombre_completo, email, sucursal (select from `SucursalSiniestro`); username auto-derived or entered.
  - "Eliminar" action calls the existing `deactivate` endpoint (soft delete — hard delete is unsafe here since `incapacidad.auditor_asignado_id` FK-references these rows).
  - Report section/table rendering `GET /usuarios/reporte-auditores`.
  - A visible `// TODO` / disabled-state note for the future reassignment-of-incapacidades module — not built now.

## Testing strategy

- Backend unit tests for `auditor_assignment_service`: siniestro-date-filter edge cases (no siniestro, multiple qualifying siniestros picks most recent, siniestro after `fecha_inicio` excluded, SALUD always defaults), sucursal-based selection with load-balance tie-breaking, fallback to `auditor_default` when no auditor configured for a sucursal, counter increment/decrement across the full state path including devolution.
- Repository test for `listar_pendientes` with `auditor_asignado_id` filter.
- Endpoint test for `GET /usuarios/reporte-auditores` (ADMIN-only, verify 403 for other roles).
- Frontend: `FiltersBar` test for the new filter option; `AuditoresPage` tests for CRUD + report render, following existing sistema-interno test conventions (vitest).

## File map (expected)

### Created
| File | Purpose |
|---|---|
| `apps/backend/alembic/versions/<ts>_add_auditor_sucursal_assignment.py` | Adds the 3 columns |
| `apps/backend/app/services/auditor_assignment_service.py` | Assignment algorithm |
| `apps/backend/scripts/seed_auditores.py` | Seeds 7 fictitious auditors + `auditor_default` |
| `apps/backend/tests/test_auditor_assignment_service.py` | Unit tests |
| `apps/frontend/sistema-interno/src/pages/admin/AuditoresPage.tsx` | Admin CRUD + report page |
| `apps/frontend/sistema-interno/src/services/auditores.ts` | API client for the admin page |

### Modified
| File | Why |
|---|---|
| `apps/backend/app/models/usuario.py` | `sucursal`, `incapacidades_asignadas_activas` columns |
| `apps/backend/app/models/incapacidad.py` | `auditor_asignado_id` column + relationship |
| `apps/backend/app/services/auditoria_service.py` | Call `asignar_auditor()` on transition to `EN_AUDITORIA` |
| `apps/backend/app/services/incapacidad_service.py` | Decrement/re-increment hooks on state transitions out of/back into auditor-active states |
| `apps/backend/app/schemas/usuario.py` | `sucursal` field |
| `apps/backend/app/schemas/incapacidad.py` | `auditor_asignado` field |
| `apps/backend/app/db/repositories/incapacidad_repository.py` | `auditor_asignado_id` filter + eager load |
| `apps/backend/app/api/v1/endpoints/incapacidades.py` | Pass-through query param |
| `apps/backend/app/api/v1/endpoints/usuarios.py` | `GET /usuarios/reporte-auditores` |
| `apps/frontend/sistema-interno/src/components/dashboard/FiltersBar.tsx` | Auditor-asignado filter |
| `apps/frontend/sistema-interno/src/router/index.tsx` | Register admin route |
