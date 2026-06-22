# Estado del Proyecto - Sistema de Gestión de Incapacidades

**Fecha de actualización**: 20 de junio de 2026  
**Versión**: 0.9.0-beta  
**Estado general**: 🔄 En Desarrollo

---

> ## 🔁 ACTUALIZACIÓN 2026-06-20 — Portal Externo refactorizado
>
> **El contenido fechado el 17 de enero (más abajo) describe el antiguo Portal
> Externo público y ya NO refleja la arquitectura actual.** Se conserva como
> registro histórico. El estado vigente es:
>
> - **Portal Externo = portal autenticado solo para empresas (rol `EMPRESA`).**
>   Ya no existe radicación ni consulta pública/anónima. El acceso reutiliza
>   `POST /api/v1/auth/login`; solo usuarios `EMPRESA` con `empresa_id` vinculado
>   pueden entrar (`ProtectedRoute`).
> - **Alcance: solo ARL.** SALUD queda fuera del alcance de este portal.
> - **Radicación individual y masiva** comparten el mismo `RadicacionPipelineService`
>   (individual = masiva con N=1). La radicación crea la `Incapacidad`
>   directamente (sin la antigua pre-incapacidad para este portal).
> - **Radicación masiva**: carga de plantilla Excel + ZIP de soportes, validación
>   por fila (formato y existencia de CIE-10 contra catálogo), creación por lotes.
> - **Job de auditoría** evalúa reglas sobre la `Incapacidad` (no sobre
>   pre-incapacidad) y transiciona `RADICADA → EN_AUDITORIA`.
> - **Consulta**: `GET /api/v1/incapacidades/mi-empresa` (solo `EMPRESA`,
>   `empresa_id` forzado desde el token). El "módulo de consulta pendiente" que
>   se describe abajo **ya está implementado** como consulta autenticada por
>   empresa (Fase 5), no como endpoint público.
> - **Integraciones ServiAlfa / Sicat**: clientes **STUB** (no productivos);
>   `IntegracionService` registra cada intento en `communication_log`.
> - **CIE-10**: formato `^[A-Z]\d{2}[0-9X]$` (estándar colombiano, sin punto) y
>   validación de existencia en catálogo.
> - **UI/UX**: login en pantalla dividida, navbar superior con menú + dropdown de
>   usuario, footer compartido con versión dinámica, layout de radicación
>   individual a 2 columnas.
>
> **Fuente autoritativa del estado actual:**
> [`docs/superpowers/PR-portal-externo-empresa-refactor.md`](./superpowers/PR-portal-externo-empresa-refactor.md)
> y los planes `docs/superpowers/plans/2026-06-19-phase{1..5}-*.md`.

---

## 📊 Resumen Ejecutivo

### Progreso Global: 85% ⚠️

| Componente | Completado | Pendiente | Prioridad |
|------------|------------|-----------|-----------|
| Arquitectura | 100% | - | ✅ |
| Modelo de Datos | 100% | - | ✅ |
| Documentación Backend | 100% | - | ✅ |
| Documentación Frontend | 90% | Consulta | 🔴 |
| Infraestructura | 100% | - | ✅ |
| Modelos SQLAlchemy | 11/11 (100%) | - | ✅ |
| Schemas Pydantic | 11/11 (100%) | - | ✅ |
| Repositories | 11/11 (100%) | - | ✅ |
| Services | 11/11 (100%) | - | ✅ |
| API Endpoints | 66/67 (98%) | 1 endpoint consulta | 🔴 |
| Autenticación JWT | 100% | - | ✅ |
| Sistema Storage MinIO | 100% | - | ✅ |
| Módulo Documentos | 100% | - | ✅ |
| Módulo Órdenes Pago | 100% | - | ✅ |
| Módulo Usuarios | 100% | - | ✅ |
| Tests Backend | 87% | Incrementar a >90% | 🟡 |
| **Frontend - Radicación (individual + masiva)** | **100%** | **-** | **✅** |
| **Frontend - Consulta (autenticada por empresa)** | **100%** | **-** | **✅** |

> ⚠️ La tabla anterior se conserva como referencia histórica del 17-ene. Tras el
> refactor del Portal Externo (ver banner superior), la radicación pública fue
> reemplazada por radicación autenticada individual **y masiva**, y la consulta
> se implementó como consulta autenticada por empresa (`/incapacidades/mi-empresa`),
> no como endpoint público.

### ⚠️ Estado Real de Frontend Fase 1

**Completado** (80%):
- ✅ Wizard de radicación de 5 pasos (217 tests pasando)
- ✅ Integración con backend FastAPI
- ✅ Upload de documentos a MinIO
- ✅ Validaciones con Zod
- ✅ Build exitoso (520 KB bundle)

