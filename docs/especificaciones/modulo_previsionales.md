# Especificación — Módulo de Incapacidades Previsionales

**Versión:** v0.4
**Última actualización:** 2026-07-29
**Estado del módulo:** Fase 0 (preparación) y Fase 1 (funciones puras de negocio) completas. Fases 2-5 (persistencia, orquestación, API REST, frontend) aún no implementadas.

## Control de cambios

| Versión | Contenido |
|---|---|
| v0.1 | Levantamiento inicial del proceso manual existente (Excel + macro de auditoría + liquidación manual) que este módulo reemplaza. |
| v0.2 | Definición de roles definitivos para el módulo: `AUDITOR_PREVISIONALES` y `AUDITOR_JURIDICO`. |
| v0.3 | Etapa 0 de preparación del proyecto + hallazgos de la ingeniería inversa de la macro de Excel original (columnas, fórmulas creídas, comportamiento de la macro). |
| v0.4 | **Este documento.** Incorpora el motor de auditoría real, verificado e implementado esta sesión (19 reglas, columnas AB-AT de la hoja FORMALIZACION) donde antes solo había una descripción "inferida" de la macro. Corrige un error crítico heredado de versiones anteriores del spec: la fórmula de liquidación usa **IBC**, no SALARIO, como base de cálculo — verificado empíricamente contra el libro de auditoría real de la aseguradora. |

---

## 1. Objetivo y alcance

Reemplazar el proceso manual actual — un flujo de Excel + macro de VBA + auditoría manual fila por fila — por un módulo backend (FastAPI) + frontend (Sistema Interno) que automatice:

1. La lectura y desencriptación del archivo Excel que entrega la AFP (protegido con contraseña).
2. La segmentación mensual de los períodos de incapacidad y el pareo con las columnas de IBC/salario/días cotizados de ese archivo.
3. La liquidación del valor a pagar por incapacidad previsional.
4. La auditoría automática de 19 reglas de negocio (columnas AB-AT de la hoja `FORMALIZACION`), dejando explícitamente como `PENDIENTE` (para decisión humana) todo lo que el negocio nunca ha resuelto de forma inequívoca, en vez de adivinar.
5. La generación del libro de cargue para el sistema externo ARPIS.

**Roles del módulo** (adicionales a los roles generales del sistema — `ADMIN`, `AUDITOR`, `APROBADOR`, `EMPRESA`, `EMPLEADO`, `READONLY`, `LIQUIDADOR` — ver `app/utils/enums.py`):

| Rol | Propósito |
|---|---|
| `AUDITOR_PREVISIONALES` | Ejecuta y revisa la auditoría de incapacidades previsionales (columnas AB-AT). |
| `AUDITOR_JURIDICO` | Revisión jurídica asociada al flujo previsional. |

Ambos roles están definidos en `app/utils/enums.py` (`RolUsuario`), pasan la constraint `chk_usuario_rol` de la tabla `usuarios`, y están registrados en el diccionario `PermissionChecker.PERMISSIONS` de `app/core/security.py` (verificado en `tests/unit/test_roles_previsionales.py`).

---

## 2. Hallazgos críticos de esta versión

### 2.1 La fórmula de liquidación usa IBC, no SALARIO

Una versión anterior del spec asumía que la base de liquidación era la columna SALARIO del archivo de la AFP. Esto es **incorrecto** y quedó corregido esta sesión tras verificación empírica contra el libro real de auditoría de la aseguradora (`RADICADOS_AUDITORIA_20260706.xlsx`, en `docs/recursos_previsionales/`).

**Fórmula correcta:**

```
Σ max(IBC_mes × 50%, SMLMV_año) ÷ 30 × días_mes
```

Es decir, por cada segmento mensual: se toma el 50% del IBC de ese mes, se compara contra el SMLMV vigente en el año de ese segmento (el mayor de los dos es la base "piso"), se divide entre 30 (mes comercial) y se multiplica por los días del segmento. El total es la suma de todos los segmentos, redondeada al final (no por segmento) con `ROUND_HALF_UP`.

