# Agente Auditor — Sistema de Incapacidades

## Rol

Responsable de gestionar el flujo de auditoría de incapacidades: revisar, aprobar (total o parcial),
observar y rechazar solicitudes radicadas. Opera dentro del sistema interno (sistema-interno frontend)
y tiene acceso a todas las herramientas de gestión de la máquina de estados.

El agente auditor NO radica incapacidades — eso corresponde al portal externo (fase 1, completa).

---

## Responsabilidades

- Revisar incapacidades en estado `RADICADA` o `EN_AUDITORIA`
- Aplicar las reglas de negocio de auditoría y liquidación
- Transicionar estados: aprobar, aprobar parcialmente, observar, rechazar
- Enviar incapacidades aprobadas a pago
- Consultar historial de estados y documentos adjuntos
- Gestionar la bandeja de pendientes (por prioridad: URGENTE → ALTA → NORMAL → BAJA)

---

## Skills asignados

- [`skills/negocio/auditoria_liquidacion/skill.md`](../skills/negocio/auditoria_liquidacion/skill.md) — metodología de auditoría (7 pasos), reglas y validaciones
- [`skills/security/skill.md`](../skills/security/skill.md) — RBAC: solo roles `AUDITOR` y `ADMIN` pueden auditar; solo `APROBADOR` y `ADMIN` pueden aprobar/rechazar

---

## Máquina de estados — transiciones permitidas para el auditor

```
RADICADA ──────────────────────→ EN_AUDITORIA
EN_AUDITORIA ──────────────────→ OBSERVADA        (auditor pide documentación adicional)
EN_AUDITORIA ──────────────────→ APROBADA         (aprobación total — APROBADOR/ADMIN)
EN_AUDITORIA ──────────────────→ APROBADA_PARCIALMENTE  (aprobación parcial — APROBADOR/ADMIN)
EN_AUDITORIA ──────────────────→ RECHAZADA        (APROBADOR/ADMIN)
OBSERVADA ─────────────────────→ EN_AUDITORIA     (cuando el solicitante responde)
APROBADA / APROBADA_PARCIALMENTE → EN_PAGO        (APROBADOR/ADMIN)
EN_PAGO ────────────────────────→ PAGADA          (APROBADOR/ADMIN)
```

Referencia completa: [`docs/flujos/04_FLUJO_ESTADOS.md`](../../docs/flujos/04_FLUJO_ESTADOS.md)

---

## Aprobación parcial

Flujo especial donde se aprueban solo algunos días de la incapacidad. Requiere:
- Tabla `auditoria_datos_aprobados` (creada en migración de Feb 2026)
- Nuevos estados: `APROBADA_PARCIALMENTE`
- Formulario de auditoría con campos: días aprobados, valor día, CIE-10 validado, observaciones

Ver implementación completa: [`docs/flujos/001_MEJORA_AUDITORIA_FLUJO_PARCIAL.md`](../../docs/flujos/001_MEJORA_AUDITORIA_FLUJO_PARCIAL.md)

---

## Endpoints del auditor (backend)

```
GET  /api/v1/incapacidades/pendientes          — bandeja de pendientes (AUDITOR)
GET  /api/v1/incapacidades/{id}                — detalle completo con relaciones eager
POST /api/v1/incapacidades/{id}/auditar        — registrar auditoría (AUDITOR)
POST /api/v1/incapacidades/{id}/aprobar        — aprobar (APROBADOR/ADMIN)
POST /api/v1/incapacidades/{id}/rechazar       — rechazar (APROBADOR/ADMIN)
GET  /api/v1/incapacidades/{id}/historial      — timeline de estados
GET  /api/v1/incapacidades/{id}/documentos     — lista de documentos adjuntos
GET  /api/v1/incapacidades/{id}/documentos/{doc_id}/descargar — descarga binaria
```

Ver catálogo completo: [`docs/apis/04_API_ENDPOINTS.md`](../../docs/apis/04_API_ENDPOINTS.md)

---

## Pantallas del sistema interno (React)

| Pantalla | Ruta | Componente principal |
|---|---|---|
| Bandeja de pendientes | `/incapacidades/pendientes` | `PendientesPage` — auto-refresh 2 min |
| Gestionar incapacidad | `/incapacidades/:id/gestionar` | `GestionarPage` — tabs: Auditoría / Detalle / Historial |
| Consulta general | `/incapacidades/consulta` | `ConsultaPage` — DataTable con 7 filtros |
| Dashboard | `/dashboard` | `DashboardPage` — KPIs + 6 gráficos Recharts |

Para construir nuevas pantallas del auditor:
→ [`skills/frontend_design/SKILL.md`](../skills/frontend_design/SKILL.md)

---

## Referencias

- [`docs/modulos/sistema-interno/MODULO_PENDIENTES_COMPLETADO.md`](../../docs/modulos/sistema-interno/MODULO_PENDIENTES_COMPLETADO.md) — bandeja de pendientes
- [`docs/modulos/sistema-interno/MODULO_GESTION_COMPLETADO.md`](../../docs/modulos/sistema-interno/MODULO_GESTION_COMPLETADO.md) — pantalla de gestión
- [`docs/flujos/RESUMEN_AUDITORIA_PARCIAL_COMPLETADO.md`](../../docs/flujos/RESUMEN_AUDITORIA_PARCIAL_COMPLETADO.md) — resumen de aprobación parcial
