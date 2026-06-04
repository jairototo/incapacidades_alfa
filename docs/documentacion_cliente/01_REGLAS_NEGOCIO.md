# REGLAS DE NEGOCIO DEL SISTEMA

**Versión**: 1.0  
**Última Actualización**: Junio 2026  
**Propósito**: Documentar todas las reglas de negocio que rigen la gestión de incapacidades

---

## RN-001: TIPOS DE INCAPACIDADES SOPORTADAS

### Descripción
El sistema soporta dos tipos de incapacidades con workflows y reglas diferenciadas:

### Incapacidades ARL
Administradoras de Riesgos Laborales - Incapacidades derivadas de accidente de trabajo o enfermedad laboral.

**Características**:
- Vinculadas a empleados de empresas
- Generadas por eventos laborales
- Gestionadas por auditores ARL

**Eventos soportados**:
- Accidente de trabajo
- Enfermedad laboral
- Accidente en trayecto

**Gestión de siniestros**: Cada incapacidad ARL puede estar asociada a un siniestro que registra detalles del accidente.

### Incapacidades SALUD
Administradoras de Salud - Incapacidades de origen médico cubierto por aseguradora.

**Características**:
- Vinculadas a afiliados con pólizas de salud
- Generadas por eventos de salud
- Gestión médica

**Módulos afectados**: TODAS las capas

---

## RN-002: GENERACIÓN DE NÚMERO DE RADICADO

### Descripción
Toda solicitud recibida exitosamente debe generar un número único de radicado que permanece invariable durante el ciclo de vida de la incapacidad.

### Requisitos
1. Número debe ser único en el sistema
2. No pueden existir dos incapacidades con el mismo número
3. Generación automática al momento de radicación
4. Formato secuencial: AAAAMMNNNNNN (año, mes, número secuencial)

### Implementación
- Generado por BackendAPI al crear incapacidad
- Almacenado en tabla `incapacidad.numero`
- Índice único para evitar duplicados
- Campo de solo lectura después de generación

### Justificación
Proporciona identificación única e inmutable de cada caso para consultas públicas y trazabilidad.

**Módulos afectados**: Radicación, Consulta, Auditoría

---

## RN-003: CICLO DE VIDA - MÁQUINA DE ESTADOS

### Descripción
Las incapacidades transitan por estados predefinidos en un orden específico. Cada transición es validada y auditada.

### Estados Permitidos

```
RADICADA
  ↓
EN_AUDITORIA
  ├─ OBSERVADA (requiere correcciones)
  ├─ APROBADA (pasa a aprobación)
  ├─ RECHAZADA (cierra el caso)
  │
  └─ Si OBSERVADA: Solicitante corrige → EN_AUDITORIA (loop)

APROBADA
  ↓
EN_PAGO
  ├─ PAGADA (pago completado)
  ├─ EN_PAGO_PARCIAL (pago parcial)
  └─ PAGADA_PARCIALMENTE (pago parcial finalizado)

RECHAZADA | CANCELADA (estados finales)
```

### Validaciones por Transición

| Transición | Rol Requerido | Precondiciones | Acción |
|-----------|---------------|----------------|--------|
| RADICADA → EN_AUDITORIA | AUDITOR | Documentación mínima presente | Inicia auditoría |
| EN_AUDITORIA → OBSERVADA | AUDITOR | Inconsistencias identificadas | Registra observaciones |
| EN_AUDITORIA → APROBADA | AUDITOR | Todas validaciones OK | Aprueba |
| EN_AUDITORIA → RECHAZADA | AUDITOR | Motivo documentado | Cierra caso |
| APROBADA → EN_PAGO | ADMIN | Orden de pago generada | Inicia pago |
| EN_PAGO → PAGADA | ADMIN | Pago confirmado | Cierra |
| OBSERVADA → EN_AUDITORIA | SOLICITANTE | Correcciones remitidas | Reinicia auditoría |

