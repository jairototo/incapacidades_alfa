# Levantamiento Funcional — Historias de Usuario

## Módulo de Incapacidades — Proceso: LIQUIDACIÓN

---

## 1. Encabezado del Documento

| Campo | Valor |
|---|---|
| Código de Necesidad/Proyecto | _(diligenciar)_ |
| Nombre Necesidad/Proyecto | Módulo de Incapacidades — Liquidación |
| Área Solicitante | _(diligenciar)_ |
| Usuarios Aprobadores | _(diligenciar)_ |
| Áreas Impactadas | Liquidación / Tesorería / Contabilidad |
| Aplicaciones Impactadas | Sistema-Interno (liquidadores, auditores, aprobadores) |
| Responsable Funcional | _(diligenciar)_ |
| Usuarios Pruebas UAT | _(diligenciar)_ |

> **Nota de alcance**: este documento cubre exclusivamente el proceso de **Liquidación** desde que una incapacidad llega a estado `LIQUIDACION`/`LIQUIDACION_PARCIAL` hasta que se marca `PAGADA`/`PAGADA_PARCIAL` mediante el módulo `Liquidacion` (el que está activo end-to-end en el Sistema-Interno). **Se excluye explícitamente el módulo de Órdenes de Pago** (`OrdenPago`, `/ordenes-pago`): su backend existe pero su frontend es un placeholder no funcional, y no fue posible confirmar con el área funcional si es un flujo canónico paralelo o legado — se documenta únicamente como hallazgo en la sección de Supuestos, sin historias de usuario asociadas, por decisión explícita del área funcional. Tampoco se incluye ninguna historia relacionada con "pre-incapacidades" (deprecado). Los procesos de Radicación y Auditoría se documentan en `HU_Radicacion_Incapacidades.md` y `HU_Auditoria_Incapacidades.md`.

---

## 2. Control de Cambio al Documento

| Fecha | Versión | Responsable | Descripción del cambio | Aplicación |
|---|---|---|---|---|
| 2026-07-16 | 1.0 | Analista Funcional (Claude Code) | Creación del documento a partir de levantamiento de código fuente (backend, sistema-interno) | Sistema-Interno |

---

## 3. Diagrama de Proceso / Hito TO-BE

```mermaid
flowchart TD
    A1([Estado: LIQUIDACION\nó LIQUIDACION_PARCIAL]) --> B1[Bandeja de Liquidación\n/incapacidades/liquidacion]

    subgraph SI["SISTEMA-INTERNO — Espacio de Liquidación"]
        B1 --> B2[Liquidador abre el caso\n/incapacidades/id/liquidacion]
        B2 --> B3[Revisa período autorizado\ny plantilla de auditoría]
        B3 --> B4[Ingresa IBL manualmente\n(integración automática pendiente)]
        B4 --> B5[Calcula desglose:\nvalor incapacidad + aportes]
        B5 --> C1{Compuerta:\n¿Liquidador conforme\ncon el desglose?}
        C1 -->|No, requiere ajuste\nde auditoría| C2[Devolver a auditoría\ncon observación]
        C1 -->|Sí| C3[Selecciona método de pago\ny guarda borrador]
        C3 --> C4{Compuerta:\n¿Completar liquidación?}
        C4 -->|Sí| C5[Completar liquidación]
    end

    C2 --> D1([Estado: EN_AUDITORIA])
    D1 -.-> D2[[Regresa a Auditoría\nver HU_Auditoria_Incapacidades.md]]

    C5 --> E1{¿Era LIQUIDACION\no LIQUIDACION_PARCIAL?}
    E1 -->|LIQUIDACION| E2([Estado: PAGADA])
    E1 -->|LIQUIDACION_PARCIAL| E3([Estado: PAGADA_PARCIAL])

    E2 --> F1[Empresa consulta estado final\nen el Portal-Externo]
    E3 --> F1

    classDef liquidacion fill:#DBEAFE,stroke:#2563EB,stroke-width:2px;
    class B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,E1,E2,E3 liquidacion;
```

**Compuertas de decisión relevantes al tramo de Liquidación**:
- **C1**: el liquidador puede detectar que el desglose calculado no corresponde a lo que auditoría autorizó, en cuyo caso devuelve el caso a auditoría con una observación obligatoria (en vez de completar el pago).
- **E1**: el estado final (`PAGADA` o `PAGADA_PARCIAL`) es determinado por el estado de origen (`LIQUIDACION` o `LIQUIDACION_PARCIAL`) heredado de la decisión tomada en Auditoría — el liquidador no elige el destino, solo confirma que el proceso de pago se completó.

---

## 4. Detalle Situación Actual de la Aplicación

### SISTEMA-INTERNO

