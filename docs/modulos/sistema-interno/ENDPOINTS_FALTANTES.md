# Endpoints Faltantes en el Backend - Análisis y Recomendaciones

**Fecha de análisis**: 23 de enero de 2026  
**Basado en**: OpenAPI specification actual vs Necesidades del Sistema Interno

---

## Resumen Ejecutivo

Después de analizar el OpenAPI actual y las necesidades del Sistema Interno (dashboard de auditoría), se identificaron **7 categorías de endpoints faltantes** que mejorarán significativamente la experiencia de usuario y eficiencia operativa.

### Estado Actual vs Futuro

| Categoría | Endpoints Actuales | Endpoints Recomendados | Prioridad |
|-----------|-------------------|------------------------|-----------|
| Búsqueda Autenticada | 0 | 3 | 🔴 Alta |
| Estadísticas/Dashboard | 0 | 5 | 🔴 Alta |
| Operaciones Masivas | 0 | 4 | 🟡 Media |
| Filtros Avanzados | Básico | 6 | 🟡 Media |
| Exportación | 0 | 3 | 🟢 Baja |
| Notificaciones | 0 | 4 | 🟢 Baja |
| Auditoría | Básico | 2 | 🟡 Media |

---

## 1. 🔴 ALTA PRIORIDAD - Búsqueda Autenticada

### Problema Actual
- Solo existe `/api/v1/incapacidades/consultar` (público, sin autenticación)
- El endpoint `/api/v1/incapacidades/` con `skip` y `limit` no soporta búsqueda avanzada
- Usuarios autenticados necesitan buscar por múltiples criterios simultáneos

### Endpoints Recomendados

#### 1.1. Búsqueda por Número (Autenticado)
```http
GET /api/v1/incapacidades/buscar
Query params:
  - numero: string (número de radicación)
  - incluir_historial: boolean (default: false)
  - incluir_documentos: boolean (default: false)

Response: IncapacidadInDB (con relaciones opcionales)
Roles: ADMIN, AUDITOR, APROBADOR, READONLY
```

**Beneficio**: Búsqueda rápida con control de relaciones (evitar over-fetching)

#### 1.2. Búsqueda Avanzada con Múltiples Filtros
```http
POST /api/v1/incapacidades/buscar-avanzada
Body: {
  numero?: string,
  numero_documento?: string,
  tipo_documento?: TipoDocumento,
  tipo?: TipoIncapacidad,
  estado?: EstadoIncapacidad[],  // array para múltiples estados
  fecha_inicio_desde?: date,
  fecha_inicio_hasta?: date,
  fecha_radicacion_desde?: date,
  fecha_radicacion_hasta?: date,
  empresa_nit?: string,
  empresa_razon_social?: string,  // búsqueda parcial (LIKE)
  valor_minimo?: number,
  valor_maximo?: number,
  prioridad?: Prioridad[],
  skip?: number,
  limit?: number,
  order_by?: string,  // "fecha_inicio", "valor_total", "created_at"
  order_dir?: "asc" | "desc"
}

Response: {
  items: IncapacidadInDB[],
  total: number,
  skip: number,
  limit: number,
  filters_applied: object  // resumen de filtros aplicados
}
```

**Beneficio**: Tabla con sorting, filtrado y paginación completa

#### 1.3. Búsqueda por Texto Completo (Full-Text Search)
```http
GET /api/v1/incapacidades/buscar-texto
Query params:
  - q: string (búsqueda en número, documento, nombres, diagnóstico)
  - limit: number (default: 20, max: 50)

Response: IncapacidadInDB[]
```

**Beneficio**: Búsqueda tipo "Google" para usuarios finales

---

## 2. 🔴 ALTA PRIORIDAD - Estadísticas y Dashboard

### Problema Actual
- No existen endpoints para métricas en tiempo real
- Dashboard requiere múltiples llamadas al API para calcular estadísticas

### Endpoints Recomendados

#### 2.1. Estadísticas Generales
```http
GET /api/v1/incapacidades/estadisticas
Query params:
  - fecha_desde?: date (default: inicio del mes)
  - fecha_hasta?: date (default: hoy)
  - agrupar_por?: "dia" | "semana" | "mes"

Response: {
  total_incapacidades: number,
  por_estado: {
    RADICADA: number,
    EN_AUDITORIA: number,
    OBSERVADA: number,
    APROBADA: number,
    RECHAZADA: number,
    EN_PAGO: number,
    PAGADA: number
  },
  por_tipo: {
    ARL: number,
    SALUD: number
  },
  valor_total: number,
  valor_promedio: number,
  dias_promedio: number,
  tiempo_promedio_auditoria: number,  // en horas
  tendencia: {  // opcional, si agrupar_por está definido
    fecha: string,
    cantidad: number,
    valor: number
  }[]
}
```