### Justificación
Asegura que cada incapacidad siga el proceso correcto sin saltos ni irregularidades. La auditoría de estado proporciona trazabilidad legal y operativa.

**Módulos afectados**: Auditoría, Aprobación, Pago, Historial

---

## RN-004: RECEPCIÓN 24/7 SIN VALIDACIÓN MÉDICA

### Descripción
El portal público acepta radicaciones cualquier día a cualquier hora. NO realiza validación médica en el momento de recepción.

### Alcance de Radicación
✅ **Aceptado**:
- Datos del solicitante
- Información del trabajador/afiliado
- Información de la empresa
- Descripción del evento
- Documentos adjuntos
- Aceptación de términos

❌ **NO aceptado en radicación**:
- Validación de diagnóstico
- Determinación de origen laboral
- Cálculo de liquidación
- Aprobación económica

### Documentos Permitidos
- Incapacidad médica (PDF, JPG, PNG)
- Historia clínica (PDF, JPG, PNG)
- Epicrisis (PDF)
- FURAT (PDF)
- Soportes diagnósticos (PDF, JPG, PNG)
- Otros soportes (PDF, JPG, PNG)

### Límites Técnicos
- Archivo máximo: 20 MB
- Máximo 10 archivos por radicación
- Formatos: PDF, JPG, PNG, JPEG

### Justificación
Maximiza accesibilidad del sistema. Las validaciones profundas se ejecutan en fase de auditoría por expertos.

**Módulos afectados**: Radicación, Portal Público, Validaciones Nivel 1

---

## RN-005: ACEPTACIÓN OBLIGATORIA DE TÉRMINOS

### Descripción
Toda radicación requiere aceptación explícita de tres términos legales por parte del solicitante.

### Términos Obligatorios
1. **Habeas Data**: Consentimiento para procesamiento de datos personales
2. **Tratamiento de Datos**: Autorización de almacenamiento y uso
3. **Declaración de Veracidad**: Declaración de que la información suministrada es verídica

### Implicaciones
- Sin aceptación, la radicación es rechazada automáticamente
- Aceptación se registra y audita
- Generación de aceptación es anexada a expediente
- Incumplimiento de declaración es motivo de rechazo

### Justificación
Proporciona cobertura legal y responsabilidad del solicitante. Reduce fraude.

**Módulos afectados**: Radicación, Seguridad, Auditoría Legal

---

## RN-006: TRAZABILIDAD EXHAUSTIVA DE CAMBIOS

### Descripción
Toda modificación realizada sobre una incapacidad, siniestro u orden de pago debe quedar registrada de forma inmutable.

### Información Registrada por Cambio
- Usuario que realizó el cambio
- Fecha y hora exacta
- Acción ejecutada (transición, observación, rechazo, etc.)
- Cambios de datos (qué valores cambiaron)
- IP del usuario
- User Agent del navegador

### Tabla de Auditoría
Tabla `historial_estado` registra automáticamente:
- `entity_type`: tipo de entidad (incapacidad, siniestro, orden_pago)
- `entity_id`: ID de la entidad
- `estado_anterior`: estado previo
- `estado_nuevo`: nuevo estado
- `observacion`: observaciones
- `fecha_cambio`: timestamp UTC
- `cambiado_por_id`: usuario ID

Tabla `auditoria_log` registra todas las acciones:
- Creaciones
- Modificaciones
- Eliminaciones
- Consultas (si está habilitado)

### Retención de Datos
- Mínimo: 7 años (según legislación laboral colombiana)
- Implementación: Archivos fríos en S3 Glacier

### Justificación
Cumplimiento normativo, investigación de fraude, auditorías internas/externas.

**Módulos afectados**: TODOS - interceptor middleware

---

## RN-007: AFILIACIÓN ACTIVA REQUERIDA

### Descripción
Para que una incapacidad sea reconocida, el trabajador/afiliado debe encontrarse afiliado al sistema en el momento del evento.

### Validaciones por Tipo