1. **Bandeja de liquidación** (`/incapacidades/liquidacion`): lista las incapacidades en estado `LIQUIDACION` o `LIQUIDACION_PARCIAL`, con la misma estructura de columnas y filtros que la bandeja de auditoría, y una acción "Liquidar" que navega al espacio de trabajo.
2. **Espacio de liquidación** (`/incapacidades/{id}/liquidacion`): pantalla dividida — visor de documentos a la izquierda, formulario de liquidación a la derecha, más pestaña de "Historial". Solo es accesible cuando el estado de la incapacidad es `LIQUIDACION` o `LIQUIDACION_PARCIAL`; en cualquier otro estado muestra "Estado no válido para liquidación".
3. **Cálculo del desglose**: el liquidador ingresa manualmente el IBL (Ingreso Base de Liquidación) — la integración automática con el sistema externo "Imaginex" está explícitamente pendiente en el código (siempre retorna `null`). Con el IBL y los días autorizados, el sistema calcula el desglose completo mediante una fórmula parametrizada por una tabla de porcentajes vigente por año (`IblParametros`), hoy solo sembrada para el año 2026.
4. **Persistencia de la liquidación**: el liquidador puede guardar un borrador (`POST /incapacidades/{id}/liquidacion`), recalcular el desglose sin guardar (`GET .../calcular-breakdown`), devolver el caso a auditoría con observación obligatoria, o completar la liquidación, lo que transiciona la incapacidad a `PAGADA` o `PAGADA_PARCIAL` según su estado de origen.
5. **Método de pago**: selector con dos opciones (CHEQUE / OXIRRE), sin validación contra una lista real de entidades pagadoras — explícitamente pendiente de confirmación con el cliente ("C2") según el propio código.
6. **Rol responsable**: no existe un rol dedicado "LIQUIDADOR" en el sistema — la liquidación la ejecutan usuarios con rol AUDITOR o ADMIN, los mismos que participan en el proceso de Auditoría.
7. **Órdenes de Pago**: existe un módulo de backend funcional (`OrdenPago`) para generar órdenes de pago bancarias, aprobarlas y exportarlas a CSV, pero **su pantalla en el Sistema-Interno es un placeholder no funcional** y no está conectado al flujo de liquidación activo. Por decisión del área funcional, queda **fuera de alcance de este documento**.

---

## 5. Funcionalidades Impactadas

| Aplicación | Funcionalidad | EXISTENTE (ruta código/menú) | NUEVA (ruta donde se requiere) |
|---|---|---|---|
| Sistema-Interno | Bandeja de liquidación | `src/pages/incapacidades/BandejaLiquidacionPage.tsx`, `GET /incapacidades/bandeja/liquidacion` | — |
| Sistema-Interno | Cálculo del desglose de liquidación | `app/services/liquidacion_service.py`, `LiquidacionPage.tsx` | — |
| Sistema-Interno | Ingreso manual de IBL | `LiquidacionPage.tsx` (input `ibl`) | Integración automática con Imaginex (`calcular-ibl`, hoy stub) |
| Sistema-Interno | Guardar borrador de liquidación | `POST /incapacidades/{id}/liquidacion` | — |
| Sistema-Interno | Completar liquidación (marcar pagada) | `POST /incapacidades/{id}/liquidacion/completar` | — |
| Sistema-Interno | Devolver a auditoría desde liquidación | `POST /incapacidades/{id}/liquidacion/devolver` | — |
| Sistema-Interno | Selección de método de pago | `MetodoPagoLiquidacion` (CHEQUE/OXIRRE) | Validación contra lista real de entidades pagadoras (pendiente "C2") |
| Sistema-Interno | Administración de parámetros IBL por año | `IblParametros` (solo migración, sin UI) | Pantalla de administración de parámetros por año |
| Sistema-Interno | Aplicación de topes SMLDV | — | Nueva regla de cálculo en `liquidacion_service.py` |
| Sistema-Interno | Días a cargo del empleador vs. entidad (split monetario) | — | Nueva lógica de cálculo, hoy solo existe la bandera de validación `PRIMER_DIA_NO_PAGABLE` |
| Sistema-Interno | Aporte adicional trabajador pensión | Campo existe, fórmula pendiente (`liquidacion_service.py`, siempre `None`) | Definición y desarrollo de la fórmula |
| Sistema-Interno | Reliquidación / ajuste posterior a completar | — | Nuevo flujo completo |
| Sistema-Interno | Reportes de liquidación | — (`/reportes` es placeholder) | Nueva pantalla de reportes |
| Sistema-Interno | Trazabilidad/historial de liquidación | `HistorialTimeline.tsx` (reutilizado) | — |

---

## 6. Requerimientos y Criterios de Aceptación por Aplicación

```
APLICACIÓN: SISTEMA-INTERNO / # Requerimiento JIRA: ____________
  → PROCESO: LIQUIDACIÓN
```

### Historia de Usuario 1:
**Bandeja de liquidación**

**Yo Como** liquidador (rol AUDITOR o ADMIN)
**Quiero** ver una cola de las incapacidades listas para liquidar
**Para** procesar el pago de los casos aprobados por auditoría de forma ordenada

Criterios de aceptación

1. **CA1: Listado de casos en estado de liquidación**
   Dado que accedo a la bandeja de liquidación
   Cuando el sistema carga los registros
   Entonces veo únicamente las incapacidades en estado `LIQUIDACION` o `LIQUIDACION_PARCIAL`

2. **CA2: Acceso al espacio de liquidación**
   Dado que tengo un caso en la bandeja
   Cuando presiono "Liquidar"
   Entonces navego a `/incapacidades/{id}/liquidacion` con el formulario de liquidación

3. **CA3: Filtros de bandeja**
   Dado que estoy en la bandeja de liquidación
   Cuando aplico filtros de tipo, empresa o antigüedad mínima
   Entonces la tabla se actualiza mostrando solo los registros que cumplen los filtros

4. **CA4: Bandeja vacía**
   Dado que no hay incapacidades pendientes de liquidar
   Cuando cargo la bandeja
   Entonces veo el mensaje "No hay liquidaciones pendientes — No hay incapacidades en estado LIQUIDACION."

5. **CA5: Control de acceso por rol**
   Dado que un usuario con `rol=EMPRESA`, `EMPLEADO` o `READONLY` intenta acceder a la bandeja de liquidación
   Cuando la aplicación evalúa la ruta
   Entonces le niega el acceso

   Regla de negocio:
   - Acceso: ADMIN, AUDITOR (permiso `INCAPACIDAD_READ` para lectura general; `INCAPACIDAD_APPROVE` para las acciones de escritura descritas en las siguientes historias).