**Pendiente Crítico** (20%):
- 🔴 **Módulo de Consulta de Incapacidades** (0%)
  - Endpoint backend público
  - Componente de búsqueda
  - Vista detallada
  - Timeline de estados
  - Descarga de documentos
  - Tests (>70% cobertura)

### Hitos Recientes

- ✅ **16 de enero**: Wizard de 5 pasos completado (217 tests)
- ✅ **15 de enero**: Integración frontend-backend 100%
- ✅ **14 de enero**: Sistema JWT con refresh tokens
- ✅ **12 de enero**: Módulo documentos con MinIO operativo
- ⚠️ **17 de enero**: Identificada falta de módulo consulta

---

## ✅ Tareas Completadas

### 1-19. [Mantener listado anterior sin cambios]

### 20. Frontend - Fase 1: Portal Externo (Radicación) ✅
- [x] Setup inicial (Vite + React + TypeScript)
- [x] Configuración TailwindCSS + Shadcn/ui
- [x] Wizard Paso 1: Tipo de incapacidad (6 tests)
- [x] Wizard Paso 2: Datos personales (55 tests)
- [x] Wizard Paso 3: Datos de incapacidad (15 tests)
- [x] Wizard Paso 4: Carga de documentos (86 tests)
- [x] Wizard Paso 5: Resumen y radicación (39 tests)
- [x] Integración completa con backend
- [x] Validaciones con Zod
- [x] React Query para data fetching
- [x] Axios con interceptors
- [x] Tests con Vitest + Testing Library

**Métricas Frontend Radicación**:
- **Tests**: 217/217 (100% passing)
- **Cobertura**: >75%
- **Build**: ✅ Exitoso (520 KB bundle)
- **Lint**: ✅ Sin errores

### 21. Documentación ✅
- [x] README.md principal del proyecto
- [x] backend/README.md con instrucciones
- [x] backend/PUERTOS.md con configuración
- [x] backend/scripts/README.md con guía de seed data
- [x] frontend/portal-externo/README.md
- [x] Documentación de cada paso del wizard
- [x] .github/copilot-instructions.md
- [x] Documentación de arquitectura completa (docs/)
- [x] ESTADO_PROYECTO.md actualizado
- [x] RESUMEN_VISUAL_COMPLETO.md

---

## 🔴 Tareas Pendientes (CRÍTICAS)

### ⚠️ URGENTE: Completar Fase 1 - Frontend Portal Externo (3-4 días)

#### 🔴 Prioridad Máxima: Módulo de Consulta de Incapacidades

**Contexto**: 
El wizard de radicación está 100% completado, pero **falta** la funcionalidad de consulta que es parte esencial del Portal Externo. Sin esta funcionalidad, la Fase 1 está **incompleta** y no se puede considerar un MVP funcional.

#### Subtareas Backend (1 día)

**1.1 Crear Endpoint Público de Consulta**
- [ ] `GET /api/v1/incapacidades/consultar?numero={numero}` - Búsqueda por número radicación
- [ ] `GET /api/v1/incapacidades/consultar?documento={doc}&tipo_documento={tipo}` - Búsqueda por documento
- [ ] Validar que el endpoint NO requiere autenticación (público)
- [ ] Response schema con datos completos:
  ```python
  class ConsultaIncapacidadPublicResponse(BaseModel):
      # Datos básicos
      numero: str
      estado: EstadoIncapacidad
      tipo: TipoIncapacidad
      fecha_inicio: date
      fecha_fin: date
      dias_totales: int
      
      # Datos del solicitante (sin información sensible)
      nombre_completo: str
      tipo_documento: TipoDocumento
      
      # Timeline de estados
      historial_estados: List[HistorialEstadoSimple]
      
      # Documentos descargables (solo nombres, sin URLs sensibles)
      documentos: List[DocumentoSimple]
      
      # Información de contacto
      contacto_soporte: ContactoSoporte
      
      # Fechas
      created_at: datetime
      updated_at: datetime
  ```
- [ ] Implementar paginación para historial
- [ ] Sanitizar respuesta (ocultar datos sensibles)
- [ ] Tests unitarios (8-10 tests)
- [ ] Tests de integración (5 tests)
- [ ] Documentar en Swagger con ejemplos

**1.2 Endpoint de Descarga Pública de Documentos**
- [ ] `GET /api/v1/incapacidades/{numero}/documentos/{doc_id}/download` - Sin auth
- [ ] Validar que el documento pertenece a la incapacidad
- [ ] Generar presigned URL temporal (15 minutos)
- [ ] Rate limiting (máximo 10 descargas por IP por hora)
- [ ] Tests (3 tests)