#### Para ARL
- Trabajador debe estar en tabla `empleado`
- Empresa debe estar activa (estado = ACTIVO)
- Relación empleado-empresa debe estar vigente
- Fecha evento ≥ fecha ingreso del empleado

#### Para SALUD
- Afiliado debe estar en tabla `afiliado`
- Póliza debe estar vigente
- Fecha evento ≥ fecha inicio póliza
- Fecha evento ≤ fecha fin póliza (si existe)

### Resultado de Validación
- ✅ CUMPLE: Continuar auditoría
- ❌ NO CUMPLE: RECHAZAR automáticamente

### Justificación
Asegura que solo se reconozcan incapacidades de personas debidamente afiliadas.

**Módulos afectados**: Auditoría, Validaciones, Aprobación

---

## RN-008: DETERMINACIÓN DE ORIGEN (ARL)

### Descripción
Toda incapacidad ARL debe ser clasificada según su origen por el auditor. El origen determina el tratamiento del caso.

### Orígenes Permitidos
1. **Accidente de Trabajo**: Evento súbito durante labor
2. **Enfermedad Laboral**: Enfermedad causada por exposición en trabajo
3. **Accidente en Trayecto**: Accidente viajando a/desde trabajo
4. **Origen Común**: No laboral (trasladar a EPS)
5. **Pendiente de Calificación**: Requiere experto médico

### Implicaciones Operativas
- **Origen Laboral** → ARL reconoce 100% del IBC
- **Origen Común** → Trasladar a EPS, ARL no paga
- **Pendiente** → Escalar a médico especialista

### Asignación de Origen
- Realizada por AUDITOR en fase de auditoría
- Basada en documentación anexada
- Puede cambiar si hay nuevas evidencias
- Cada cambio genera historial

### Justificación
Determina la competencia de pago (ARL vs EPS). Fundamental para aplicar normativa correcta.

**Módulos afectados**: Auditoría, Aprobación, Liquidación

---

## RN-009: INCAPACIDADES CONSECUTIVAS - ANÁLISIS UNITARIO

### Descripción
Las incapacidades consecutivas relacionadas con el mismo evento deben analizarse como un único periodo de incapacidad.

### Clasificación de Incapacidades Consecutivas

| Tipo | Descripción | Tratamiento |
|------|-------------|-------------|
| **Inicial** | Primera incapacidad del evento | Análisis completo |
| **Prórroga** | Extensión del mismo diagnóstico | Validar coherencia |
| **Recaída** | Reaparición después de mejoría | Análisis de causalidad |

### Validaciones
1. Detectar períodos sin brecha (máximo 1 día de tolerancia)
2. Verificar mismo diagnóstico CIE10 (o relacionado)
3. Verificar mismo trabajador
4. Verificar mismo evento generador

### Liquidación
- Sumar todos los días de todas las incapacidades
- Generar una única orden de pago
- Unificar pagos evitando duplicación

### Justificación
Evita pagos duplicados. Refleja la realidad médica del trabajador.

**Módulos afectados**: Auditoría, Liquidación, Validaciones

---

## RN-010: VALOR DE LIQUIDACIÓN - INCAPACIDAD TEMPORAL

### Descripción
La incapacidad temporal ARL se reconoce al 100% del Ingreso Base de Cotización (IBC) del trabajador.

### Fórmula de Cálculo

```
Valor Pagar = IBC × Días Reconocidos

Donde:
- IBC = Ingreso Base de Cotización (reportado a la ARL)
- Días Reconocidos = Calculados por auditor según incapacidad médica
```

### Restricciones
1. El IBC no puede ser menor a salario mínimo vigente
2. Existe tope máximo según normativa (actualizado anualmente)
3. Se paga solo por días reconocidos por el auditor (no por la incapacidad física)

### Documento de Origen
- Para ARL: IBC declarado en reporte a fondo
- Para SALUD: Última cotización disponible