**Evidencia:** la fórmula con IBC coincide con la columna VALOR auditada por la aseguradora en **37 de 37** filas comparables del libro real (`test_regresion_masiva_contra_workbook_auditado`, en `tests/unit/test_liquidacion_previsional.py`). La misma fórmula usando SALARIO en vez de IBC solo coincide en 35 de 37 — los 2 casos discrepantes son la prueba definitiva de que IBC es la base correcta:

- **Identificación `16743444`**: IBC = 3.750.905, SALARIO = 0 en el archivo fuente. El resultado auditado (1.875.453) es exactamente el 50% del IBC (1.875.452,5, redondeado), no del SALARIO — que era cero.
- **Identificación `18594086`**: IBC = 4.600.000, 60 días de incapacidad, SALARIO = 0 en el archivo fuente. El resultado auditado (4.600.000) solo es reproducible con IBC como base.

La implementación (función pura, sin I/O) vive en `apps/backend/app/services/previsionales/liquidacion_previsional.py::calcular_valor`.

### 2.2 Motor de auditoría de 19 reglas (columnas AB-AT), implementado y verificado

`apps/backend/app/services/previsionales/auditoria_rules.py` implementa las 19 reglas de la hoja `FORMALIZACION`, columnas AB a AT, como funciones puras `regla_xx_*(row, ctx) -> Senal`. El registro `REGLAS_PREVISIONALES` mapea cada letra de columna a su función y se ejecuta en orden vía `evaluar_todas()`.

| Columna | Regla | Resumen |
|---|---|---|
| AB | Día 181 (auditado) | El día 181 fijado por el auditor (no el de la AFP). |
| AC | Aval | Ver contrato no negociable §2.3. |
| AD | Filas repetidas en el lote | ALERTA si hay más de una fila con la misma (identificación, fecha_inicial) en el lote. |
| AE | Día 181 (AFP) | Tomado de las solicitudes AFP precargadas. |
| AF | Día 540 (límite) | Ver contrato no negociable §2.4. |
| AG | Fecha CRIE | Tomada de las solicitudes AFP. |
| AH | FI | Ver contrato no negociable §2.3. |
| AI | FF | Ver contrato no negociable §2.3. |
| AJ | CI | Ver contrato no negociable §2.3 — PENDIENTE fijo. |
| AK | CF | Ver contrato no negociable §2.3 — PENDIENTE fijo. |
| AL | Coincidencia día 181 (Arpis vs AFP) | OK si coinciden, ALERTA si no. |
| AM | Siniestro | Ver contrato no negociable §2.3. |
| AN | Origen del siniestro | Deriva de la misma selección que AM. |
| AO | Estado del siniestro | Deriva de la misma selección que AM. |
| AP | Fechas del siniestro | Deriva de la misma selección que AM; valores tipados (fecha_aviso, fecha_siniestro). |
| AQ | Texto pago ITE | `"SE REALIZA PAGO DE ITE DE {fecha_inicial} A {fecha_final}"`. |
| AR | Siniestro + valor AFP | Concatenación de campos propios de la fila. |
| AS | Sipren | INFO — lo diligencia Sipren; fuera del alcance de este motor. |
| AT | Posible doble pago | ALERTA si (identificación, fecha_inicial) ya tiene un ITE pagado registrado. |

Estas funciones son **puras**: no hacen I/O ni acceden a BD/async; reciben una fila (`dict`) y un `ContextoAuditoria` congelado, que una capa de servicio posterior (aún no implementada) tendría que precargar **una vez por lote**, no por fila — evitando el patrón N+1 que `CLAUDE.md` señala como el pecado capital de este repo (el Laravel original hacía ~2.500 queries para 255 filas).