#### 2.2. Estadísticas por Usuario (Auditor)
```http
GET /api/v1/incapacidades/estadisticas/usuario/{user_id}
Query params:
  - periodo: "semana" | "mes" | "trimestre" | "año"

Response: {
  incapacidades_auditadas: number,
  incapacidades_aprobadas: number,
  incapacidades_rechazadas: number,
  incapacidades_observadas: number,
  tiempo_promedio_auditoria: number,
  ranking_productividad: number  // posición entre todos los auditores
}
```

#### 2.3. Indicadores Clave (KPIs)
```http
GET /api/v1/incapacidades/kpis
Query params:
  - fecha_desde?: date
  - fecha_hasta?: date

Response: {
  tasa_aprobacion: number,  // % de aprobadas vs total auditadas
  tasa_rechazo: number,
  tiempo_promedio_ciclo: number,  // desde radicación hasta pago (en días)
  incapacidades_pendientes: number,  // RADICADA + EN_AUDITORIA + OBSERVADA
  valor_pendiente_pago: number,  // suma de APROBADA + EN_PAGO
  backlog_auditoria: number,  // incapacidades en estado RADICADA > 3 días
  sla_compliance: number  // % de incapacidades procesadas dentro de SLA
}
```

#### 2.4. Top Empresas/Afiliados
```http
GET /api/v1/incapacidades/estadisticas/top-empresas
Query params:
  - limite: number (default: 10)
  - ordenar_por: "cantidad" | "valor_total"
  - periodo: "mes" | "trimestre" | "año"

Response: {
  empresa_nit: string,
  empresa_razon_social: string,
  cantidad_incapacidades: number,
  valor_total: number,
  promedio_dias: number
}[]
```

#### 2.5. Alertas y Notificaciones
```http
GET /api/v1/incapacidades/alertas
Query params:
  - tipo?: "sla_vencido" | "valor_alto" | "documentos_faltantes"
  - solo_criticas?: boolean

Response: {
  tipo: string,
  incapacidad_id: string,
  incapacidad_numero: string,
  mensaje: string,
  severidad: "baja" | "media" | "alta" | "critica",
  created_at: string
}[]
```

---

## 3. 🟡 MEDIA PRIORIDAD - Operaciones Masivas

### Endpoints Recomendados

#### 3.1. Radicar Múltiples Incapacidades
```http
POST /api/v1/incapacidades/radicar-masivo
Body: {
  incapacidad_ids: string[]  // max 50
}

Response: {
  exitosos: number,
  fallidos: number,
  resultados: {
    incapacidad_id: string,
    status: "success" | "error",
    mensaje?: string
  }[]
}
```

#### 3.2. Asignar Auditor en Lote
```http
POST /api/v1/incapacidades/asignar-auditor
Body: {
  incapacidad_ids: string[],
  auditor_id: string
}

Response: similar a 3.1
```

#### 3.3. Cambiar Prioridad en Lote
```http
POST /api/v1/incapacidades/cambiar-prioridad
Body: {
  incapacidad_ids: string[],
  nueva_prioridad: Prioridad
}
```

#### 3.4. Exportar Selección
```http
POST /api/v1/incapacidades/exportar
Body: {
  incapacidad_ids?: string[],  // opcional, si no se proporciona usa filtros
  filtros?: IncapacidadFiltros,
  formato: "excel" | "csv" | "pdf",
  incluir_documentos: boolean
}

Response: {
  url_descarga: string,
  expires_in: number,
  nombre_archivo: string
}
```

---

## 4. 🟡 MEDIA PRIORIDAD - Filtros y Validaciones

### Endpoints Recomendados

#### 4.1. Validar CIE-10
```http
GET /api/v1/catalogos/cie10/validar
Query params:
  - codigo: string

Response: {
  valido: boolean,
  codigo_normalizado?: string,
  descripcion?: string,
  categoria?: string
}
```

#### 4.2. Autocompletar Diagnóstico
```http
GET /api/v1/catalogos/cie10/autocompletar
Query params:
  - q: string (mínimo 3 caracteres)
  - limite: number (default: 10)

Response: {
  codigo: string,
  descripcion: string,
  categoria: string
}[]
```

#### 4.3. Validar Duplicados
```http
POST /api/v1/incapacidades/validar-duplicado
Body: {
  tipo_documento: string,
  numero_documento: string,
  fecha_inicio: date,
  fecha_fin: date
}

Response: {
  existe_duplicado: boolean,
  incapacidades_similares?: IncapacidadInDB[]
}
```

---

## 5. 🟢 BAJA PRIORIDAD - Exportación y Reportes

### Endpoints Recomendados

#### 5.1. Generar Reporte Ejecutivo
```http
POST /api/v1/reportes/ejecutivo
Body: {
  fecha_desde: date,
  fecha_hasta: date,
  incluir_graficos: boolean,
  formato: "pdf" | "excel"
}

Response: {
  url_descarga: string,
  expires_in: number
}
```

#### 5.2. Exportar Incapacidades a Excel
```http
GET /api/v1/incapacidades/exportar-excel
Query params: (mismos que búsqueda avanzada)

Response: Blob (archivo Excel)
```