### Justificación
Normativa Ley 776 de 2002. Asegura cálculo uniforme y justo.

**Módulos afectados**: Liquidación, Auditoría, Reportes

---

## RN-011: RECHAZO DE INCAPACIDADES DUPLICADAS

### Descripción
El sistema debe detectar y rechazar incapacidades duplicadas o fraudulentas.

### Criterios de Duplicidad
Se considera duplicada si coinciden:
1. Número de documento del trabajador/afiliado
2. Diagnóstico (código CIE10)
3. Fechas (inicio ± 1 día)
4. Número de incapacidad médica (si aplica)

### Acción Automática
- Comparar contra todas las incapacidades previas
- Si se detecta duplicidad:
  - RECHAZAR automáticamente
  - Registrar como "POSIBLE_FRAUDE"
  - Notificar a supervisor de auditoría
  - Anexar análisis

### Excepciones Permitidas
- Recaudaciones (incapacidades que continúan, permitidas con justificación)
- Nuevas incapacidades del mismo trabajador (después de 30 días)

### Justificación
Prevención de fraude y pagos duplicados.

**Módulos afectados**: Auditoría, Seguridad, Validaciones

---

## RN-012: ORDEN DE PAGO - GENERACIÓN AUTOMÁTICA

### Descripción
Una incapacidad APROBADA genera automáticamente una orden de pago.

### Proceso de Generación
1. Auditor aprueba incapacidad
2. Sistema calcula valor (RN-010)
3. Genera orden de pago automáticamente
4. Estado = GENERADA
5. Notificación a aprobador

### Datos en Orden de Pago
- Número único de orden
- Beneficiario (empleado/afiliado)
- Documento identificación
- Banco y cuenta bancaria
- Valor a pagar
- Referencia de incapacidad
- Fecha de generación

### Estados de la Orden
```
GENERADA → APROBADA → EN_PROCESO → PAGADA
    │                       │
    └─────→ ANULADA ←───────┘
```

### Justificación
Automatiza generación de órdenes, reduciendo tiempos y errores manuales.

**Módulos afectados**: Auditoría, Aprobación, Pago, Liquidación

---

## RN-013: APROBACIÓN REQUIERE DECISIÓN EXPLÍCITA

### Descripción
Una orden de pago no puede ser pagada sin aprobación explícita de un aprobador autorizado.

### Requisitos de Aprobación
1. Orden debe estar en estado GENERADA
2. Aprobador debe tener rol APROBADOR o ADMIN
3. Aprobador revisa:
   - Cálculo correcto
   - Beneficiario correcto
   - Cantidad de días reconocidos
4. Aprobador ejecuta acción: APROBAR o RECHAZAR

### Registro de Aprobación
- Usuario aprobador
- Fecha y hora
- Observaciones (si aplica)
- Firma digital (futuro)

### Impacto
- Si APROBADA: Orden pasa a EN_PROCESO/PAGADA
- Si RECHAZADA: Vuelve a EN_AUDITORIA

### Justificación
Control segregado. Evita pagos sin revisión.

**Módulos afectados**: Aprobación, Órdenes de Pago

---

## RN-014: SOLICITUD DE CORRECCIONES - CICLO DE OBSERVACIÓN

### Descripción
Cuando el auditor identifica inconsistencias menores, marca la incapacidad como OBSERVADA en lugar de rechazarla.

### Proceso

1. **Auditor identifica observación** (documento faltante, dato inconsistente, etc.)
2. **Registra observación** con detalles específicos
3. **Transición**: EN_AUDITORIA → OBSERVADA
4. **Notificación**: Se envía al solicitante especificando qué corregir
5. **Corrección**: Solicitante remite documentos/datos corregidos
6. **Reingreso**: Incapacidad vuelve a EN_AUDITORIA
7. **Nueva auditoría**: Auditor valida correcciones
8. **Resultado**: APROBADA o RECHAZADA