> **Nota de verificación:** el mapeo AB-AT documentado arriba refleja la implementación tal como quedó codificada y verificada contra pruebas unitarias esta sesión (`tests/unit/test_auditoria_rules_previsional.py`). No se hizo, dentro del alcance de esta tarea, una segunda verificación columna-por-columna contra una captura visual fresca de la hoja `FORMALIZACION`; esa verificación se hizo en la tarea que produjo `auditoria_rules.py` (Task 1.4, ver `progress.md`: "19-rule AB-AT audit engine, all 4 non-negotiable contracts verified").

### 2.3 Los 4 contratos no negociables del motor de auditoría

El motor deliberadamente **no** "arregla" con heurísticas los siguientes cuatro puntos, porque el negocio nunca los ha resuelto de forma inequívoca:

1. **AVAL (columna AC) nunca se autocalcula.** Permanece `PENDIENTE` mientras `aval is None`; solo un auditor humano lo cambia, mediante una acción separada fuera de este motor.
2. **FI/FF (columnas AH/AI) son valores tipados `{"identificacion": str, "fecha": date}`, nunca texto concatenado.** Esto corrige una fragilidad real de la macro original, que concatenaba identificación + fecha en un string y se rompía silenciosamente cuando el archivo mezclaba formatos de fecha (`dd/mm/yyyy` vs `yyyy/mm/dd`).
3. **CI/CF (columnas AJ/AK) quedan permanentemente `PENDIENTE`.** Dependen del libro externo `[1]DATOS`, que nunca fue entregado a este proyecto. Esto es una limitación **permanente** del alcance actual, no un TODO por resolver en una fase posterior.
4. **El cruce de siniestro (AM-AP) nunca elige silenciosamente entre múltiples candidatos.** Si hay más de un siniestro candidato para la misma identificación, el motor no adivina "el primero" (al estilo del `VLOOKUP` original de Excel) ni "el más reciente" (un requerimiento de negocio que nunca fue reconciliado con la macro real). En su lugar, emite `PENDIENTE` exponiendo la lista completa de candidatos (`{"candidatos": [...], "seleccionado": None}`), para que un humano decida.

### 2.4 Día 540 = Día 181 + 359 días (aritmética pura)

Se cierra el debate "360 vs 540 días" mencionado en versiones anteriores del spec: el resultado de la columna AF es el **día 540**, calculado como `día_181 + 359 días` (aritmética de calendario pura, constante `_DIAS_DIA_181_A_DIA_540 = 359` en el código). La columna informativa de la AFP sobre el día 360 es solo eso — informativa — y no participa en el cálculo del límite.

### 2.5 "Repetida" = agrupación intra-lote por (identificación, fecha_inicial)

La regla AD (filas repetidas) agrupa **todas** las filas del lote cargado por la clave `(identificación, fecha_inicial)`, sin importar el orden en que llegaron (`agrupar_repetidas()` en `auditoria_rules.py` produce el mismo resultado sin importar el orden de entrada). Esto corrige una fragilidad de la fórmula de Excel original, que solo comparaba filas **adyacentes** y por tanto no detectaba duplicados que no quedaran uno junto al otro en la hoja.

Esta resolución cubre únicamente la deduplicación **dentro de un mismo lote cargado**. Ver §4 para lo que queda pendiente sobre "repetida" contra otras fuentes (SOLICITUDES históricas, `[1]DATOS`).

---

## 3. Estado de implementación

