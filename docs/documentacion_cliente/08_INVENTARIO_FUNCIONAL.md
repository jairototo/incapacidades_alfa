# INVENTARIO FUNCIONAL

**Versión**: 1.0  
**Última Actualización**: Junio 2026  
**Propósito**: Matriz de funcionalidades por módulo y su estado de implementación

---

## RESUMEN EJECUTIVO

El sistema de gestión de incapacidades cuenta con **8 módulos principales** con un total de **85+ funcionalidades**, de las cuales:

- ✅ **48 Completadas** (56%)
- 🔄 **18 En Desarrollo** (21%)
- ⏳ **19 Pendientes** (23%)

---

## 1. MÓDULO: AUTENTICACIÓN Y AUTORIZACIÓN

| Funcionalidad | Descripción | Estado | Release | HU | RN |
|---|---|---|---|---|---|
| Login | Autenticación con email y contraseña | ✅ Completada | 1.0 | HU-001 | RN-040 |
| Logout | Cerrar sesión y revocar tokens | ✅ Completada | 1.0 | HU-003 | RN-040 |
| Logout All | Revocar todas las sesiones | ✅ Completada | 1.0 | HU-004 | RN-040 |
| Refresh Token | Renovar access token expirado | ✅ Completada | 1.0 | HU-005 | RN-041 |
| Cambiar Password | Cambiar contraseña propia | ✅ Completada | 1.0 | HU-006 | RN-042 |
| Reset Password | Recuperar contraseña olvidada | ⏳ Pendiente | 1.1 | HU-007 | RN-042 |
| Bloqueo Automático | Bloquear cuenta tras intentos fallidos | ✅ Completada | 1.0 | HU-002 | RN-042 |
| Desbloqueo Manual | Admin desbloquea cuenta | 🔄 En Desarrollo | 1.1 | HU-052 | RN-042 |
| Gestión de Roles | Asignar roles a usuarios | ✅ Completada | 1.0 | HU-008 | RN-045 |
| Validación RBAC | Validar permisos por rol | ✅ Completada | 1.0 | HU-009 | RN-045 |
| Auditoría de Accesos | Log de accesos al sistema | ✅ Completada | 1.0 | HU-010 | RN-050 |

**Total Autenticación**: 11 funcionalidades  
**% Completadas**: 64%

---

## 2. MÓDULO: RADICACIÓN DE INCAPACIDADES

| Funcionalidad | Descripción | Estado | Release | HU | RN |
|---|---|---|---|---|---|
| Wizard Radicación | Formulario de 6 pasos para radicar | ✅ Completada | 1.0 | HU-011 | RN-001 |
| Radicar ARL | Radicación de incapacidad laboral | ✅ Completada | 1.0 | HU-011 | RN-001 |
| Radicar SALUD | Radicación de incapacidad de salud | ✅ Completada | 1.0 | HU-019 | RN-001 |
| Validación Datos | Validar campos obligatorios | ✅ Completada | 1.0 | HU-012 | RN-005 |
| Generar Radicado | Generar número único | ✅ Completada | 1.0 | HU-011 | RN-002 |
| Cálculo Días | Calcular días automáticamente | ✅ Completada | 1.0 | HU-013 | RN-010 |
| Cálculo Valor | Calcular valor total automáticamente | ✅ Completada | 1.0 | HU-014 | RN-010 |
| Autocomplete CIE-10 | Búsqueda de diagnósticos CIE-10 | ✅ Completada | 1.0 | HU-015 | RN-012 |
| Guardar Borrador | Guardar radicación en borrador | 🔄 En Desarrollo | 1.1 | HU-016 | RN-008 |
| Editar Borrador | Editar radicación en borrador | 🔄 En Desarrollo | 1.1 | HU-017 | RN-008 |
| Cancelar Radicación | Descartar radicación sin enviar | ⏳ Pendiente | 1.1 | HU-018 | RN-008 |
| Comprobante Radicación | Generar comprobante tras radicar | ✅ Completada | 1.0 | HU-020 | RN-030 |
| Subir Documentos | Cargar documentos adjuntos | ✅ Completada | 1.0 | HU-011 | RN-020 |
| Eliminar Documento | Borrar documento antes de radicar | 🔄 En Desarrollo | 1.1 | HU-011 | RN-020 |

**Total Radicación**: 14 funcionalidades  
**% Completadas**: 71%

---

## 3. MÓDULO: CONSULTA Y SEGUIMIENTO

