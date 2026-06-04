# Matriz de Trazabilidad - Sistema de Gestión de Incapacidades

**Versión**: 2.0  
**Fecha**: Junio 2026  
**Propósito**: Relacionar historias de usuario, reglas de negocio, tablas de base de datos, endpoints API y pantallas

---

## Mapeo: HU → RN → Tablas → API → Pantallas

### HU-011: Inicio de Radicación (ARL)

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-011 - Inicio de Radicación (Portal Externo - ARL) |
| **Reglas de Negocio** | RN-001, RN-002, RN-004, RN-005, RN-006 |
| **Validaciones** | V-RAD-001 a V-RAD-004, V-PER-001 a V-PER-006 |
| **Tablas de Datos** | PRE_INCAPACIDAD, SOLICITANTE, EMPRESA |
| **Endpoints API** | `POST /api/v1/incapacidades/consulta` |
| **Servicios Backend** | `pre_incapacidad_service.crear()`, `solicitante_service.crear_o_buscar()` |
| **Pantallas Frontend** | Portal Externo: Wizard Paso 1-2 (Solicitante, Empresa) |
| **Componentes React** | RadicacionWizard, FormSolicitante, FormEmpresa |

### HU-012: Ingreso de Datos Empresa (ARL)

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-012 - Ingreso de Datos de Empresa (ARL) |
| **Reglas de Negocio** | RN-002 (empresa obligatoria ARL) |
| **Validaciones** | V-PER-004 (NIT), búsqueda en EMPRESA |
| **Tablas de Datos** | EMPRESA, PRE_INCAPACIDAD |
| **Endpoints API** | `GET /api/v1/empresas/buscar?nit=X` `POST /api/v1/incapacidades/consulta` |
| **Servicios Backend** | `empresa_service.buscar_por_nit()` |
| **Pantallas Frontend** | Wizard Paso 2 (Búsqueda/Ingreso Empresa) |

### HU-013: Ingreso de Datos Empleado (ARL)

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-013 - Ingreso de Datos del Empleado (ARL) |
| **Reglas de Negocio** | RN-002 (empleado obligatorio ARL) |
| **Validaciones** | V-PER-004 (documento), V-PER-001 (nombres/apellidos) |
| **Tablas de Datos** | EMPLEADO, PRE_INCAPACIDAD |
| **Endpoints API** | `GET /api/v1/empleados/buscar?nit=X&doc=Y` |
| **Pantallas Frontend** | Wizard Paso 3 (Búsqueda/Ingreso Empleado) |

### HU-014: Ingreso de Datos Incapacidad

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-014 - Ingreso de Datos de la Incapacidad |
| **Reglas de Negocio** | RN-005 (fechas), RN-006 (cálculo días), RN-025 (CIE-10) |
| **Validaciones** | V-RAD-002 (rangos fecha), V-RAD-003 (cálculo), V-MED-001 (CIE-10) |
| **Tablas de Datos** | PRE_INCAPACIDAD, CATALOGO_CIE10 |
| **Endpoints API** | `POST /api/v1/incapacidades/consulta` `GET /api/v1/catalogos/cie10?termino=X` |
| **Servicios Backend** | `catalogo_service.buscar_cie10()` |
| **Pantallas Frontend** | Wizard Paso 4 (Datos Médicos) |

### HU-015: Carga de Documentos

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-015 - Carga de Documentos Soportes |
| **Reglas de Negocio** | RN-026 (validación documentos), RN-027 (formato) |
| **Validaciones** | V-DOC-001, V-DOC-002, V-DOC-003, V-DOC-004 |
| **Tablas de Datos** | PRE_DOCUMENTO, MinIO (bucket) |
| **Endpoints API** | `POST /api/v1/incapacidades/documentos/upload` |
| **Servicios Backend** | `documento_service.validar_archivo()`, `storage_service.upload()` |
| **Pantallas Frontend** | Wizard Paso 5 (Carga Documentos) |
| **Componentes React** | DocumentUploadArea, FileList |