---

### Historia de Usuario 2:
**Cálculo del desglose de liquidación**

**Yo Como** liquidador (rol AUDITOR o ADMIN)
**Quiero** calcular el desglose económico de una incapacidad a partir del IBL y los días autorizados
**Para** determinar el valor exacto a reconocer y sus aportes asociados antes de completar el pago

Criterios de aceptación

1. **CA1: Cálculo exitoso del desglose**
   Dado que estoy en el espacio de liquidación de un caso con `dias_autorizados > 0`
   Cuando ingreso un IBL mayor a cero y presiono "Calcular desglose"
   Entonces el sistema calcula y muestra: valor de la incapacidad temporal, aporte patronal a pensión, aporte trabajador a pensión, aporte patronal a salud y aporte trabajador a salud, más el valor total

   Regla de negocio (fórmulas, unidad COP, redondeo `ROUND_HALF_UP` a 2 decimales):
   - `valor_dia = IBL / 30`
   - `valor_incapacidad_temporal = valor_dia × dias_autorizados` (100% del IBC, fundamento Ley 776 de 2002 art. 3)
   - `aporte_patronal_pension = valor_dia × dias_autorizados × (%aporte_patronal_pension / 100)`
   - `aporte_trabajador_pension = valor_dia × dias_autorizados × (%aporte_trabajador_pension / 100)`
   - `aporte_patronal_salud = valor_dia × dias_autorizados × (%aporte_patronal_salud / 100)`
   - `aporte_trabajador_salud = valor_dia × dias_autorizados × (%aporte_trabajador_salud / 100)`
   - `valor_total = valor_incapacidad_temporal + aporte_patronal_pension + aporte_trabajador_pension + aporte_patronal_salud + aporte_trabajador_salud`
   - Porcentajes vigentes para el año 2026 (tabla `IblParametros`): aporte patronal pensión **12.00%**, aporte patronal salud **8.50%**, aporte trabajador pensión **4.00%**, aporte trabajador salud **4.00%**.

2. **CA2: Días autorizados no definidos**
   Dado que la incapacidad no tiene días totales/autorizados definidos
   Cuando intento calcular el desglose
   Entonces el sistema muestra el error "No se puede calcular — La incapacidad no tiene días totales definidos" y no ejecuta el cálculo

3. **CA3: IBL obligatorio y mayor a cero**
   Dado que intento calcular el desglose sin ingresar el IBL, o con un valor menor o igual a cero
   Cuando el formulario valida el campo
   Entonces muestra "El IBL es obligatorio" o "El IBL debe ser un número mayor a 0" según corresponda, y no ejecuta el cálculo

4. **CA4: Parámetros de año no configurados**
   Dado que la fecha de inicio autorizada de la incapacidad corresponde a un año para el cual no existe una fila en la tabla de parámetros IBL (ej. 2027, año no sembrado)
   Cuando intento calcular el desglose
   Entonces el sistema retorna un error de solicitud inválida y no completa el cálculo

   Regla de negocio:
   - **[HALLAZGO — RIESGO OPERATIVO]**: la tabla `IblParametros` solo tiene sembrado el año 2026 (mediante migración de base de datos). Sin una pantalla de administración (ver HU-8), cualquier incapacidad liquidada en 2027 en adelante fallará este cálculo.

5. **CA5: Recuperación del último desglose guardado**
   Dado que reabro un caso que ya tiene una liquidación guardada previamente
   Cuando el espacio de liquidación carga
   Entonces el sistema muestra el desglose previamente guardado, sin necesidad de recalcular, hasta que yo decida hacerlo manualmente

---

### Historia de Usuario 3:
**Ingreso manual de IBL (integración automática pendiente)**

**Yo Como** liquidador (rol AUDITOR o ADMIN)
**Quiero** ingresar manualmente el IBL de la incapacidad
**Para** poder calcular la liquidación mientras la integración automática con el sistema de nómina/afiliación (Imaginex) no está disponible

Criterios de aceptación

1. **CA1: Ingreso manual habilitado**
   Dado que estoy en el formulario de liquidación
   Cuando ingreso un valor numérico en el campo IBL
   Entonces el sistema lo acepta como base para el cálculo del desglose

   Regla de negocio:
   - **[HALLAZGO — INTEGRACIÓN PENDIENTE]**: el endpoint de cálculo automático (`calcular-ibl`) existe pero siempre retorna `IBL = null`, con nota explícita en el código "Integración con Imaginex pendiente de especificación". Hoy el 100% de los IBL se ingresan manualmente.

2. **CA2: Aviso visible de integración pendiente**
   Dado que estoy en el formulario de liquidación
   Cuando visualizo el campo de IBL
   Entonces veo la nota "Integración Imaginex pendiente — ingreso manual" junto al campo

3. **CA3: Origen del IBL (fundamento normativo)**
   Dado que debo determinar el IBL de una incapacidad de origen laboral
   Cuando la incapacidad corresponde a accidente de trabajo
   Entonces debo utilizar el IBC reportado a la ARL
   Y cuando corresponde a enfermedad laboral, debo aplicar el promedio del IBC según la normatividad vigente

   Regla de negocio:
   - RN006 (Base de liquidación): Ley 1562 de 2012 — **[ANEXAR NORMA Y ANEXO TÉCNICO]** para el detalle exacto del período de promedio (meses a considerar).