| Funcionalidad | Descripción | Estado | Release | HU | RN |
|---|---|---|---|---|---|
| Consulta Pública | Consultar sin autenticación por número | ✅ Completada | 1.0 | HU-021 | RN-002 |
| Listar Mis Incapacidades | Ver listado personal | ✅ Completada | 1.0 | HU-022 | RN-002 |
| Ver Detalles | Ver información completa | ✅ Completada | 1.0 | HU-023 | RN-002 |
| Descargar Documentos | Descargar archivos adjuntos | ✅ Completada | 1.0 | HU-024 | RN-020 |
| Historial de Cambios | Ver quién cambió qué y cuándo | ✅ Completada | 1.0 | HU-025 | RN-050 |
| Búsqueda Avanzada | Filtros complejos de búsqueda | 🔄 En Desarrollo | 1.1 | HU-026 | RN-002 |
| Exportar Excel | Descargar listado en Excel | ⏳ Pendiente | 1.1 | HU-027 | RN-060 |
| Notificaciones en Tiempo Real | Alertas de cambios de estado | 🔄 En Desarrollo | 1.2 | HU-028 | RN-055 |
| Ver Borradores | Listar radicaciones pendientes | 🔄 En Desarrollo | 1.1 | HU-029 | RN-008 |
| Estadísticas | Gráficos y análisis de casos | ⏳ Pendiente | 1.2 | HU-030 | RN-060 |

**Total Consulta**: 10 funcionalidades  
**% Completadas**: 60%

---

## 4. MÓDULO: AUDITORÍA

| Funcionalidad | Descripción | Estado | Release | HU | RN |
|---|---|---|---|---|---|
| Ver Pendientes de Auditoría | Listar casos EN_AUDITORIA | ✅ Completada | 1.0 | HU-031 | RN-003 |
| Asignar a Auditor | Distribuir casos a auditores | ⏳ Pendiente | 1.1 | HU-032 | RN-025 |
| Revisar Documentación | Ver documentos del caso | ✅ Completada | 1.0 | HU-033 | RN-025 |
| Solicitar Documentos | Pedir documentos faltantes | ⏳ Pendiente | 1.1 | HU-034 | RN-025 |
| Aprobar Incapacidad | Cambiar a APROBADA | ✅ Completada | 1.0 | HU-035 | RN-003 |
| Observar Incapacidad | Solicitar correcciones (OBSERVADA) | ✅ Completada | 1.0 | HU-036 | RN-003 |
| Rechazar Incapacidad | Terminar caso (RECHAZADA) | ✅ Completada | 1.0 | HU-037 | RN-003 |
| Registrar Datos Aprobados | Guardar snapshot de aprobación | ✅ Completada | 1.0 | HU-038 | RN-025 |
| Auditoría por Muestreo | Selección aleatoria de casos | ⏳ Pendiente | 1.3 | HU-039 | RN-025 |
| Reporte de Auditoría | Métricas de performance de auditores | ⏳ Pendiente | 1.2 | HU-040 | RN-060 |

**Total Auditoría**: 10 funcionalidades  
**% Completadas**: 70%

---

## 5. MÓDULO: APROBACIÓN Y PAGO

| Funcionalidad | Descripción | Estado | Release | HU | RN |
|---|---|---|---|---|---|
| Generar Orden de Pago | Crear orden para incapacidad aprobada | ✅ Completada | 1.0 | HU-041 | RN-030 |
| Aprobar Orden | Autorizar orden para pago | ✅ Completada | 1.0 | HU-042 | RN-030 |
| Rechazar Orden | Anular orden antes de pagar | ✅ Completada | 1.0 | HU-043 | RN-030 |
| Ejecutar Pago | Registrar pago realizado | ✅ Completada | 1.0 | HU-044 | RN-030 |
| Pago Parcial | Registrar pago de monto menor | ✅ Completada | 1.0 | HU-045 | RN-030 |
| Anular Orden | Cancelar orden de pago | ✅ Completada | 1.0 | HU-046 | RN-030 |
| Ver Órdenes Pendientes | Listar órdenes APROBADAS | ✅ Completada | 1.0 | HU-047 | RN-030 |
| Reconciliación de Pagos | Comparar pagos vs banco | ⏳ Pendiente | 1.3 | HU-048 | RN-030 |
| Orden Manual | Crear orden sin incapacidad | ⏳ Pendiente | 1.2 | HU-049 | RN-030 |
| Comprobante de Pago | Generar PDF de confirmación | ⏳ Pendiente | 1.1 | HU-050 | RN-030 |

**Total Pago**: 10 funcionalidades  
**% Completadas**: 70%