### HU-019: Procesamiento PRE_INCAPACIDAD

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-019 - Procesamiento de Radicación por Job |
| **Reglas de Negocio** | RN-001 a RN-010 (validación incapacidad) |
| **Validaciones** | Todas las validaciones de RN |
| **Tablas de Datos** | PRE_INCAPACIDAD → INCAPACIDAD, EMPRESA, EMPLEADO, DOCUMENTO |
| **Servicios Backend** | `pre_incapacidad_service.procesar()` |
| **Job/Celery** | `tasks.procesar_pre_incapacidades` (cada 5 min) |
| **Cambios BD** | PRE_INCAPACIDAD.estado: PENDIENTE → PROCESADA/RECHAZADA/ERROR |

### HU-031: Bandeja de Auditoría

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-031 - Obtener Incapacidades Pendientes de Auditoría |
| **Reglas de Negocio** | RN-031 (RBAC: AUDITOR), RN-018 (transición válida) |
| **Validaciones** | V-EST-001 (transición RADICADA → EN_AUDITORIA) |
| **Tablas de Datos** | INCAPACIDAD (filtro estado), USUARIO |
| **Endpoints API** | `GET /api/v1/incapacidades/bandeja-auditoria` |
| **Servicios Backend** | `incapacidad_service.get_bandeja_auditoria(auditor_id)` |
| **Pantallas Frontend** | Sistema Interno: Bandeja Auditoría |

### HU-033: Aprobar Incapacidad

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-033 - Aprobar Incapacidad |
| **Reglas de Negocio** | RN-012, RN-018, RN-031 (AUDITOR), RN-038 (validaciones) |
| **Validaciones** | V-EST-002 (precondiciones transición) |
| **Tablas de Datos** | INCAPACIDAD, HISTORIAL_ESTADO, AUDITORIA_DATOS_APROBADOS, AUDITORIA_LOG, DOCUMENTO |
| **Endpoints API** | `POST /api/v1/incapacidades/{id}/aprobar` |
| **Servicios Backend** | `incapacidad_service.aprobar()`, `historial_estado_service.registrar_cambio()` |
| **Eventos** | Email: "Incapacidad aprobada", AUDITORIA_LOG: CREATE |
| **Pantallas Frontend** | Vista Detalles Incapacidad con botón Aprobar |

### HU-042: Generar Orden de Pago

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-042 - Generar Orden de Pago |
| **Reglas de Negocio** | RN-015, RN-041, RN-043 (validación beneficiario) |
| **Validaciones** | V-FIN-001 a V-FIN-005 (montos, banco, cuenta) |
| **Tablas de Datos** | ORDEN_PAGO, INCAPACIDAD, HISTORIAL_ESTADO |
| **Endpoints API** | `POST /api/v1/incapacidades/{id}/generar-orden-pago` |
| **Servicios Backend** | `orden_pago_service.generar()` |
| **Transacciones** | INCAPACIDAD.estado: APROBADA → EN_PAGO |
| **Pantallas Frontend** | Vista Detalles → Form Generar Orden |

### HU-048: Confirmar Pago

| Categoría | Referencias |
|-----------|------------|
| **Historia de Usuario** | HU-048 - Confirmar Pago Realizado |
| **Reglas de Negocio** | RN-016, RN-046, RN-049 (retención comprobantes) |
| **Validaciones** | Referencia de transacción válida |
| **Tablas de Datos** | ORDEN_PAGO, INCAPACIDAD, DOCUMENTO (comprobante) |
| **Endpoints API** | `POST /api/v1/ordenes-pago/{id}/confirmar-pago` |
| **Servicios Backend** | `orden_pago_service.confirmar_pago()` |
| **Storage** | Subida de comprobante a MinIO (bucket comprobantes) |
| **Transacciones** | ORDEN_PAGO.estado: EN_PROCESO → PAGADA; INCAPACIDAD: EN_PAGO → PAGADA |