### Límite de Ciclos
Máximo 3 ciclos de observación. En el 4to intento: RECHAZAR.

### Tiempo de Respuesta
Solicitante tiene 10 días hábiles para corregir. Si no responde: RECHAZAR automáticamente.

### Justificación
Permite mejorar información sin descartar casos viables. Mejora experiencia del solicitante.

**Módulos afectados**: Radicación, Auditoría, Notificaciones

---

## RN-015: RECHAZO - CAUSAS Y DOCUMENTACIÓN

### Descripción
Un auditor puede rechazar una incapacidad. Todo rechazo debe estar fundado y documentado.

### Causas de Rechazo Predefinidas
1. No afiliación al momento del evento
2. Información inconsistente
3. Documentación falsificada
4. Indicio de fraude
5. Diagnóstico no relacionado con evento
6. Evento anterior a afiliación
7. Incapacidad vencida
8. Falta de documentación esencial después de 10 días
9. No solicitud de corrección en tiempo
10. Duplicidad con caso anterior

### Información de Rechazo
- Causa específica (de lista predefinida)
- Observación adicional (texto libre)
- Documentación de respaldo (referencia a documentos)
- Datos para recurso (si aplica)

### Notificación
Se comunica al solicitante:
- Causa del rechazo
- Observaciones
- Procedimiento para recurso (si aplica)
- Contacto para consultas

### Justificación
Transparencia. Permite al solicitante entender decisión y ejercer derechos.

**Módulos afectados**: Auditoría, Notificaciones, Reportes

---

## RN-016: CONTROL DE ACCESO POR ROLES

### Descripción
El sistema implementa Control de Acceso Basado en Roles (RBAC) con 6 roles diferenciados.

### Roles y Permisos

| Rol | Crear | Leer | Actualizar | Eliminar | Auditar | Aprobar | Pagar |
|-----|-------|------|-----------|----------|---------|---------|-------|
| **ADMIN** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **AUDITOR** | ❌ | ✅ | ⚠️ | ❌ | ✅ | ❌ | ❌ |
| **APROBADOR** | ❌ | ✅ | ⚠️ | ❌ | ❌ | ✅ | ✅ |
| **EMPRESA** | ✅ | ⚠️ | ⚠️ | ❌ | ❌ | ❌ | ❌ |
| **EMPLEADO** | ✅ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **READONLY** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

Notas:
- ✅ = Permiso completo
- ⚠️ = Permiso limitado (solo propios registros o supervisados)
- ❌ = Sin permiso

### Visibilidad de Datos
- **ADMIN/AUDITOR/APROBADOR**: Todas las incapacidades
- **EMPRESA**: Solo incapacidades de sus empleados
- **EMPLEADO**: Solo propias incapacidades
- **READONLY**: Lectura sin acciones

### Justificación
Seguridad operativa. Segregación de funciones.

**Módulos afectados**: Autenticación, Autorización, API

---

## RN-017: DOCUMENTOS - ALMACENAMIENTO SEGURO

### Descripción
Todos los documentos se almacenan en MinIO/S3 con validación de integridad.

### Validaciones de Documento
1. Tipo MIME (PDF, JPG, PNG, JPEG)
2. Extensión archivo
3. Firma binaria (magic numbers)
4. Tamaño máximo (20 MB)
5. Archivo no vacío (> 1 KB)
6. Virus scan (futuro)

### Integridad de Datos
Cada documento almacena:
- Hash MD5 (para validación de cambios)
- Hash SHA256 (para seguridad criptográfica)
- Metadatos: tamaño, MIME type, fecha carga
- Usuario que cargó (uploaded_by_id)

### Almacenamiento Físico
- Bucket por tipo (INCAPACIDAD, HISTORIA_CLINICA, EPICRISIS, SOPORTE, etc.)
- Ruta de almacenamiento: `{bucket}/{año}/{mes}/{id_incapacidad}/{archivo}`
- Respaldo automático en S3
- Cifrado en tránsito (HTTPS) y reposo

