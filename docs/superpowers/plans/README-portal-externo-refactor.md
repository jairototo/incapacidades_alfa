# Portal Externo — Refactor a portal EMPRESA: índice de planes

**Spec:** [`../specs/2026-06-19-portal-externo-empresa-refactor-design.md`](../specs/2026-06-19-portal-externo-empresa-refactor-design.md)
**Fecha:** 2026-06-19 · **Estado:** pendiente de aprobación del usuario (todos los planes upfront, sin implementación aún)

| # | Plan | Alcance | Dependencias |
|---|------|---------|--------------|
| 1 | [Phase 1 — Autenticación](2026-06-19-phase1-autenticacion.md) | Login propio EMPRESA, guard rol+empresa, dashboard 3 acciones, retiro de rutas públicas, enriquecimiento `/auth/me` | — |
| 2 | [Phase 2 — Radicación Individual + Pipeline](2026-06-19-phase2-radicacion-individual.md) | `prorroga` (migración), pipeline compartido (Incapacidad directa + solicitante), selector de empleado, form individual | Phase 1 |
| 3 | [Phase 3 — Radicación Masiva + Integración](2026-06-19-phase3-radicacion-masiva.md) | `communication_log` + `numero_radicacion_servialfa`, stubs ServiAlfa/Sicat, reglas reutilizables, plantilla/validación/ZIP Excel, submit con gating | Phase 1, 2 |
| 4 | [Phase 4 — Job de Auditoría](2026-06-19-phase4-job-auditoria.md) | `auditoria_resultado` (migración), servicio de auditoría, tarea Celery, transición a `EN_AUDITORIA`, enqueue real | Phase 2, 3 |
| 5 | [Phase 5 — Consulta](2026-06-19-phase5-consulta.md) | Endpoint `mi-empresa` acotado al token, tabla filtrable + drawer de detalle/timeline | Phase 1 |

## Orden de implementación recomendado

`1 → 2 → 3 → 4 → 5`. Notas de acoplamiento entre fases:

- **Phase 2** introduce dos hooks inyectables con defaults no-op: `enqueue_auditoria_incapacidad`
  (lo reemplaza **Phase 4**) y el hook `integracion` (lo reemplaza **Phase 3.6**). Por eso Phase 2 es
  testeable de forma aislada y las fases posteriores solo sustituyen los defaults.
- **Phase 3** reutiliza el `RadicacionPipelineService` de Phase 2 para el submit masivo y aporta las
  reglas de validación dict-based que **Phase 4** también consume.
- **Phase 4** sustituye el no-op de enqueue por la tarea Celery real.
- **Phase 5** solo depende de Phase 1 (auth) y puede hacerse en paralelo tras Phase 1.

## Migraciones Alembic creadas (en conjunto)

1. `incapacidad.prorroga` (Phase 2)
2. `incapacidad.numero_radicacion_servialfa` (Phase 3)
3. `communication_log` (Phase 3)
4. `auditoria_resultado` (Phase 4)

## Convenciones de ejecución

- Backend: tests en Docker → `docker exec incapacidades-api python -m pytest <ruta> -v --no-cov`.
- Frontend: `npm test -- <patrón>` y `npm run build` desde `apps/frontend/portal-externo`.
- TDD por tarea (test rojo → implementación → verde → commit). Conventional Commits.