---

## Mapeo por Módulo del Sistema

### Módulo: Radicación

| Componente | Tabla | API Endpoint | HU | RN |
|-----------|-------|--------------|-----|-----|
| Portal Público | PRE_INCAPACIDAD, PRE_DOCUMENTO, SOLICITANTE | `POST /consulta` | HU-011..016 | RN-001..010 |
| Validación | CATALOGO_CIE10, EMPRESA, EMPLEADO | `GET /catalogos/cie10`, `GET /empresas/buscar` | HU-012..014 | RN-025 |
| Job Procesador | INCAPACIDAD, DOCUMENTO | Job interno | HU-019 | RN-001..010 |
| Notificaciones | USUARIO | Email via Celery | HU-016, HU-020 | RN-052 |

### Módulo: Auditoría

| Componente | Tabla | API Endpoint | HU | RN |
|-----------|-------|--------------|-----|-----|
| Bandeja | INCAPACIDAD | `GET /bandeja-auditoria` | HU-031 | RN-018..020 |
| Revisión | DOCUMENTO, HISTORIAL_ESTADO | `GET /{id}` | HU-032 | RN-032..040 |
| Aprobación | AUDITORIA_DATOS_APROBADOS, HISTORIAL_ESTADO | `POST /{id}/aprobar` | HU-033 | RN-012 |
| Rechazo | INCAPACIDAD, HISTORIAL_ESTADO | `POST /{id}/rechazar` | HU-035 | RN-014 |
| Observación | INCAPACIDAD, HISTORIAL_ESTADO | `POST /{id}/observar` | HU-034 | RN-013 |

### Módulo: Aprobación & Pagos

| Componente | Tabla | API Endpoint | HU | RN |
|-----------|-------|--------------|-----|-----|
| Bandeja Órdenes | ORDEN_PAGO | `GET /ordenes-pago/bandeja` | HU-043 | RN-041 |
| Generar OP | ORDEN_PAGO, INCAPACIDAD | `POST /{id}/generar-orden-pago` | HU-042 | RN-015, RN-041 |
| Aprobar OP | ORDEN_PAGO, AUDITORIA_LOG | `POST /ordenes-pago/{id}/aprobar` | HU-045 | RN-042 |
| Rechazar OP | ORDEN_PAGO, INCAPACIDAD | `POST /ordenes-pago/{id}/rechazar` | HU-046 | RN-046 |
| Procesar Pago | ORDEN_PAGO, INCAPACIDAD | Job interno | HU-047 | RN-045 |
| Confirmar Pago | ORDEN_PAGO, DOCUMENTO (comprobante) | `POST /ordenes-pago/{id}/confirmar-pago` | HU-048 | RN-016, RN-046 |

### Módulo: Autenticación & Acceso

| Componente | Tabla | API Endpoint | HU | RN |
|-----------|-------|--------------|-----|-----|
| Login | USUARIO, REFRESH_TOKEN | `POST /auth/login` | HU-001 | RN-031..035 |
| Logout | REFRESH_TOKEN | `POST /auth/logout` | HU-002 | RN-035 |
| Renovación Token | REFRESH_TOKEN | `POST /auth/refresh` | HU-003 | RN-036 |
| Cambio Contraseña | USUARIO | `PUT /usuarios/{id}/password` | HU-004 | RN-034, RN-036 |
| Gestión Usuarios | USUARIO | `POST/PUT/DELETE /usuarios` | HU-007..009 | RN-031, RN-039 |

### Módulo: Consulta & Reportes

| Componente | Tabla | API Endpoint | HU | RN |
|-----------|-------|--------------|-----|-----|
| Consulta Pública | INCAPACIDAD | `GET /incapacidades/consultar` | HU-021 | RN-040 |
| Búsqueda Avanzada | INCAPACIDAD | `GET /incapacidades/buscar` | HU-022 | RN-028 |
| Detalles | INCAPACIDAD, DOCUMENTO, HISTORIAL_ESTADO | `GET /incapacidades/{id}` | HU-023 | - |
| Exportación | INCAPACIDAD | `GET /incapacidades/exportar` | HU-025 | RN-039 |
| Dashboard | INCAPACIDAD, ORDEN_PAGO | `GET /estadisticas/dashboard` | HU-028 | - |
| Reportes | INCAPACIDAD, ORDEN_PAGO | `GET /reportes/...` | HU-029..030 | - |