4. **CA4: Integración automática (NUEVA)**
   Dado que el sistema de Imaginex está disponible e integrado
   Cuando abro el formulario de liquidación de un caso
   Entonces el sistema propone automáticamente el IBL calculado, permitiendo al liquidador aceptarlo o sobrescribirlo manualmente

   Regla de negocio:
   - **[SUPUESTO — VALIDAR]**: se documenta como mejora futura; no existe especificación técnica de la integración con Imaginex en el código ni en la documentación disponible.

---

### Historia de Usuario 4:
**Guardar borrador de liquidación**

**Yo Como** liquidador (rol AUDITOR o ADMIN)
**Quiero** guardar el avance de una liquidación sin completarla todavía
**Para** poder revisar o continuar el trabajo más tarde sin perder la información ya calculada

Criterios de aceptación

1. **CA1: Guardado exitoso**
   Dado que calculé el desglose y seleccioné un método de pago
   Cuando presiono "Guardar borrador"
   Entonces el sistema persiste el registro de liquidación (IBL, período, desglose, método de pago, notas) y muestra "Liquidación guardada correctamente"
   Y la incapacidad permanece en su estado actual (`LIQUIDACION` o `LIQUIDACION_PARCIAL`)

2. **CA2: Recalculo server-side al guardar**
   Dado que envío un borrador con IBL informado
   Cuando el backend procesa la solicitud
   Entonces recalcula el desglose completo del lado del servidor (no confía en los valores enviados por el cliente) antes de persistir

3. **CA3: Notas del liquidador**
   Dado que quiero dejar contexto adicional sobre la liquidación
   Cuando escribo hasta 1000 caracteres en el campo "Notas del liquidador" y guardo
   Entonces el sistema persiste la nota junto con el resto del registro

4. **CA4: Error al guardar**
   Dado que ocurre un error al persistir el borrador (ej. estado de la incapacidad ya no es válido para liquidación)
   Cuando intento guardar
   Entonces el sistema muestra "Error al guardar" con el detalle correspondiente y no pierde los datos ya diligenciados en el formulario

5. **CA5: Restricción de estado para guardar**
   Dado que una incapacidad no se encuentra en `LIQUIDACION` ni `LIQUIDACION_PARCIAL`
   Cuando el backend recibe una solicitud de guardado para ese caso
   Entonces la rechaza

---

### Historia de Usuario 5:
**Completar liquidación (marcar como pagada)**

**Yo Como** liquidador (rol AUDITOR o ADMIN)
**Quiero** completar formalmente la liquidación de una incapacidad
**Para** cerrar el ciclo de pago y dejar constancia de que el valor fue reconocido

Criterios de aceptación

1. **CA1: Completar liquidación desde estado LIQUIDACION**
   Dado que tengo una liquidación guardada para un caso en estado `LIQUIDACION`
   Cuando presiono "Completar liquidación" y confirmo
   Entonces el sistema transiciona la incapacidad a `PAGADA`, muestra "Liquidación completada — La incapacidad ha sido marcada como pagada." y me redirige a la bandeja de pendientes tras unos segundos

2. **CA2: Completar liquidación desde estado LIQUIDACION_PARCIAL**
   Dado que tengo una liquidación guardada para un caso en estado `LIQUIDACION_PARCIAL`
   Cuando completo la liquidación
   Entonces el sistema transiciona la incapacidad a `PAGADA_PARCIAL`

3. **CA3: Bloqueo si no existe liquidación guardada**
   Dado que intento completar una liquidación sin haber guardado previamente un borrador con desglose calculado
   Cuando presiono "Completar liquidación"
   Entonces el sistema rechaza la acción, ya que exige un registro de `Liquidacion` previamente persistido

4. **CA4: Registro en historial**
   Dado que completo una liquidación
   Cuando el sistema transiciona el estado
   Entonces registra en el historial de estados el usuario responsable, la fecha/hora y el estado resultante

5. **CA5: Error al completar**
   Dado que ocurre un error al completar (ej. condición de estado ya no válida por concurrencia)
   Cuando el sistema procesa la solicitud
   Entonces muestra "Error al completar" y no modifica el estado de la incapacidad

---

### Historia de Usuario 6:
**Devolver incapacidad a auditoría desde liquidación**

**Yo Como** liquidador (rol AUDITOR o ADMIN)
**Quiero** devolver un caso a auditoría cuando detecto que la información aprobada no permite completar correctamente la liquidación
**Para** que el auditor corrija la aprobación antes de continuar con el pago

Criterios de aceptación

1. **CA1: Devolución exitosa**
   Dado que estoy en el espacio de liquidación de un caso
   Cuando presiono "Devolver a auditoría", escribo una observación (obligatoria, máximo 1000 caracteres) y confirmo
   Entonces el sistema transiciona la incapacidad de vuelta a `EN_AUDITORIA`, muestra "Incapacidad devuelta a auditoría — El auditor recibirá la incapacidad nuevamente." y me redirige a la bandeja de pendientes

2. **CA2: Observación obligatoria**
   Dado que intento confirmar la devolución sin escribir una observación
   Cuando el sistema valida el formulario
   Entonces muestra el error correspondiente y no permite continuar

3. **CA3: Confirmación explícita antes de devolver**
   Dado que presiono "Devolver a auditoría"
   Cuando se abre el diálogo de confirmación
   Entonces veo el texto "La incapacidad {numero} será devuelta al estado EN_AUDITORIA. El auditor recibirá la incapacidad nuevamente para revisión." antes de poder confirmar

4. **CA4: Pérdida del borrador de liquidación al devolver**
   Dado que devuelvo una incapacidad a auditoría
   Cuando el auditor la vuelva a aprobar posteriormente
   Entonces el liquidador deberá recalcular/reingresar el desglose de liquidación, ya que el estado destino (`EN_AUDITORIA`) reinicia el ciclo de aprobación

   Regla de negocio:
   - **[SUPUESTO — VALIDAR]**: confirmar con el área funcional si el borrador de liquidación previamente guardado debe conservarse como referencia histórica o descartarse.