### Control de Acceso
- Documento vinculado a incapacidad
- Acceso solo a usuarios autorizados para esa incapacidad
- Descarga registrada en auditoría

### Justificación
Seguridad, cumplimiento legal, prevención de alteración de documentos.

**Módulos afectados**: Documentos, Auditoría, Almacenamiento

---

## RN-018: VALIDACIÓN DE DATOS - 40+ VALIDACIONES

### Descripción
El sistema ejecuta validaciones exhaustivas en todos los puntos de entrada de datos.

### Categorías de Validación

#### Datos de Solicitante
- Documento obligatorio (VAL005-VAL008)
- Nombre válido (VAL009-VAL011)
- Correo válido formato (VAL012-VAL014)
- Teléfono 7-15 dígitos (VAL015-VAL017)

#### Fechas
- Formato YYYY-MM-DD (VAL019)
- No fechas imposibles (VAL020)
- Evento no futuro (VAL021)
- Fecha inicio ≤ fecha fin (VAL049)

#### Empresa
- NIT obligatorio formato (VAL027-VAL028)
- Razón social presente (VAL029)

#### Documentos
- Mínimo 1 documento (VAL030)
- Tipo permitido (VAL031)
- No vacío (VAL032)
- Tamaño ≤ 20MB (VAL033)
- Máximo 10 archivos (VAL035)

#### Seguridad
- Captcha validación (VAL036)
- Habeas data aceptada (VAL037)
- Veracidad declarada (VAL038)
- Rate limiting (VAL039)
- Antivirus/firma binaria (VAL040)

Ver documento `validaciones.md` para detalle completo.

### Resultado de Validación
- VÁLIDO: Continuar proceso
- INVÁLIDO: Rechazar con mensaje de error específico
- ADVERTENCIA: Continuar pero registrar para auditoría

### Justificación
Calidad de datos, prevención de fraude, experiencia del usuario.

**Módulos afectados**: TODAS las capas (Frontend + Backend)

---

## RN-019: NOTIFICACIONES POR EMAIL

### Descripción
El sistema envía notificaciones automáticas por email en hitos clave del trámite.

### Eventos que Generan Notificación

| Evento | Destinatario | Contenido |
|--------|--------------|----------|
| Radicación exitosa | Solicitante | Número radicado, fecha, instrucciones |
| Solicitud de corrección | Solicitante | Qué corregir, plazo, instrucciones |
| Aprobación | Solicitante | Confirmación, próximos pasos |
| Rechazo | Solicitante | Motivo, detalles, procedimiento recurso |
| Orden de pago generada | Admin/Aprobador | Detalles para revisión |
| Pago realizado | Solicitante | Confirmación, comprobante |

### Plantillas de Email
Cada notificación usa plantilla con:
- Logo de la aseguradora
- Datos del caso
- Próximos pasos
- Número de radicado (en footer)
- Contacto de soporte

### Configuración
- Servidor SMTP configurable
- Idioma: Español
- Remitente: no-reply@segurosbolivar.com

### Justificación
Transparencia, comunicación oportuna, mejora en experiencia del usuario.

**Módulos afectados**: Radicación, Auditoría, Aprobación, Pago

---

## RN-020: CATÁLOGO CIE-10

### Descripción
El sistema utiliza códigos CIE-10 de la Clasificación Internacional de Enfermedades para diagnósticos.

### Componentes
- **Tabla**: `catalogo_cie10` con 388 códigos válidos
- **Columnas**: código, descripción
- **Actualizaciones**: Anual según OMS/MINSALUD

### Validaciones
1. Código debe existir en catálogo
2. Código debe ser relevante para auditoría médica
3. Código no puede cambiar durante auditoría (solo puede descartarse)

### Consultas
- Búsqueda por código exacto
- Búsqueda por descripción (full-text search)
- Autocomplete en formularios

### Justificación
Estandarización internacional de diagnósticos. Facilita auditoría médica.