---

## 6. MÓDULO: ADMINISTRACIÓN DE USUARIOS

| Funcionalidad | Descripción | Estado | Release | HU | RN |
|---|---|---|---|---|---|
| Crear Usuario | Admin agrega nuevo usuario | ✅ Completada | 1.0 | HU-051 | RN-045 |
| Editar Usuario | Admin modifica datos de usuario | 🔄 En Desarrollo | 1.1 | - | RN-045 |
| Listar Usuarios | Ver todos los usuarios | 🔄 En Desarrollo | 1.1 | - | RN-045 |
| Bloquear Usuario | Suspender acceso | ✅ Completada | 1.0 | HU-052 | RN-045 |
| Desbloquear Usuario | Reactivar acceso | 🔄 En Desarrollo | 1.1 | HU-052 | RN-045 |
| Resetear Password | Admin genera password temporal | 🔄 En Desarrollo | 1.1 | - | RN-042 |
| Cambiar Rol | Modificar rol de usuario | 🔄 En Desarrollo | 1.1 | - | RN-045 |
| Log de Cambios Admin | Auditoría de acciones de admin | 🔄 En Desarrollo | 1.1 | - | RN-050 |

**Total Admin**: 8 funcionalidades  
**% Completadas**: 37%

---

## 7. MÓDULO: REPORTES Y ANÁLISIS

| Funcionalidad | Descripción | Estado | Release | HU | RN |
|---|---|---|---|---|---|
| Reporte por Estado | Incapacidades agrupadas por estado | ⏳ Pendiente | 1.2 | HU-053 | RN-060 |
| Reporte por Empresa | Análisis por empresa | ⏳ Pendiente | 1.2 | HU-054 | RN-060 |
| Dashboard Ejecutivo | KPIs principales para director | ⏳ Pendiente | 1.2 | HU-055 | RN-060 |
| Exportar PDF | Descargar reportes en PDF | ⏳ Pendiente | 1.2 | - | RN-060 |
| Gráficos Interactivos | Charts dinámicos | ⏳ Pendiente | 1.2 | - | RN-060 |
| Alertas Automáticas | Notificaciones de anomalías | ⏳ Pendiente | 1.3 | - | RN-055 |

**Total Reportes**: 6 funcionalidades  
**% Completadas**: 0%

---

## 8. MÓDULO: CATÁLOGOS Y REFERENCIA

| Funcionalidad | Descripción | Estado | Release | HU | RN |
|---|---|---|---|---|---|
| CIE-10 CRUD | Gestionar códigos de diagnóstico | 🔄 En Desarrollo | 1.1 | - | RN-012 |
| Municipios | Catálogo de ciudades | ✅ Completada | 1.0 | - | RN-013 |
| Departamentos | Catálogo de departamentos | ✅ Completada | 1.0 | - | RN-013 |
| Tipos de Documentos | Catálogo de tipos de archivo | ✅ Completada | 1.0 | - | RN-020 |
| EPS | Entidades prestadores de salud | ✅ Completada | 1.0 | - | RN-014 |
| IPS | Instituciones prestadoras de servicios | ✅ Completada | 1.0 | - | RN-014 |
| Sincronización Catálogos | Actualizar desde sistema externo | ⏳ Pendiente | 1.2 | - | RN-013 |

**Total Catálogos**: 7 funcionalidades  
**% Completadas**: 86%

---

## 9. MÓDULO: INTEGRACIÓN DE DATOS

| Funcionalidad | Descripción | Estado | Release | HU | RN |
|---|---|---|---|---|---|
| Importar Empleados | Upload masivo de empleados | 🔄 En Desarrollo | 1.1 | - | RN-015 |
| Importar Afiliados | Upload masivo de afiliados | 🔄 En Desarrollo | 1.1 | - | RN-015 |
| Sincronización Empresas | Integración con sistema externo | 🔄 En Desarrollo | 1.1 | - | RN-015 |
| Validación de Duplicados | Detectar empresas/empleados duplicados | ⏳ Pendiente | 1.2 | - | RN-005 |
| Reporte de Importaciones | Historial de imports | ⏳ Pendiente | 1.2 | - | RN-050 |

**Total Integración**: 5 funcionalidades  
**% Completadas**: 40%

---

## MATRIZ DE COBERTURA POR RELEASE

