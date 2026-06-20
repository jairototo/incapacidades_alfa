# Spec — Portal Externo: Refactor a portal autenticado para EMPRESA

- **Fecha**: 2026-06-19
- **Autor**: brainstorming session (Danilo + Claude)
- **Estado**: Aprobado para planificación
- **Alcance**: `apps/frontend/portal-externo` + cambios de soporte en `apps/backend`

---

## 1. Objetivo

Convertir el `portal-externo` (hoy público: `/`, `/consultar`, `/radicar`) en un portal
**autenticado para usuarios con rol `EMPRESA`**, que tras iniciar sesión accedan a un
dashboard con tres acciones: **Radicación Individual**, **Radicación Masiva** y
**Consulta de Incapacidades**. Todo el alcance es **solo ARL** (empresa → empleado).

La radicación deja de crear `pre_incapacidad` y pasa a crear `Incapacidad` directamente
mediante un **pipeline compartido** (individual = masiva con N=1), que resuelve el
solicitante desde la empresa autenticada, dispara un **job de auditoría** y registra
los intentos de integración con sistemas externos (**ServiAlfa**, **Sicat**) en un
**`communication_log`** para trazabilidad.

## 2. Decisiones bloqueadas (confirmadas con el usuario)

| # | Decisión |
|---|----------|
| D1 | Generar los **5 planes de fase** por adelantado; el usuario los revisa y aprueba **todos** antes de cualquier implementación. |
| D2 | Login propio en el portal reutilizando `POST /api/v1/auth/login` (espejo de `sistema-interno`). Sin login en Laravel. |
| D3 | Solo **EMPRESA** puede acceder; además debe estar **vinculada a una empresa** (`usuario.empresa_id != null`). |
| D4 | Solo **ARL**. SALUD (afiliados) queda fuera de alcance. |
| D5 | **Pipeline unificado**: individual y masiva crean `Incapacidad` directamente, resuelven solicitante desde la empresa, y corren el mismo job de auditoría + stubs + `communication_log`. Individual es N=1. |
| D6 | Consulta = **tabla filtrable + drill-down** de detalle (reusa `DetalleIncapacidad`/`TimelineEstados`), siempre acotada a la empresa autenticada. |
| D7 | Phase 4 usa una **tabla nueva** `auditoria_resultado` (no `ValidationInconsistencia`, no un flag). Almacena cada regla evaluada con pass/fail. |
| D8 | `numero` de radicación se genera **internamente** ahora (generador de secuencia existente, no UUID). El número definitivo de ServiAlfa llega después vía stub y se guarda en columna aparte. |
| D9 | Adjuntos de radicación individual usan el `FileUpload` por slots existente. El pipeline ZIP es exclusivo de la masiva. |

## 3. Hallazgos del código actual (base de reutilización)

- **Auth backend ya existe y funciona**: `POST /auth/login` (username/password → access+refresh JWT),
  `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me`. `sistema-interno` ya lo consume
  con `authStore` (Zustand + persist) e interceptores Axios con silent-refresh.
- **`UserProfileResponse` NO expone `empresa_id` ni `empresa`** → requiere enriquecimiento (única
  modificación de auth backend necesaria).
- **`Usuario.empresa_id`** es el vínculo EMPRESA→empresa (FK nullable, `lazy="selectin"` a `empresa`).
- **`Empleado.empresa_id` es NOT NULL** (relación dura, no débil como asumía el brief). El filtro
  "empleados de la empresa autenticada" funciona igual; no se depende del supuesto "empleado independiente".
- **`Incapacidad`** es FK-based (`empleado_id`, `empresa_id`, `solicitante_id`); **no** tiene `prorroga`.
  Generador `_generar_numero_incapacidad` produce `{prefix}-{fecha}-{NNNN}`.
- **Endpoint directo de creación de `Incapacidad`** ya existe (valida empleado↔empresa, empresa ACTIVA).
- **Endpoint de listado filtrable por `empresa_id`/`empresa_nit`** ya existe (base para Phase 5).
- **`Solicitante`** se identifica por `correo` único.
- **`PreIncapacidadValidationService`** valida campos planos sobre `PreIncapacidad`; debe refactorizarse
  a un módulo de reglas reutilizable que opere también sobre `Incapacidad` (FK-based).
- **Celery** disponible (`app/tasks/incapacidad_tasks.py`); patrón `asyncio.run()` documentado.
- **Diseño**: paleta Seguros Alfa (mantener intacta), Roboto, primitivos Shadcn, `shadow-sm`,
  radios suaves. Portal-externo: Tailwind v4 + Zod v4.

