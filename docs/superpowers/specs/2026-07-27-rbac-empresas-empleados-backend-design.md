# RBAC + Módulo Administrativo Empresas/Empleados — Diseño Backend

**Fecha**: 2026-07-27
**Branch**: iniciando_desarrollo_para_produccion
**Alcance de este documento**: Backend únicamente (Fases 1–4 de la matriz original). El frontend (Fases 5–8: rutas/guards, UI de Empresas con gráficas, UI de Empleados, carga masiva y navegación cruzada) es un spec separado que se escribirá después de que este contrato de API quede fijo.

## 0. Contexto y estado actual verificado

- `RolUsuario` (`app/utils/enums.py:87-94`): `ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY`.
- `Permissions` (`app/core/security.py:129-173`) ya define `EMPRESA_CREATE/READ/UPDATE/DELETE` y `EMPLEADO_CREATE/READ/UPDATE/DELETE`, pero **no se usan hoy** en `empresas.py`/`empleados.py`.
- `PermissionChecker` (`app/core/security.py:236-326`) es el mecanismo de autorización estándar del proyecto (patrón `dependencies=[Depends(PermissionChecker([...]))]`, ya usado en `incapacidades.py:354`).
- `empresas.py`: **ningún endpoint tiene restricción de rol** salvo `get_empresa_empleados`. `empleados.py`: **ningún endpoint tiene ni siquiera `get_current_user`**.
- `Usuario.empresa_id` (FK a `empresa.id`, nullable, `ondelete SET NULL`) **ya existe** — no requiere migración de esquema.
- `Usuario.must_change_password` **ya existe**.
- `usuario_service.py` ya tiene `_generate_temp_password()` y `reset_password()` (invalida sesiones vía `increment_token_version`) — se reutilizan como base para creación/regeneración de password de usuario-empresa.
- Creación de `Empresa` **no crea** `Usuario` hoy.
- No existe lógica de carga masiva para Empresas/Empleados; el patrón de referencia es `bulk_radicacion_service.py` (dry-run → confirmar, openpyxl).
- Migración head actual: `4d58280019e6` (`add_auditor_sucursal_assignment_columns`).

## 1. Decisiones resueltas (antes `⚠️ PENDIENTE`)

| # | Pregunta original | Decisión |
|---|---|---|
| 1 | Acceso de LIQUIDADOR a Empleados | Solo lectura (`EMPLEADO_READ`); sin crear/editar/eliminar/cargar masivo |
| 2 | LIQUIDADOR ve filtros y gráficas de Empresas | Sí, igual que AUDITOR (mismo `EMPRESA_READ`) |
| 3 | Segunda gráfica | Opción A: tendencia mensual de radicadas, últimos 12 meses |
| 4 | ¿Gráficas reflejan filtros del listado? | No — siempre globales, sin parámetros |
| 5 | Forzar cambio de password al usuario-empresa recién creado | **No** — `must_change_password=False` |
| 6 | Regenerar password invalida sesiones activas | **Sí** — se incrementa `token_version` |
| 7 | Carga masiva: parcial vs todo-o-nada | Parcial — se insertan solo las filas válidas, se reporta el resto |
| 8 | Campo "correo" de Empresa vs login del usuario | Es el mismo campo `Empresa.email_contacto` (no se agrega columna nueva) |
| 9 | `username` del usuario-empresa autogenerado | El NIT de la empresa |
| 10 | Empresas existentes sin Usuario asociado | Backfill vía migración de datos (ver §5), con pausa de confirmación antes de aplicar |
| 11 | Campos bancarios (`cuenta_bancaria`, `banco`, `tipo_cuenta`) en creación de Empleado | **No se piden** ni en creación individual ni en carga masiva — el modelo conserva las columnas (nullable) para otros flujos, pero quedan fuera de ambos formularios de creación |
| 12 | Dry-run → confirmar en carga masiva | Re-subir el mismo archivo `.xlsx` en el paso de confirmación (sin token de validación ni caché server-side) |

## 2. RBAC en Empresas y Empleados

Reutiliza el mecanismo existente, sin mecanismo paralelo.

**Matriz de permisos a aplicar** (actualiza `PermissionChecker.PERMISSIONS` en `security.py:239-280` agregando entradas de LIQUIDADOR):