**Criterios de aceptación backend**:
- Endpoints públicos funcionando sin JWT
- Response sanitizada sin datos sensibles
- Búsqueda por número y documento funcionando
- Tests >80% cobertura
- Documentación Swagger completa
- Rate limiting implementado

---

#### Subtareas Frontend (2-3 días)

**2.1 Routing y Navegación**
- [ ] Crear ruta `/consultar` en React Router
- [ ] Agregar link en homepage
- [ ] Breadcrumbs de navegación
- [ ] Tests de routing (2 tests)

**2.2 Componente de Búsqueda**
- [ ] Crear `src/components/consulta/BusquedaIncapacidad.tsx`
  - Formulario con dos modos de búsqueda:
    - Por número de radicación
    - Por documento + tipo documento
  - Validación con Zod
  - Loading states
  - Manejo de errores (404, 500)
  - Botón de limpiar búsqueda
- [ ] Schema Zod `consultaSchema`:
  ```typescript
  const consultaSchema = z.object({
    modo: z.enum(['numero', 'documento']),
    numero: z.string().optional(),
    documento: z.string().optional(),
    tipo_documento: z.enum(['CEDULA', 'PASAPORTE', 'CEDULA_EXTRANJERIA']).optional(),
  }).refine(
    (data) => {
      if (data.modo === 'numero') return !!data.numero;
      return !!data.documento && !!data.tipo_documento;
    },
    { message: 'Datos incompletos' }
  );
  ```
- [ ] Tests (10 tests):
  - Render inicial
  - Cambio entre modos
  - Validaciones
  - Submit exitoso
  - Error 404
  - Loading states

**2.3 Servicio API**
- [ ] Crear `src/services/consultaService.ts`:
  ```typescript
  export async function consultarIncapacidad(
    params: ConsultaParams
  ): Promise<IncapacidadPublicaResponse> {
    const { data } = await api.get('/incapacidades/consultar', { params });
    return data;
  }
  
  export function useConsultarIncapacidad() {
    return useMutation({
      mutationFn: consultarIncapacidad,
      // ...
    });
  }
  ```
- [ ] Hook React Query con error handling
- [ ] Tests (5 tests)

**2.4 Vista Detallada de Incapacidad**
- [ ] Crear `src/components/consulta/DetalleIncapacidad.tsx`
  - Card con información básica
  - Card con datos del solicitante
  - Timeline de estados visual
  - Lista de documentos descargables
  - Información de contacto
  - Botón de nueva consulta
- [ ] Usar componentes de Shadcn/ui:
  - `Card`
  - `Badge` (para estados)
  - `Timeline` (custom)
  - `Button`
  - `Alert` (para observaciones)
- [ ] Tests (15 tests):
  - Render con datos completos
  - Render con datos mínimos
  - Estados diferentes (RADICADA, APROBADA, etc.)
  - Click en documentos
  - Navegación

**2.5 Timeline de Estados**
- [ ] Crear `src/components/consulta/TimelineEstados.tsx`
  - Componente visual tipo stepper
  - Iconos por estado
  - Fechas de transición
  - Observaciones si existen
  - Responsive
- [ ] Tests (8 tests)

**2.6 Lista de Documentos Descargables**
- [ ] Crear `src/components/consulta/DocumentosDescargables.tsx`
  - Tabla con nombre, tipo, tamaño
  - Botón de descarga con loading
  - Preview de PDF (opcional)
  - Manejo de errores
- [ ] Integrar con endpoint de descarga pública
- [ ] Tests (10 tests)

**2.7 Información de Contacto**
- [ ] Crear `src/components/consulta/ContactoSoporte.tsx`
  - Card con información
  - Email, teléfono, horario
  - FAQs comunes
- [ ] Tests (3 tests)

**2.8 Página de Consulta Principal**
- [ ] Crear `src/pages/ConsultarIncapacidad.tsx`
  - Layout responsive
  - Integración de todos los componentes
  - Estados de búsqueda (inicial, buscando, resultado, error)
  - Breadcrumbs
  - SEO metadata
- [ ] Tests E2E (5 tests):
  - Flujo completo búsqueda exitosa
  - Búsqueda sin resultados
  - Error de servidor
  - Descarga de documento
  - Navegación

**Criterios de aceptación frontend**:
- Búsqueda por número y documento funcionando
- Vista detallada responsive
- Timeline visual completa
- Descarga de documentos funcionando
- Tests >70% cobertura (60+ tests nuevos)
- Build exitoso
- 0 errores TypeScript
- Lighthouse score >90

---

#### Subtareas Documentación (0.5 día)