## 4. Cambios transversales de datos (Alembic)

> Todos los cambios de BD son migraciones Alembic. Nada de DDL manual.

1. **`incapacidad.prorroga`** — `Boolean NOT NULL DEFAULT false`.
2. **`incapacidad.numero_radicacion_servialfa`** — `String NULL` (número definitivo externo, llega vía stub).
3. **`communication_log`** (tabla nueva):
   - `id` (UUID PK), `incapacidad_id` (FK → incapacidad, NOT NULL, ondelete CASCADE),
   - `sistema` (`SERVIALFA` | `SICAT`), `estado` (`SUCCESS` | `FAILURE` | `PENDING`),
   - `payload_resumen` (JSONB/Text), `respuesta` (JSONB/Text), `created_at`.
   - Una fila por intento de integración (stub o real).
4. **`auditoria_resultado`** (tabla nueva, Phase 4):
   - `id` (UUID PK), `incapacidad_id` (FK → incapacidad, NOT NULL, ondelete CASCADE),
   - `regla` (código de regla), `categoria` (FIELD/BUSINESS/...), `aprobado` (Boolean),
   - `severidad` (ERROR|WARNING|INFO), `detalle` (Text, mensaje), `created_at`.
   - Una fila por regla evaluada (incluye las que pasan).

## 5. Requisitos por fase

### Phase 1 — Autenticación (frontend + enriquecimiento `/me`)

**Backend**: enriquecer `UserProfileResponse` con `empresa_id` y un resumen `empresa`
(nit, razón social, email_contacto, estado). Sin endpoints nuevos.

**Frontend**:
- `authStore` (Zustand + persist), tipos de auth, `loginSchema` (Zod v4).
- Instancia Axios con interceptores: `Authorization: Bearer`, silent-refresh en 401, logout en fallo de refresh.
- `LoginPage` → `POST /auth/login`; guarda tokens + perfil.
- `ProtectedRoute`: requiere autenticado **AND** `rol === 'EMPRESA'` **AND** `empresa_id != null`.
  - Si no cumple rol/empresa → pantalla de bloqueo ("Contacte a Servicio al Cliente"), no el dashboard.
- **Dashboard** (`/`): saludo + nombre de empresa + 3 tarjetas de acción (patrón `advices.md`).
- `/radicar` (wizard público viejo) → **redirect a `/login`**. `/consultar` público → retirado
  (se reemplaza por la consulta autenticada de Phase 5).

### Phase 2 — Radicación individual (`/radicar/individual`)

- Wizard reelaborado, **ARL only**, **sin paso de empresa, sin paso de solicitante** (ambos resueltos):
  - **Selector de empleado** (buscable) que lista solo empleados con `empresa_id` = empresa autenticada.
    Tooltip `?`: *"Si no encuentra al empleado, reporte el caso a Servicio al Cliente."*
  - **Switch `prorroga`** (sí/no).
  - Datos de la incapacidad (igual que hoy) + adjuntos por slots (`FileUpload` existente, sin cambios).
- Submit vía **pipeline compartido** (N=1, ver Phase 3.5).
- Backend: endpoint para listar empleados de la empresa autenticada (scope desde token).

### Phase 3 — Radicación masiva (`/radicar/masiva`)

**3.1 Plantilla Excel**
- Botón "Descargar plantilla" → **modal grande** con multiselect buscable de empleados (scope empresa).
- Sin selección → plantilla solo con encabezados. Con selección → filas pre-rellenadas.
- Incluye todos los campos del formulario individual + `prorroga`.
- Backend: `GET .../plantilla` (openpyxl) genera el `.xlsx`.

**3.2 Carga y validación**
- Usuario sube el Excel completado. Sistema **ignora filas vacías**.
- Por cada fila no vacía corre `validate_field_level` + `validate_business_rules` (reglas portadas).
- UI: tabla de resultados; **todos** los errores por fila (no solo el primero).
- Fila que pasa todo → slots individuales de archivo (`INCAPACIDAD`, `HISTORIA_CLINICA`, otros requeridos).
- Botón de borrar por fila antes del envío final.

**3.3 ZIP global** (≤ 20 MB, alternativa a la carga fila por fila)
- Convención de nombre: `{numero_documento}_{TIPO}.{ext}` (ej. `1023555444_INCAPACIDAD.pdf`).
- Backend parsea nombres, mapea cada documento a su fila, retorna el resultado de asignación.
- UI actualiza qué documentos quedaron adjuntos por fila.

**3.4 Lógica del botón de envío**
- "Radicar Incapacidades" habilitado solo si **todas** las filas pasan **todas** las validaciones
  **y** tienen todos los documentos requeridos.