| Componente | Estado | Ubicación |
|---|---|---|
| Roles `AUDITOR_PREVISIONALES` / `AUDITOR_JURIDICO` | ✅ Listo | `app/utils/enums.py`, `app/core/security.py` |
| Tabla `smlmv_parametros` (sembrada con 2024/2025/2026) | ✅ Listo | `app/models/previsionales/smlmv_parametros.py`, migración `87e66dac698e` |
| Segmentación mensual de fechas + parseo de columnas multivalor de la AFP | ✅ Listo (funciones puras) | `app/services/previsionales/segmentacion.py` |
| Fórmula de liquidación (base IBC), verificada 37/37 contra libro real | ✅ Listo (función pura) | `app/services/previsionales/liquidacion_previsional.py` |
| Parsers tolerantes de Excel (fecha, decimal, entero, radicado, encabezados normalizados) | ✅ Listo | `app/services/previsionales/excel_common.py` |
| Motor de 19 reglas de auditoría AB-AT | ✅ Listo, como funciones puras | `app/services/previsionales/auditoria_rules.py` |
| Exportador ARPIS (agrupación de salarios, normalización de radicado, mapeo de tipo de ingreso, construcción del libro de cargue) | ✅ Listo | `app/services/previsionales/arpis_export.py` |
| Lector/desencriptador del Excel de la AFP (contraseña, `msoffcrypto`) | 🔶 Fixture de prueba encriptada real, verificada | `tests/fixtures/afp_formalizacion_encrypted.xlsx`, `tests/unit/test_lote_excel_reader_fixture.py`; el servicio real de lectura/orquestación (`lote_excel_reader.py` o equivalente) **aún no existe** |
| `auditoria_service.py` (orquestación: precarga de `ContextoAuditoria`, ejecución por lote, persistencia de señales) | ⬜ No existe | Fase 2+ |
| `lote_service.py` (ciclo de vida del lote cargado) | ⬜ No existe | Fase 2+ |
| Modelos de BD (`lotes_previsionales`, `incapacidades_previsionales`, y tablas relacionadas de auditoría/liquidación) | ⬜ No existen | Fase 2 |
| Endpoints REST del módulo | ⬜ No existen | Fase 3+ |
| Frontend (Sistema Interno) | ⬜ No existe | Fase 4-5 |

Todo lo marcado ✅ son **funciones puras**: reciben datos ya parseados y devuelven resultados, sin tocar base de datos ni hacer llamadas de red. Esto fue deliberado (ver docstrings de cada módulo) para poder verificar la lógica de negocio de forma aislada, antes de construir la capa de persistencia/orquestación que las va a invocar.

---

## 4. Pendientes que siguen abiertos

Estos puntos **no** se resuelven en esta versión del módulo. Se dejan explícitos en vez de forzar una decisión no verificada:

- ⚠️ **PENDIENTE** — El libro externo `[1]DATOS` nunca fue entregado a este proyecto. Bloquea permanentemente las columnas CI/CF (AJ/AK) hasta que exista.
- ⚠️ **PENDIENTE** — Criterio de selección de siniestro cuando hay múltiples candidatos: "primera coincidencia" (estilo `VLOOKUP` de la macro original) vs "más reciente" (un requerimiento de negocio mencionado en algún momento, pero nunca reconciliado contra el comportamiento real de la macro). El motor expone los candidatos en vez de decidir (ver §2.3, punto 4).
- ⚠️ **PENDIENTE** — Regla de CRIE tardío: ¿se debe automatizar `max(día_181, fecha_CRIE)` como límite, o se deja siempre a criterio del auditor humano? No está codificada en ninguna fórmula verificada esta sesión.
- ⚠️ **PENDIENTE** — Criterio único de "repetida": esta sesión solo resolvió la deduplicación **intra-lote** (§2.5). Sigue sin unificar el criterio para "repetida" contra el histórico de SOLICITUDES o contra `[1]DATOS`.
- ⚠️ **PENDIENTE** — Definición funcional completa del tipo `AJUSTE` más allá de su mapeo a código ARPIS (2) + flag de ajuste en `arpis_export.py::mapear_tipo_ingreso`.
- ⚠️ **PENDIENTE** — Mapeo de tipo de documento de identificación → código ARPIS. No implementado; fuera del alcance de `arpis_export.py` tal como quedó esta sesión.
- ⚠️ **PENDIENTE** — ¿Es intencional que solo se exporte a ARPIS el primer código CIE-10 de la lista (`arpis_export.py::construir_libro_arpis`, columna R), o es una limitación temporal que debería revisarse?
- ⚠️ **PENDIENTE** — La regla del cero inicial en radicados de 15 dígitos (`normalizar_radicado`, que rellena a 16 dígitos solo si el valor tiene exactamente 15) — ¿es un requisito documentado del sistema ARPIS, o un parche empírico observado en los datos de prueba?
- ⚠️ **PENDIENTE** — Qué hacer de negocio cuando una incapacidad tiene más de 3 grupos de salario. El módulo ahora **alerta explícitamente** (`DemasiadosGruposError` en `arpis_export.py::agrupar_salarios`) en vez de perder datos silenciosamente como hacía la macro, pero la decisión de qué hacer con esa alerta (¿bloquear el lote? ¿marcarlo para revisión manual? ¿algo más?) corresponde a una capa de servicio posterior y sigue sin definirse.