---

## Matriz de Tabla ↔ Historial

| Tabla | Auditoría | Historial Estado | Campos Auditados |
|-------|-----------|------------------|-----------------|
| USUARIO | AUDITORIA_LOG | - | rol, estado, contraseña |
| EMPRESA | AUDITORIA_LOG | - | estado, datos contacto |
| EMPLEADO | AUDITORIA_LOG | - | estado, datos bancarios |
| INCAPACIDAD | AUDITORIA_LOG | HISTORIAL_ESTADO | estado, observaciones |
| SINIESTRO | AUDITORIA_LOG | HISTORIAL_ESTADO | estado, descripción |
| ORDEN_PAGO | AUDITORIA_LOG | HISTORIAL_ESTADO | estado, monto |
| DOCUMENTO | AUDITORIA_LOG | - | validado, observación |

---

## Validaciones por HU

| HU | Validaciones aplicadas |
|-----|--------|
| HU-011 (Radicación) | V-RAD-001..004, V-PER-001..006, V-MED-001..004 |
| HU-015 (Documentos) | V-DOC-001..004 |
| HU-033 (Aprobar) | V-EST-001..003, RN-038 |
| HU-042 (Orden Pago) | V-FIN-001..005, V-EST-002 |
| HU-001 (Login) | V-USU-001..002, RN-034..035 |

---

## API Endpoints Completo

| Método | Endpoint | HU | Autenticación | Roles |
|--------|----------|-----|---|---|
| GET | `/api/v1/incapacidades/consultar` | HU-021 | NO | Público |
| POST | `/api/v1/incapacidades/consulta` | HU-011..017 | NO | Público |
| GET | `/api/v1/incapacidades/bandeja-auditoria` | HU-031 | SÍ | AUDITOR |
| POST | `/api/v1/incapacidades/{id}/aprobar` | HU-033 | SÍ | AUDITOR |
| POST | `/api/v1/incapacidades/{id}/generar-orden-pago` | HU-042 | SÍ | ADMIN |
| POST | `/api/v1/ordenes-pago/{id}/aprobar` | HU-045 | SÍ | APROBADOR |
| POST | `/api/v1/ordenes-pago/{id}/confirmar-pago` | HU-048 | SÍ | APROBADOR |
| POST | `/api/v1/auth/login` | HU-001 | NO | Público |
| POST | `/api/v1/documentos/upload` | HU-015 | SÍ | Todos |
| GET | `/api/v1/reportes/dashboard` | HU-028 | SÍ | ADMIN, AUDITOR |

---

## Diagrama de Flujo: De HU a Implementación

```
HU-011 (Radicación)
    ↓
RN-001..010 (Validaciones tipo, fechas, etc.)
    ↓
V-RAD-001..004 (Validaciones específicas)
    ↓
PRE_INCAPACIDAD table
    ↓
POST /api/v1/incapacidades/consulta endpoint
    ↓
`pre_incapacidad_service.crear()` backend service
    ↓
RadicacionWizard React component
    ↓
Portal Externo frontend
```

---

## Cobertura de Trazabilidad

✅ **Completamente trazable**:
- Cada HU mapea a RN específicas
- Cada RN mapea a validaciones V-*
- Cada validación mapea a tablas de datos
- Cada tabla mapea a endpoints API
- Cada endpoint mapea a servicios backend
- Cada servicio mapea a pantallas frontend

**Garantía**: Un cambio en requisito puede rastrearse a través de todos los niveles

---

*Matriz sincronizada con documentación completa - Junio 2026*