---

### Historia de Usuario 7:
**Selección de método de pago**

**Yo Como** liquidador (rol AUDITOR o ADMIN)
**Quiero** indicar el método de pago con el que se reconocerá la incapacidad
**Para** que el área de tesorería sepa cómo procesar el desembolso

Criterios de aceptación

1. **CA1: Selección de método de pago**
   Dado que estoy diligenciando el formulario de liquidación
   Cuando selecciono "Cheque" u "Oxirre (transferencia electrónica)"
   Entonces el sistema guarda la selección junto con el resto del registro de liquidación

2. **CA2: Campo opcional**
   Dado que no selecciono ningún método de pago
   Cuando guardo el borrador
   Entonces el sistema lo permite sin bloquear el guardado, dado que el campo es opcional en el estado actual

3. **CA3: Validación contra lista de entidades pagadoras (NUEVA)**
   Dado que selecciono el método de pago
   Cuando el área de negocio defina qué entidades pagan por CHEQUE y cuáles por OXIRRE
   Entonces el sistema deberá validar que el método seleccionado sea consistente con la entidad pagadora de la incapacidad

   Regla de negocio:
   - **[SUPUESTO — VALIDAR / PENDIENTE "C2"]**: el propio código documenta que "la lista de entidades que pagan por CHEQUE vs OXIRRE está pendiente de confirmación con el cliente". No se puede implementar esta validación sin esa definición.

4. **CA4: Ampliación de opciones de método de pago**
   Dado que el área funcional identifique un tercer método de pago vigente (ej. consignación directa)
   Cuando se agregue como nueva opción
   Entonces el sistema deberá soportarlo sin romper los registros de liquidación ya existentes

---

### Historia de Usuario 8:
**Administración de parámetros IBL por año** *(NUEVA)*

**Yo Como** administrador del sistema (rol ADMIN)
**Quiero** gestionar los porcentajes de aportes (pensión y salud, patronal y trabajador) vigentes para cada año
**Para** que el cálculo de liquidación siga funcionando correctamente cuando cambien los porcentajes legales o cuando inicie un nuevo año fiscal

Criterios de aceptación

1. **CA1: Consulta de parámetros vigentes**
   Dado que soy administrador
   Cuando accedo a la pantalla de "Parámetros de Liquidación"
   Entonces veo el listado de años configurados con sus 4 porcentajes (aporte patronal pensión, aporte patronal salud, aporte trabajador pensión, aporte trabajador salud)

   Regla de negocio:
   - **[SUPUESTO — VALIDAR]**: no existe ninguna pantalla ni endpoint de administración en el código actual; los parámetros solo se cargan mediante una migración de base de datos (hoy únicamente para el año 2026). Se documenta como requerimiento nuevo derivado de un riesgo operativo identificado.

2. **CA2: Creación de parámetros para un nuevo año**
   Dado que se aproxima el cierre de año y aún no existen parámetros para el siguiente
   Cuando el administrador ingresa los 4 porcentajes para el nuevo año y guarda
   Entonces el sistema crea el registro y queda disponible para el cálculo de liquidaciones cuya fecha de inicio autorizada caiga en ese año

3. **CA3: Validación de unicidad por año**
   Dado que ya existe un registro de parámetros para un año determinado
   Cuando intento crear otro registro para el mismo año
   Entonces el sistema lo rechaza indicando que ya existe una configuración para ese año (puedo editarla, no duplicarla)

4. **CA4: Alerta preventiva de año sin configurar**
   Dado que se acerca el cambio de año (ej. faltan 30 días para el 1 de enero) y no existe configuración para el año entrante
   Cuando el sistema evalúa el estado de la tabla de parámetros
   Entonces genera una alerta visible al administrador indicando que debe configurar los parámetros del nuevo año antes de que se generen errores en liquidación

---

### Historia de Usuario 9:
**Aplicación de topes SMLDV** *(NUEVA)*

**Yo Como** liquidador (rol AUDITOR o ADMIN)
**Quiero** que el sistema aplique automáticamente los topes legales basados en el Salario Mínimo Legal Diario Vigente (SMLDV)
**Para** que ningún valor liquidado exceda o incumpla los límites normativos de reconocimiento económico

Criterios de aceptación

1. **CA1: Aplicación del tope máximo**
   Dado que el valor día calculado (`IBL / 30`) supera el tope máximo permitido en SMLDV para el año vigente
   Cuando el sistema calcula el desglose
   Entonces ajusta el valor día al tope máximo antes de aplicar los porcentajes de aportes

   Regla de negocio:
   - **[ANEXAR NORMA Y ANEXO TÉCNICO — SUPUESTO]**: no existe ninguna lógica de topes SMLDV en el código actual (`liquidacion_service.py`); se requiere que el área funcional/jurídica confirme el tope exacto aplicable (múltiplo de SMLDV) y su fuente normativa antes de implementar.

2. **CA2: Configuración del valor de SMLDV por año**
   Dado que el SMLDV cambia cada año
   Cuando el administrador configura el nuevo valor para el año vigente
   Entonces el sistema lo utiliza para todos los cálculos de topes de ese año

3. **CA3: Sin afectación cuando el valor está dentro del tope**
   Dado que el valor día calculado no supera el tope SMLDV vigente
   Cuando el sistema calcula el desglose
   Entonces no aplica ningún ajuste y utiliza el valor calculado normalmente