---

## 5. Deuda técnica que NO se replica

Comportamientos del proceso manual (macro de Excel) que este módulo identificó como defectos y que el código nuevo evita deliberadamente. Esta tabla es guía para toda implementación futura del módulo, no solo para lo ya construido:

| Comportamiento legado (macro Excel) | Por qué no se replica en este módulo |
|---|---|
| Errores de conteo silenciosos (mismatch de filas sin aviso) | `ConteoSegmentosError` se levanta explícitamente cuando el número de segmentos no coincide con las columnas IBC/salario/días de la AFP (`segmentacion.py::parear_segmentos`) |
| Pérdida de datos cuando había más de 3 grupos de salario (los grupos 4+ se metían silenciosamente en el grupo 3) | `DemasiadosGruposError` explícito (`arpis_export.py::agrupar_salarios`) |
| Validación de encabezados por igualdad exacta, sensible a tildes/mayúsculas/espacios | `normalizar_encabezado` tolera tildes, mayúsculas y espacios múltiples antes de comparar (`excel_common.py`) |
| Errores escritos directamente en celdas de datos, en vez de reportarse aparte | Los parsers levantan `CeldaInvalidaError` tipada en vez de escribir texto de error dentro de una celda de datos |
| Tipo de documento de identificación descartado y "quemado" a un valor fijo (`"2"`) | Cuando se implemente el mapeo tipo documento → ARPIS (ver pendiente en §4), no debe repetirse este atajo — debe ser un mapeo explícito y verificable |
| Cruces de siniestro/solicitud por texto concatenado, con formatos de fecha inconsistentes (`dd/mm/yyyy` vs `yyyy/mm/dd`) | FI/FF (AH/AI) son valores tipados `{"identificacion": str, "fecha": date}`, nunca texto concatenado (ver §2.3, punto 2) |

---

## Referencias de código (verificación)

- `apps/backend/app/services/previsionales/segmentacion.py`
- `apps/backend/app/services/previsionales/liquidacion_previsional.py`
- `apps/backend/app/services/previsionales/excel_common.py`
- `apps/backend/app/services/previsionales/auditoria_rules.py`
- `apps/backend/app/services/previsionales/arpis_export.py`
- `apps/backend/app/models/previsionales/smlmv_parametros.py`
- `apps/backend/app/utils/enums.py` (`RolUsuario.AUDITOR_PREVISIONALES`, `RolUsuario.AUDITOR_JURIDICO`)
- `apps/backend/tests/unit/test_liquidacion_previsional.py`
- `apps/backend/tests/unit/test_auditoria_rules_previsional.py`
- `apps/backend/tests/unit/test_segmentacion_previsional.py`
- `apps/backend/tests/unit/test_excel_common_previsional.py`
- `apps/backend/tests/unit/test_roles_previsionales.py`
- `apps/backend/tests/unit/test_lote_excel_reader_fixture.py`
- `apps/backend/alembic/versions/20260729_1929_87e66dac698e_add_smlmv_parametros_table.py`
- `docs/recursos_previsionales/RADICADOS_AUDITORIA_20260706.xlsx` (libro de auditoría real usado para la verificación 37/37)
- `.superpowers/sdd/fizzy-gathering-adleman/progress.md` (bitácora de las tareas 0.1-1.5 que produjeron este código)