| Endpoint | Permiso | Roles |
|---|---|---|
| `GET /empresas`, `GET /empresas/{id}`, `GET /empresas/analitica` | `EMPRESA_READ` | ADMIN, AUDITOR, LIQUIDADOR |
| `POST /empresas`, `PATCH /empresas/{id}`, `DELETE /empresas/{id}`, activate/deactivate, `POST /empresas/{id}/regenerar-password` | `EMPRESA_CREATE`/`UPDATE`/`DELETE` | ADMIN |
| `GET /empleados`, `GET /empleados/{id}` | `EMPLEADO_READ` | ADMIN, AUDITOR, LIQUIDADOR |
| `POST /empleados`, `PATCH /empleados/{id}`, `DELETE /empleados/{id}`, activate/deactivate, `GET /empleados/plantilla`, `POST /empleados/carga-masiva/*` | `EMPLEADO_CREATE`/`UPDATE`/`DELETE` | ADMIN, AUDITOR (no LIQUIDADOR) |

Implementación:
- Agregar `dependencies=[Depends(PermissionChecker([Permissions.X]))]` a cada endpoint de `empresas.py` y `empleados.py`.
- Agregar `current_user: Usuario = Depends(get_current_user)` donde el handler necesite el usuario (todos los de `empleados.py`, que hoy no lo tienen en absoluto).
- Reflejar la misma matriz en el frontend (`authStore.ts:112-130`, mapa de permisos duplicado del lado cliente) — se actualiza a mano, siguiendo el patrón ya existente de mantener ambos mapas sincronizados manualmente.

## 3. Relación Empresa ↔ Usuario

### Creación (`POST /empresas`)
1. Validar que `email_contacto` no esté ya en uso por otro `Usuario.email` → `409 Conflict` si lo está.
2. Transacción única: crear `Empresa` → crear `Usuario` (`username=nit`, `email=email_contacto`, `rol=RolUsuario.EMPRESA`, `empresa_id=<empresa.id>`, `password_hash=hash(temp_password)`, `must_change_password=False`) → commit conjunto. Si falla la creación del `Usuario`, rollback completo (sin `Empresa` huérfana).
3. Password temporal generado con el mismo helper que ya usa `usuario_service._generate_temp_password()`.
4. Respuesta: `EmpresaResponse` extendido con campo **solo-de-respuesta** `usuario_generado: { username, password }`, presente únicamente en esta llamada de creación — nunca en GET/list posteriores.

### Edición (`PATCH /empresas/{id}`)
- `nombre` (razón social) editable libremente.
- Si cambia `email_contacto`: validar unicidad contra otros `Usuario.email` (excluyendo el propio usuario de esta empresa) → `409` si hay conflicto; si no, actualizar `Empresa.email_contacto` y `Usuario.email` juntos en la misma transacción.