4. **CA4: Trazabilidad del ajuste por tope**
   Dado que un cálculo fue ajustado por aplicación de un tope SMLDV
   Cuando el liquidador revisa el desglose
   Entonces el sistema indica visualmente que se aplicó un ajuste por tope, mostrando el valor original y el valor topado

---

### Historia de Usuario 10:
**Cálculo de días a cargo del empleador vs. la entidad** *(NUEVA)*

**Yo Como** liquidador (rol AUDITOR o ADMIN)
**Quiero** que el sistema calcule y separe el valor correspondiente a los días a cargo del empleador de los días a cargo de la ARL/EPS
**Para** liquidar únicamente la porción económica que le corresponde reconocer a la entidad

Criterios de aceptación

1. **CA1: Separación de días según origen**
   Dado que una incapacidad ARL tiene su fecha de inicio coincidente con la fecha del siniestro (regla `PRIMER_DIA_NO_PAGABLE`)
   Cuando el sistema calcula el desglose
   Entonces excluye monetariamente ese primer día del valor a cargo de la ARL, separándolo como día a cargo del empleador

   Regla de negocio:
   - **[ANEXAR NORMA Y ANEXO TÉCNICO — SUPUESTO]**: hoy solo existe la bandera de validación que bloquea la aprobación total (ver `HU_Auditoria_Incapacidades.md`, HU-1 CA4), pero no existe ningún cálculo monetario que separe el valor de esos días. Se requiere que el área funcional confirme la regla exacta de días a cargo del empleador según el tipo de incapacidad (origen común vs. laboral) y su fundamento normativo.

2. **CA2: Visualización del desglose por responsable de pago**
   Dado que una incapacidad tiene días a cargo del empleador y días a cargo de la entidad
   Cuando el liquidador revisa el desglose
   Entonces ve claramente diferenciado el valor total, el valor a cargo del empleador (informativo, no se paga desde este sistema) y el valor a cargo de la entidad (el que sí se liquida)

3. **CA3: Incapacidades de origen común (no aplican a la ARL)**
   Dado que una incapacidad es de origen común
   Cuando se determina el origen en auditoría (ver `HU_Auditoria_Incapacidades.md`)
   Entonces el caso se traslada a la EPS y no continúa en el módulo de liquidación de la ARL

   Regla de negocio:
   - RN003 (Determinación de origen): la ARL solamente reconoce incapacidades de origen laboral; origen común se traslada a EPS.

4. **CA4: Consistencia con el porcentaje a cargo**
   Dado que el área funcional defina el `% a cargo` de la entidad vs. el empleador para cada tramo de días
   Cuando el sistema calcule el desglose
   Entonces deberá aplicar ese porcentaje de forma configurable (no hardcodeada), para permitir ajustes normativos futuros sin requerir despliegue de código

---

### Historia de Usuario 11:
**Reliquidación / ajuste posterior a una liquidación completada** *(NUEVA)*

**Yo Como** liquidador o coordinador de liquidación (rol AUDITOR o ADMIN)
**Quiero** poder ajustar una liquidación que ya fue completada cuando se detecta un error posterior
**Para** corregir el valor reconocido sin tener que reabrir todo el ciclo de auditoría desde cero

Criterios de aceptación

1. **CA1: Solicitud de reliquidación**
   Dado que tengo una incapacidad en estado `PAGADA` o `PAGADA_PARCIAL` con un error identificado en su liquidación
   Cuando solicito una reliquidación indicando el motivo
   Entonces el sistema habilita nuevamente el formulario de liquidación conservando el registro anterior como historial

   Regla de negocio:
   - **[SUPUESTO — VALIDAR]**: no existe ningún flujo de reliquidación en el código actual; los estados `PAGADA`/`PAGADA_PARCIAL` son terminales sin transición de retorno definida en la máquina de estados (`ALLOWED_TRANSITIONS`). Requiere definición completa de diseño con el área funcional, incluyendo si se versiona la liquidación o se sobrescribe.

2. **CA2: Versionamiento del historial de liquidaciones**
   Dado que se ejecuta una reliquidación
   Cuando el nuevo cálculo se guarda
   Entonces el sistema conserva la liquidación anterior como versión histórica consultable, sin perder la trazabilidad del valor originalmente pagado

3. **CA3: Aprobación de la reliquidación**
   Dado que se genera una reliquidación con un valor distinto al original
   Cuando se completa el nuevo cálculo
   Entonces requiere una aprobación adicional (rol APROBADOR o superior) antes de confirmarse como definitiva

4. **CA4: Restricción de reliquidaciones múltiples sin control**
   Dado que una incapacidad ya tiene una reliquidación en curso
   Cuando se intenta iniciar una segunda reliquidación simultánea
   Entonces el sistema lo bloquea hasta que la primera se resuelva

---

### Historia de Usuario 12:
**Reportes de liquidación y trazabilidad** *(NUEVA para reportes; trazabilidad de historial ya existente)*

**Yo Como** coordinador de liquidación o auditoría (rol ADMIN, AUDITOR o APROBADOR)
**Quiero** consultar reportes agregados de las liquidaciones procesadas y el historial detallado de cada una
**Para** hacer seguimiento financiero y de gestión del proceso de liquidación

Criterios de aceptación

1. **CA1: Historial de cambios de estado de una liquidación**
   Dado que abro una incapacidad liquidada
   Cuando accedo a la pestaña "Historial"
   Entonces veo la línea de tiempo completa de cambios de estado, con usuario responsable, fecha y observaciones de cada transición

   Regla de negocio:
   - Esta capacidad ya existe (reutiliza `HistorialTimeline.tsx`), por lo tanto es EXISTENTE.