- El botón es **clicable-pero-estilo-deshabilitado** (`aria-disabled`, no el atributo HTML `disabled`).
  Al hacer clic estando inválido: **(1)** banner resumen al inicio de la tabla con cuántas filas bloquean
  y por qué, **(2)** resaltar todas las filas con errores/documentos faltantes, **(3)** scroll a la primera
  fila bloqueante.

**3.5 Envío (pipeline compartido individual + masiva)**
- **No** crea `pre_incapacidad`. Crea `Incapacidad` directamente.
- Genera `numero` internamente (generador de secuencia existente).
- Almacena `Incapacidad` + documentos.
- **Solicitante**: busca `solicitante` por el correo de la empresa autenticada; si no existe, lo crea
  con datos de la empresa. Ningún dato de solicitante viene del frontend.
- Dispara el **job de auditoría** (Phase 4).
- Envía **un solo** correo resumen con todas las incapacidades radicadas y sus números.

**3.6 Integración externa (stubs — specs externas pendientes)**
- `ServiAlfaClient` (stub): recibe los datos de la incapacidad, retorna `numero_radicacion_servialfa`
  (mock), que se guarda en `Incapacidad`.
- `SicatClient` (stub): recibe los adjuntos referenciando el `numero_radicacion_servialfa`.
- Cada intento (stub o real) se registra en `communication_log` (timestamp, sistema, estado,
  resumen de payload, respuesta). Interfaz limpia para sustituir por HTTP real luego.

### Phase 4 — Job de auditoría

- Tarea Celery en `app/tasks/`, opera sobre `Incapacidad` (FK-based).
- Refactor: extraer las reglas de `PreIncapacidadValidationService` a un **módulo de reglas compartido**
  que opere tanto sobre entrada plana (PreIncapacidad) como FK (Incapacidad).
- Por cada regla persiste una fila en **`auditoria_resultado`** (regla, aprobado, severidad, detalle).
- Al terminar → transición de `Incapacidad` a **`EN_AUDITORIA`** (+ `historial_estado`).

### Phase 5 — Consulta (`/consulta`)

- Tabla filtrable acotada a la empresa autenticada (**`empresa_id` desde el token, no query param**):
  - Filtros: estado, tipo, rango de fechas, búsqueda por documento/empleado.
  - Columnas: número, empleado, CIE-10, periodo, estado.
  - Clic en fila → detalle + timeline (reusa `DetalleIncapacidad` / `TimelineEstados`).
- Backend: reutiliza el listado filtrable existente, **endurecido** para que una empresa solo vea lo suyo.

## 6. Arquitectura de integración (stubs)

```
RadicacionPipelineService.radicar(rows, empresa, user)
  └─ por cada row:
       crea Incapacidad (numero interno, prorroga, FKs validadas)
       guarda Documentos
       resuelve/crea Solicitante (por correo de empresa)
       ServiAlfaClient.enviar(incapacidad) ── log → communication_log (PENDING/SUCCESS/FAILURE)
            └─ numero_radicacion_servialfa → Incapacidad
       SicatClient.enviar(documentos, numero_servialfa) ── log → communication_log
       enqueue AuditoriaTask(incapacidad_id)
  └─ envía un correo resumen (todas las incapacidades + números)
```

`ServiAlfaClient` / `SicatClient`: interfaces con implementación stub hoy (respuesta mock + log),
sustituibles por cliente HTTP real sin tocar el pipeline.

## 7. Testing

- **Backend** (pytest en Docker, `docker exec incapacidades-api`): migraciones, pipeline de radicación,
  validación por fila, parser ZIP, generación de plantilla, stubs + `communication_log`, job de auditoría
  + `auditoria_resultado`, scoping de consulta por empresa, enriquecimiento `/me`. Umbral 70%.
- **Frontend** (vitest): authStore + guard, LoginPage, dashboard, wizard individual (selector empleado,
  prorroga), flujo masiva (tabla de validación, slots, ZIP, gating de envío), consulta. Umbral 70%.

## 8. Fuera de alcance

- SALUD / afiliados.
- Gestión de usuarios EMPRESA y asignación de roles (vive en `sistema-interno`).
- Llamadas HTTP reales a ServiAlfa/Sicat (specs pendientes; hoy solo stubs).
- Generación definitiva de `numero_radicacion` por sistemas externos (pendiente).

## 9. Entregable

Spec (este documento) → **5 planes de implementación** (uno por fase; lo transversal se reparte
en Phase 1 y Phase 3) en `docs/superpowers/plans/`, para revisión y aprobación del usuario
**antes** de escribir código.