**3.1 Documentación Técnica**
- [ ] Crear `docs/10_CONSULTA_INCAPACIDADES.md`:
  - Arquitectura del módulo
  - Endpoints backend
  - Componentes frontend
  - Flujos de usuario
  - Casos de error
  - Screenshots
- [ ] Actualizar `frontend/portal-externo/README.md`
- [ ] Crear `frontend/portal-externo/CONSULTA_COMPLETADO.md`

**3.2 Documentación de Usuario**
- [ ] Crear guía de usuario para consulta
- [ ] FAQ con preguntas comunes
- [ ] Troubleshooting

---

### Fase 2: Frontend - Sistema Interno (4-6 semanas) - POSTPONER

**NOTA**: No iniciar hasta completar Fase 1 al 100%

#### 2.1 Autenticación JWT en Frontend (1 semana)
- [ ] Implementar login/logout en React
- [ ] Store de autenticación con Zustand
- [ ] Axios interceptors para refresh token automático
- [ ] Guards de rutas protegidas
- [ ] Manejo de expiración de sesión
- [ ] Tests (>70% cobertura)

#### 2.2 Dashboard de Auditoría (2 semanas)
- [ ] Layout principal con sidebar
- [ ] Dashboard con métricas en tiempo real
- [ ] Gráficos con Recharts
- [ ] Filtros avanzados
- [ ] Paginación optimizada
- [ ] Export a Excel/PDF
- [ ] Tests

[... resto de tareas Fase 2 sin cambios ...]

---

## 📦 Dependencias del Proyecto

[Sin cambios]

---

## 🎯 Próximos Pasos Inmediatos

### Sprint Actual (Esta Semana) - CRÍTICO ⚠️

**Prioridad 1 - Completar Fase 1: Módulo de Consulta** 🔴
1. **Backend** (1 día):
   - Implementar endpoint público de consulta
   - Endpoint de descarga pública
   - Tests completos
   - Documentación Swagger

2. **Frontend** (2-3 días):
   - Componente de búsqueda
   - Vista detallada
   - Timeline de estados
   - Lista de documentos
   - Tests completos (60+ nuevos tests)

3. **Documentación** (0.5 día):
   - Crear docs/10_CONSULTA_INCAPACIDADES.md
   - Actualizar README principal
   - Guía de usuario

**Criterios para considerar Fase 1 completa**:
- ✅ Wizard de radicación funcionando (YA COMPLETADO)
- ⏳ Módulo de consulta funcionando
- ⏳ Tests totales >280 (217 actuales + 60+ consulta)
- ⏳ Build exitoso con consulta incluida
- ⏳ Documentación completa de ambos módulos
- ⏳ Demo funcional end-to-end

**Estimación total**: 3-4 días de desarrollo

---

**Prioridad 2 - Solo después de completar Fase 1**
- Planificación Fase 2 (Sistema Interno)
- Diseño de arquitectura
- Creación de backlog detallado

---

## 🐛 Problemas Conocidos

1. **Fase 1 Frontend Incompleta** (🔴 Crítico)
   - Falta módulo de consulta
   - MVP no funcional sin esta parte
   - Bloquea inicio de Fase 2
   - Prioridad: Máxima
   - Solución: Implementar según plan en este documento

2. **Flower no inicia correctamente** (⚠️ Prioridad Media)
   - Error: `ValueError: not enough values to unpack`
   - Workaround: Usar Celery CLI directamente
   - Fix pendiente: Actualizar versión de Flower

3. **Rate Limiting no implementado** (🟡 Prioridad Media)
   - Endpoints públicos vulnerables a abuso
   - Solución: Implementar rate limiting con slowapi
   - Especialmente crítico para endpoint de consulta

---

## 📝 Notas de Desarrollo

### Estado Real del Proyecto

**Situación Actual**:
El proyecto está en **85% de completitud global**, pero la **Fase 1 está incompleta al 80%**. Aunque el wizard de radicación funciona perfectamente, **falta el módulo de consulta** que es esencial para considerar el Portal Externo como funcional.

**Decisión Crítica**:
**NO INICIAR Fase 2** hasta completar Fase 1 al 100%. Un MVP incompleto genera deuda técnica y confusión.

**Prioridad Absoluta**:
Implementar módulo de consulta en los próximos 3-4 días siguiendo el plan detallado en este documento.

---

**Estado actualizado**: 17 de enero de 2026  
**Próxima revisión**: Al completar módulo de consulta  
**Versión del documento**: 0.9.0

---

```
⚠️  FASE 1 INCOMPLETA - CONSULTA PENDIENTE  ⚠️

  Completado:  ████████████████░░░░  80%
  
  ✅ Radicación: 100%
  ⏳ Consulta:     0%  ← SIGUIENTE TAREA CRÍTICA
  
  Estimación: 3-4 días de desarrollo
```