| Release | Versión | Fecha Estimada | Funcionalidades | Estado |
|---------|---------|---|---|---|
| Phase 1 | 1.0 | Completada (Junio 2026) | 48 | ✅ LIBERADA |
| Phase 2 | 1.1 | Q3 2026 | +18 (en paralelo) | 🔄 EN PROGRESO |
| Phase 3 | 1.2 | Q4 2026 | +10 | ⏳ PLANEADO |
| Phase 4 | 1.3 | Q1 2027 | +9 | ⏳ PLANEADO |

---

## MATRIZ DE IMPLEMENTACIÓN POR STACK

### Backend (FastAPI)

| Componente | Funcionalidades | Estado | % |
|---|---|---|---|
| Endpoints API | 50+ | ✅ Completado | 100% |
| Services | 15 | ✅ Completado | 100% |
| Repositories | 12 | ✅ Completado | 100% |
| Models | 16 | ✅ Completado | 100% |
| Migrations | 5 | ✅ Completado | 100% |
| Autenticación JWT | 6 endpoints | ✅ Completado | 100% |
| RBAC Middleware | Completo | ✅ Completado | 100% |
| Celery Tasks | 10+ | 🔄 En Desarrollo | 80% |
| Email Templates | 8 | 🔄 En Desarrollo | 60% |
| Storage (MinIO/FS) | Upload/Download | ✅ Completado | 100% |

### Frontend Portal Externo (React)

| Componente | Funcionalidades | Estado | % |
|---|---|---|---|
| Wizard Radicación | 6 pasos | ✅ Completado | 100% |
| Módulo Consulta | Query pública | ✅ Completado | 100% |
| Home / Layout | Responsivo | ✅ Completado | 100% |
| Validación Zod | Todos los forms | ✅ Completado | 100% |
| API Client (Axios) | Todos los endpoints | ✅ Completado | 100% |
| Error Handling | Global | ✅ Completado | 100% |
| Loading States | Skeleton/Spinner | ✅ Completado | 100% |
| Responsive Design | Mobile + Desktop | ✅ Completado | 100% |

### Frontend Sistema Interno (React)

| Componente | Funcionalidades | Estado | % |
|---|---|---|---|
| Login Screen | - | ⏳ Pendiente | 0% |
| Dashboard | Métricas | ⏳ Pendiente | 0% |
| Listado Incapacidades | Grid + Filtros | ⏳ Pendiente | 0% |
| Panel Auditoría | Detalles + Acciones | ⏳ Pendiente | 0% |
| Panel Aprobación | Órdenes de pago | ⏳ Pendiente | 0% |
| Panel Pago | Ejecución | ⏳ Pendiente | 0% |
| Admin User Mgmt | CRUD usuarios | ⏳ Pendiente | 0% |
| Reportes | Gráficos | ⏳ Pendiente | 0% |

---

## DEPENDENCIAS TÉCNICAS

### Bloqueadores Actuales

| Dependencia | Estado | Impacto | ETA |
|---|---|---|---|
| Autenticación desde Laravel | ✅ Completada | Permite login en el sistema | - |
| Base de datos PostgreSQL | ✅ Setup | Almacenamiento persistente | - |
| MinIO / Filesystem | ✅ Completado | Almacenamiento documentos | - |
| RabbitMQ | ✅ Completado | Cola de tareas | - |
| Redis | ✅ Completado | Cache y sesiones | - |
| Integración correo | 🔄 En Desarrollo | Notificaciones email | Q3 2026 |
| Integración bancaria | ⏳ Pendiente | Reconciliación de pagos | Q4 2026 |
| API externa (Datos empleados) | ⏳ Pendiente | Sincronización masiva | Q3 2026 |

---

## RIESGOS Y MITIGACIÓN

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Retraso en integración email | Media | Alto | Usar servicio tercero (SendGrid, AWS SES) |
| Performance en reportes (muchos datos) | Media | Medio | Implementar vistas materializadas, índices |
| Escalabilidad en concurrencia | Baja | Alto | Usar load balancer, múltiples API instances |
| Pérdida de documentos en MinIO | Baja | Crítico | Backup automático, replicación |

---

## MATRIZ DE DEPENDENCIAS ENTRE FUNCIONALIDADES

```
Autenticación ──→ Radicación
   │                  │
   ├─→ Auditoría ─────┤
   │      │           │
   └──────┼─→ Pago ←──┘
          │
          └─→ Reportes
```

**Ruta crítica**:
1. Autenticación ✅
2. Radicación ✅
3. Auditoría ✅
4. Pago ✅

---

**Último actualizado**: 3 de Junio, 2026

**Responsable**: Equipo de Desarrollo

**Próxima revisión**: Semanal (Sprint Review)