2. **CA2: Reporte agregado de liquidaciones por período (NUEVA)**
   Dado que soy coordinador de liquidación
   Cuando accedo a la pantalla de "Reportes" y selecciono un rango de fechas
   Entonces el sistema muestra el total de incapacidades liquidadas, el valor total pagado y el desglose por tipo (ARL) y por empresa

   Regla de negocio:
   - **[SUPUESTO — VALIDAR]**: la pantalla `/reportes` es hoy un placeholder sin ninguna funcionalidad; se requiere definición completa de los indicadores y filtros con el área funcional.

3. **CA3: Exportación del reporte**
   Dado que genero un reporte de liquidaciones
   Cuando presiono "Exportar"
   Entonces el sistema descarga el reporte en un formato reutilizable (CSV o Excel)

4. **CA4: Control de acceso por rol**
   Dado que un usuario con `rol=EMPRESA` o `EMPLEADO` intenta acceder a los reportes de liquidación
   Cuando la aplicación evalúa la ruta
   Entonces le niega el acceso, ya que esta información es de uso interno exclusivo

---

## 7. Diagrama Casos de Uso

### Caso de Uso: Calcular y completar liquidación (HU-2, HU-4, HU-5)

| Campo | Detalle |
|---|---|
| Funcionalidad Antecesora | Aprobación en auditoría (`HU_Auditoria_Incapacidades.md`, HU-3/HU-4) |
| Precondición | Incapacidad en estado `LIQUIDACION` o `LIQUIDACION_PARCIAL`; días autorizados > 0 |
| **P1** | Liquidador abre el caso desde la bandeja de liquidación — **Ejecutor: Usuario AUDITOR/ADMIN** |
| **P2** | Liquidador revisa el período autorizado y la plantilla de auditoría — **Ejecutor: Usuario AUDITOR/ADMIN** |
| **P3** | Liquidador ingresa el IBL manualmente — **Ejecutor: Usuario AUDITOR/ADMIN** |
| **P4** | Sistema calcula el desglose (valor incapacidad + 4 aportes) según parámetros del año — **Ejecutor: Sistema (Backend)** |
| **P5** | Liquidador selecciona método de pago y guarda el borrador — **Ejecutor: Usuario AUDITOR/ADMIN** |
| **P6** | Sistema recalcula y persiste el registro de liquidación server-side — **Ejecutor: Sistema (Backend)** |
| **P7** | Liquidador confirma "Completar liquidación" — **Ejecutor: Usuario AUDITOR/ADMIN** |
| **P8** | Sistema transiciona el estado a `PAGADA`/`PAGADA_PARCIAL` y registra el historial — **Ejecutor: Sistema (Backend)** |
| Postcondición | Incapacidad en estado terminal `PAGADA` o `PAGADA_PARCIAL`, con registro de liquidación completo persistido |
| Reglas de Negocio | RN005, RN006, RN007 (fórmulas de liquidación, ver HU-2 CA1); Ley 776/2002 art. 3; Ley 1562/2012 |
| Excepciones | IBL no informado o inválido; días autorizados en 0; año sin parámetros IBL configurados; estado de la incapacidad ya no válido por concurrencia |
| Volumetrías | **[SUPUESTO — VALIDAR]**: solicitar al área funcional el volumen mensual esperado de liquidaciones y el valor económico total procesado, para dimensionar controles de aprobación |
| Frecuencia de Ejecución | Diaria, ligada al ciclo de pagos de la ARL |
| Posibles Alertas | Ninguna alerta automática identificada en código (ej. no existe alerta de "liquidación pendiente hace más de N días") — **[SUPUESTO — VALIDAR]** si se requiere |
| Funcionalidad Predecesora | Ninguna dentro de este proceso |

### Caso de Uso: Devolver incapacidad a auditoría desde liquidación (HU-6)

| Campo | Detalle |
|---|---|
| Funcionalidad Antecesora | Cálculo del desglose de liquidación (HU-2) |
| Precondición | Incapacidad en estado `LIQUIDACION` o `LIQUIDACION_PARCIAL` |
| **P1** | Liquidador identifica una inconsistencia entre lo aprobado y lo liquidable — **Ejecutor: Usuario AUDITOR/ADMIN** |
| **P2** | Liquidador presiona "Devolver a auditoría" — **Ejecutor: Usuario AUDITOR/ADMIN** |
| **P3** | Liquidador registra la observación obligatoria — **Ejecutor: Usuario AUDITOR/ADMIN** |
| **P4** | Sistema transiciona el estado a `EN_AUDITORIA` y registra el historial — **Ejecutor: Sistema (Backend)** |
| Postcondición | Incapacidad regresa al proceso de Auditoría para su revisión (ver `HU_Auditoria_Incapacidades.md`) |
| Reglas de Negocio | RN004 (Trazabilidad) |
| Excepciones | Observación vacía o menor al mínimo requerido |
| Volumetrías | **[SUPUESTO — VALIDAR]** |
| Frecuencia de Ejecución | Bajo demanda, según hallazgos del liquidador |
| Posibles Alertas | Ninguna identificada |
| Funcionalidad Predecesora | Ninguna |

---

## 8. Dependencia de Otras Necesidades/Proyectos