**Módulos afectados**: Radicación, Auditoría, Catalogación

---

## RN-021: INTEGRIDAD REFERENCIAL

### Descripción
Las relaciones entre tablas mantienen integridad referencial através de constraints de base de datos.

### Relaciones Principales

```
USUARIO 1 ──┬── N REFRESH_TOKEN
            ├── N INCAPACIDAD (radicado_por)
            ├── N INCAPACIDAD (auditado_por)
            ├── N INCAPACIDAD (aprobado_por)
            └── N DOCUMENTO (uploaded_by)

EMPRESA 1 ──┬── N EMPLEADO
            └── N INCAPACIDAD

EMPLEADO 1 ──── N INCAPACIDAD (ARL)
AFILIADO 1 ──── N INCAPACIDAD (SALUD)

EMPLEADO 1 ──── N SINIESTRO
INCAPACIDAD 1 ──┬── N DOCUMENTO
                ├── N HISTORIAL_ESTADO
                └── 1 ORDEN_PAGO
```

### Restricciones
- NO DELETE de tabla padre si existen referencias
- NO UPDATE de claves primarias
- CASCADE DELETE donde aplique
- Validación en aplicación antes de operaciones

### Justificación
Integridad de datos, consistencia, prevención de corrupción.

**Módulos afectados**: Base de datos, Repositories, API

---

## RN-022: CAMPOS AUDITABLES

### Descripción
Todas las tablas incluyen campos para auditoría automática.

### Campos Estándar en Todas las Tablas

```sql
id UUID PRIMARY KEY NOT NULL
created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
metadata JSONB
```

### Información de Auditoría
- `created_at`: Marca temporal de creación
- `updated_at`: Marca temporal de última modificación
- `metadata`: JSON para datos adicionales específicos
- `id`: Identificador único UUID inmutable

### Actualización Automática
- `created_at`: Se establece una sola vez al insertar
- `updated_at`: Se actualiza automáticamente en cada UPDATE
- Implementado a través de triggers de PostgreSQL

### Justificación
Auditoría, debugging, análisis histórico, compliance.

**Módulos afectados**: Todas las tablas

---

## Resumen de Reglas - Matriz de Relación

| Regla | Módulo | Fase | Estado |
|-------|--------|------|--------|
| RN-001 | Radicación | 1 | ✅ Implementada |
| RN-002 | Radicación | 1 | ✅ Implementada |
| RN-003 | Auditoría | 1 | ✅ Implementada |
| RN-004 | Radicación | 1 | ✅ Implementada |
| RN-005 | Seguridad | 1 | ✅ Implementada |
| RN-006 | Auditoría | 1 | ✅ Implementada |
| RN-007 | Auditoría | 2 | 🔄 En desarrollo |
| RN-008 | Auditoría | 2 | 🔄 En desarrollo |
| RN-009 | Auditoría | 2 | 🔄 En desarrollo |
| RN-010 | Liquidación | 2 | 🔄 En desarrollo |
| RN-011 | Seguridad | 1 | ✅ Implementada |
| RN-012 | Aprobación | 2 | 🔄 En desarrollo |
| RN-013 | Aprobación | 2 | 🔄 En desarrollo |
| RN-014 | Radicación | 1 | ✅ Implementada |
| RN-015 | Auditoría | 2 | 🔄 En desarrollo |
| RN-016 | Autenticación | 1 | ✅ Implementada |
| RN-017 | Documentos | 1 | ✅ Implementada |
| RN-018 | Validaciones | 1 | ✅ Implementada |
| RN-019 | Notificaciones | 1 | ✅ Implementada |
| RN-020 | Catalogación | 1 | ✅ Implementada |
| RN-021 | Base de Datos | 1 | ✅ Implementada |
| RN-022 | Auditoría | 1 | ✅ Implementada |

---

**Última actualización**: Junio 2026  
**Próxima revisión**: Octubre 2026 (post-launch Fase 2)