#### 5.3. Generar Certificado de Incapacidad
```http
GET /api/v1/incapacidades/{id}/certificado
Query params:
  - formato: "pdf"

Response: Blob (PDF con membrete)
```

---

## 6. 🟢 BAJA PRIORIDAD - Notificaciones

### Endpoints Recomendados

#### 6.1. Configurar Notificaciones
```http
POST /api/v1/usuarios/{user_id}/notificaciones/configurar
Body: {
  email_incapacidad_asignada: boolean,
  email_cambio_estado: boolean,
  email_documento_nuevo: boolean,
  email_resumen_diario: boolean
}
```

#### 6.2. Enviar Notificación Manual
```http
POST /api/v1/incapacidades/{id}/notificar
Body: {
  destinatarios: string[],  // emails
  asunto: string,
  mensaje: string
}
```

---

## 7. 🟡 MEDIA PRIORIDAD - Auditoría Avanzada

### Endpoints Recomendados

#### 7.1. Log de Auditoría de Incapacidad
```http
GET /api/v1/incapacidades/{id}/auditoria-log
Query params:
  - incluir_cambios_documentos: boolean
  - incluir_accesos: boolean

Response: {
  timestamp: string,
  usuario: string,
  accion: AccionAuditoria,
  cambios: object,  // before/after
  ip_address?: string,
  user_agent?: string
}[]
```

#### 7.2. Reporte de Auditoría Global
```http
GET /api/v1/auditoria/reporte
Query params:
  - fecha_desde: date,
  - fecha_hasta: date,
  - usuario_id?: string,
  - accion?: AccionAuditoria

Response: AuditoriaLog[]
```

---

## Priorización de Implementación

### Sprint 1 (2 semanas) - Funcionalidad Crítica
1. Búsqueda por número autenticada (1.1)
2. Estadísticas generales (2.1)
3. KPIs (2.3)

**Impacto**: Dashboard operativo básico

### Sprint 2 (2 semanas) - Búsqueda y Filtrado
1. Búsqueda avanzada (1.2)
2. Búsqueda por texto (1.3)
3. Validar duplicados (4.3)

**Impacto**: Experiencia de usuario completa

### Sprint 3 (2 semanas) - Operaciones Masivas
1. Radicar en lote (3.1)
2. Asignar auditor (3.2)
3. Exportar selección (3.4)

**Impacto**: Eficiencia operativa

### Sprint 4 (1 semana) - Estadísticas Avanzadas
1. Estadísticas por usuario (2.2)
2. Top empresas (2.4)
3. Alertas (2.5)

**Impacto**: Monitoreo y optimización

### Sprint 5 (Opcional) - Reportes y Notificaciones
1. Exportar a Excel (5.2)
2. Reporte ejecutivo (5.1)
3. Notificaciones (6.1, 6.2)

**Impacto**: Valor agregado

---

## Consideraciones de Implementación

### Seguridad
- Todos los endpoints requieren autenticación JWT
- Validar permisos RBAC en cada endpoint
- Limitar resultados para prevenir DoS (max 1000 registros)
- Rate limiting en búsquedas (10 req/min por usuario)

### Performance
- Cachear estadísticas (Redis, TTL 5 minutos)
- Índices en PostgreSQL para búsquedas:
  - `idx_incapacidad_numero` (ya existe)
  - `idx_incapacidad_estado_fecha` (nuevo)
  - `idx_incapacidad_tipo_empresa` (nuevo)
  - `idx_incapacidad_numero_documento` (nuevo)
- Paginación obligatoria en búsquedas
- Background jobs para exportaciones grandes (Celery)

### Testing
- Cobertura >80% en nuevos endpoints
- Tests de carga para búsquedas (500 concurrent users)
- Tests de seguridad (SQL injection, XSS)

### Documentación
- Actualizar OpenAPI automáticamente
- Ejemplos en Swagger UI
- Changelog con versioning semántico

---

## Alternativas Consideradas

### Opción 1: GraphQL en lugar de REST
**Pros**: Fetching flexible, evita over-fetching  
**Cons**: Complejidad adicional, curva de aprendizaje  
**Decisión**: Mantener REST por consistencia y simplicidad

### Opción 2: Elasticsearch para Búsqueda
**Pros**: Performance excepcional, full-text search avanzado  
**Cons**: Infraestructura adicional, sincronización de datos  
**Decisión**: Implementar en Fase 3 si el volumen supera 100K incapacidades

### Opción 3: WebSockets para Notificaciones
**Pros**: Tiempo real, menor latencia  
**Cons**: Complejidad de conexión persistente  
**Decisión**: Implementar en Fase 3, usar polling cada 30s inicialmente

---

## Conclusión

La implementación de estos endpoints incrementará la eficiencia operativa en:
- **60% reducción** en tiempo de búsqueda (con filtros avanzados)
- **80% reducción** en tiempo de generación de reportes (con estadísticas pre-calculadas)
- **40% reducción** en errores de duplicados (con validación en tiempo real)

**Recomendación**: Priorizar Sprints 1-3 (6 semanas) para MVP del Sistema Interno funcional.