| Proyecto/Necesidad | Tipo de Dependencia | Descripción |
|---|---|---|
| HU_Auditoria_Incapacidades.md | Predecesora | Los estados `LIQUIDACION`/`LIQUIDACION_PARCIAL` resultan de la aprobación en auditoría |
| Módulo de Órdenes de Pago (`OrdenPago`) | Excluida de este alcance | Backend funcional existente pero desconectado del flujo activo; frontend es un placeholder. Se documenta solo como hallazgo (sección 11), sin historias asociadas, por decisión del área funcional |
| Integración "Imaginex" | Dependencia técnica pendiente | Cálculo automático de IBL — hoy sin especificación técnica disponible |
| Definición normativa de topes SMLDV y % a cargo empleador/entidad | Dependencia normativa | Bloquea el desarrollo de HU-9 y HU-10 hasta contar con la fuente normativa exacta |

---

## 9. Anexos

| Nombre Anexo | Adjunto | Aplicativo y Funcionalidad |
|---|---|---|
| Ley 776 de 2002 (artículo 3) | **[ANEXAR NORMA Y ANEXO TÉCNICO]** | Subsidio = 100% del IBC — HU-2 |
| Ley 1562 de 2012 | **[ANEXAR NORMA Y ANEXO TÉCNICO]** | Base de liquidación para enfermedad laboral (promedio IBC) — HU-3 |
| Norma de topes SMLDV vigente | **[ANEXAR NORMA Y ANEXO TÉCNICO — PENDIENTE]** | HU-9 |
| Norma de días a cargo del empleador vs. entidad | **[ANEXAR NORMA Y ANEXO TÉCNICO — PENDIENTE]** | HU-10 |

---

## 10. Tabla Resumen

| N° HU | Aplicación | Proceso | Nombre HU | # CAs | Funcionalidad Existente/Nueva |
|---|---|---|---|---|---|
| HU-1 | Sistema-Interno | Liquidación | Bandeja de liquidación | 5 | Existente |
| HU-2 | Sistema-Interno | Liquidación | Cálculo del desglose de liquidación | 5 | Existente (CA4: riesgo operativo) |
| HU-3 | Sistema-Interno | Liquidación | Ingreso manual de IBL | 4 | Existente (CA4: nueva mejora) |
| HU-4 | Sistema-Interno | Liquidación | Guardar borrador de liquidación | 5 | Existente |
| HU-5 | Sistema-Interno | Liquidación | Completar liquidación | 5 | Existente |
| HU-6 | Sistema-Interno | Liquidación | Devolver a auditoría desde liquidación | 4 | Existente |
| HU-7 | Sistema-Interno | Liquidación | Selección de método de pago | 4 | Existente (CA3: nueva validación) |
| HU-8 | Sistema-Interno | Liquidación | Administración de parámetros IBL por año | 4 | **Nueva** |
| HU-9 | Sistema-Interno | Liquidación | Aplicación de topes SMLDV | 4 | **Nueva** |
| HU-10 | Sistema-Interno | Liquidación | Días a cargo empleador vs. entidad | 4 | **Nueva** |
| HU-11 | Sistema-Interno | Liquidación | Reliquidación / ajuste posterior | 4 | **Nueva** |
| HU-12 | Sistema-Interno | Liquidación | Reportes de liquidación y trazabilidad | 4 | Mixta (CA1 existente, CA2-4 nuevas) |

---

## 11. Supuestos y Pendientes por Validar con el Área Funcional

1. **[EXCLUSIÓN CONFIRMADA]** El módulo de Órdenes de Pago (`OrdenPago`, `/ordenes-pago`) queda **fuera de alcance** de este documento por decisión del área funcional. Queda como hallazgo técnico: su backend está completo (creación, aprobación, registro de pago, exportación CSV) pero su frontend en Sistema-Interno es un placeholder no funcional, y no está conectado al flujo de `Liquidacion` documentado aquí. Se recomienda una decisión de producto explícita en un futuro levantamiento sobre si este módulo se retoma, se reemplaza o se elimina del código.
2. **[RIESGO OPERATIVO — urgente]** La tabla `IblParametros` solo tiene configurado el año 2026. Sin la administración de parámetros (HU-8), toda liquidación con fecha de inicio autorizada en 2027 en adelante fallará. Se recomienda priorizar HU-8 antes del cierre de 2026.
3. **[ANEXAR NORMA — bloqueante]** Topes SMLDV (HU-9) y días a cargo del empleador vs. entidad (HU-10): no existe ninguna lógica en el código actual; ambas historias requieren la fuente normativa exacta antes de poder pasar a diseño técnico.
4. **[PENDIENTE]** Fórmula del `aporte_adicional_trabajador_pension`: el propio código lo marca como "TBD, revisión legal pendiente" — no se incluyó como historia de usuario independiente por no tener ninguna base funcional; se recomienda incorporarlo cuando el área legal defina la fórmula.
5. **[PENDIENTE "C2"]** Validación de método de pago contra lista real de entidades (HU-7, CA3): el propio código documenta esta pendiente de confirmación con el cliente.
6. **[PENDIENTE]** Reliquidación (HU-11): no existe ninguna base de código; los estados `PAGADA`/`PAGADA_PARCIAL` son hoy terminales sin transición de retorno. Requiere decisión de diseño (versionamiento vs. sobrescritura) antes de desarrollo.
7. **[PENDIENTE]** Reportes de liquidación (HU-12, CA2-CA4): la pantalla existe como placeholder sin ningún indicador definido; requiere levantamiento de indicadores con el área financiera/contable.
8. **[SUPUESTO]** No existe un rol "LIQUIDADOR" dedicado en el sistema — todas las historias de este documento asumen que las ejecuta un usuario con rol AUDITOR o ADMIN. Confirmar si el negocio requiere un rol separado con permisos propios.
9. **[SUPUESTO]** Volumetrías y valores económicos totales procesados mensualmente no están documentados en el código; se solicitan al área financiera para dimensionar controles y pruebas de carga.