### Regenerar password (`POST /empresas/{id}/regenerar-password`, ADMIN)
- Reutiliza la generación de password temporal de `usuario_service` sobre el `Usuario` vinculado a la empresa.
- Incrementa `token_version` (invalida sesiones activas, decisión #6).
- Respuesta: `{ username, password }`, mostrada una sola vez, mismo manejo que en creación.

## 4. Endpoint de analítica

`GET /empresas/analitica` — gated con `EMPRESA_READ` (ADMIN, AUDITOR, LIQUIDADOR), sin parámetros (datos siempre globales, decisión #4). Un solo payload con ambos datasets:

```json
{
  "top_empresas": [
    { "empresa_id": 1, "razon_social": "...", "nit": "...", "total_radicadas": 142 }
  ],
  "tendencia_mensual": [
    { "periodo": "2025-08", "total": 310 }
  ]
}
```

- **`top_empresas`**: `SELECT empresa_id, razon_social, nit, COUNT(*)` sobre `incapacidades` unido a `empresas`, agrupado, `ORDER BY total DESC LIMIT 10`. Cuenta **todas** las incapacidades alguna vez radicadas por la empresa (`fecha_radicacion IS NOT NULL`), sin importar el estado actual (decisión de la pregunta sobre "radicadas").
- **`tendencia_mensual`**: `SELECT date_trunc('month', fecha_radicacion), COUNT(*)` para los últimos 12 meses, agrupado; mismos criterios de conteo. Meses sin radicaciones se completan con `total: 0` en Python (sin huecos en el gráfico de línea).
- Ambas queries son agregaciones únicas (sin N+1). Vive en un nuevo `AnaliticaService` + repositorio dedicado, siguiendo la separación services/repositories existente — no inline en el endpoint.

## 5. Migraciones

1. **Schema**: ninguna requerida — `Usuario.empresa_id` y `Usuario.must_change_password` ya existen; `RolUsuario.EMPRESA` ya existe.
2. **Data (backfill)**: para cada `Empresa` sin `Usuario` vinculado, crear uno (`username=nit`, `email=email_contacto`, `rol=EMPRESA`, password temporal, `must_change_password=False`). Se genera con `make migrate`, pero **se pausa para mostrar el script y confirmar antes de aplicarlo** contra datos reales (regla #4 de CLAUDE.md) — cada empresa retroalimentada recibe una contraseña real, así que el usuario debe verla antes de ejecutarse.

## 6. Carga masiva de Empleados (Excel)

Patrón espejo de `bulk_radicacion_service.py` (dry-run → confirmar).

**Columnas de la plantilla / carga** (campos bancarios excluidos, decisión #11):
`numero_documento, tipo_documento, nombres, apellidos, email, telefono, fecha_nacimiento, genero, cargo, area, fecha_ingreso, salario_base, nit_empresa`

1. `GET /empleados/plantilla` (`EMPLEADO_CREATE`, ADMIN/AUDITOR — solo quien puede cargar empleados necesita la plantilla; se excluye a LIQUIDADOR, que no puede escribir Empleados) — genera y descarga un `.xlsx` (openpyxl) con las columnas anteriores, una fila de ejemplo, y una hoja "Instrucciones" explicando cada columna.
2. `POST /empleados/carga-masiva/validar` (dry-run, `EMPLEADO_CREATE`) — recibe el `.xlsx`, valida fila por fila: campos obligatorios presentes, formato de `tipo_documento`/`numero_documento`, `nit_empresa` existe en BD, sin duplicados de `numero_documento` (en el archivo o ya en BD). **No escribe nada en BD.** Devuelve `{ total_filas, validas, con_error, errores: [{fila, columna, mensaje}] }`.
3. `POST /empleados/carga-masiva/confirmar` (`EMPLEADO_CREATE`) — recibe el **mismo archivo re-subido** (decisión #12, sin token de validación), lo re-parsea/re-valida desde cero con el mismo validador del dry-run, e inserta solo las filas válidas (inserción parcial, decisión #7) en una transacción. Devuelve resumen + reporte de errores descargable (`.xlsx`) para las filas inválidas.

## 7. Pruebas (pytest, async-native, `tests/unit` + `tests/integration`)

- **RBAC**: parametrizado sobre {Empresas, Empleados} × {lectura, escritura} × {ADMIN, AUDITOR, LIQUIDADOR, no autenticado} → 200/403 según la matriz de §2.
- **Creación de Empresa**: crea `Usuario` atómicamente; rollback sin `Empresa` huérfana si falla la creación del `Usuario` (mock de race de email duplicado); `usuario_generado` presente solo en la respuesta de creación, nunca en GET/list posteriores.
- **Unicidad de correo**: crear/editar con `email_contacto` duplicado → `409`.
- **Regenerar password**: `token_version` se incrementa (sesiones invalidadas).
- **Analítica**: `top_empresas` máximo 10, orden descendente; `tendencia_mensual` con 12 entradas, huecos rellenados con 0; conteos incluyen incapacidades sin importar estado actual.
- **Carga masiva**: dry-run detecta cada tipo de error (campo obligatorio faltante, `nit_empresa` inválido, `numero_documento` duplicado en archivo y en BD) sin escribir en BD; confirmar inserta solo filas válidas y devuelve reporte de errores para el resto.
- **Backfill**: cada `Empresa` preexistente sin `Usuario` queda con uno tras la migración; ninguna `Empresa` con `Usuario` ya existente se duplica.

## 8. Fuera de alcance de este documento

- Todo lo de frontend (Fases 5–8): rutas/guards, UI de Empresas con panel de gráficas, UI de Empleados, flujo de carga masiva en UI, navegación cruzada Empresas→Empleados. Spec separado, a escribir después de que este contrato de API esté aprobado.
- Cambios al modelo `Empleado` para exponer/usar `cuenta_bancaria`/`banco`/`tipo_cuenta` en algún otro flujo — quedan como están, simplemente no se piden en creación.
