# Fase 2: Sistema Interno - Dashboard de Auditoría y Gestión

**Objetivo**: Aplicación web interna con autenticación JWT para auditoría, aprobación y gestión completa de incapacidades.

---

## 📋 Requerimientos Funcionales

### RF-010: Autenticación y Autorización
**Como** usuario del sistema interno  
**Quiero** autenticarme con credenciales seguras  
**Para** acceder a funcionalidades según mi rol

**Criterios de Aceptación**:
- [ ] Login con email/username y contraseña
- [ ] Autenticación JWT con refresh tokens
- [ ] Redirección según rol después del login
- [ ] Logout y revocación de tokens
- [ ] Sesión persistente con refresh automático
- [ ] Bloqueo de cuenta después de 5 intentos fallidos
- [ ] Recuperación de contraseña por email

### RF-011: Dashboard de Auditoría
**Como** auditor  
**Quiero** visualizar incapacidades pendientes de revisión  
**Para** auditarlas eficientemente

**Criterios de Aceptación**:
- [ ] Vista de incapacidades en estado RADICADA
- [ ] Filtros por tipo (ARL/SALUD), fecha, empresa
- [ ] Búsqueda por número, documento, empresa
- [ ] Ordenamiento por fecha, prioridad, días
- [ ] Indicadores visuales de prioridad
- [ ] Contador de incapacidades pendientes
- [ ] Métricas: tiempo promedio de auditoría, SLA

### RF-012: Auditoría de Incapacidad
**Como** auditor  
**Quiero** revisar una incapacidad en detalle  
**Para** aprobarla, rechazarla u observarla

**Criterios de Aceptación**:
- [ ] Visualización completa de datos de incapacidad
- [ ] Descarga y preview de documentos adjuntos
- [ ] Verificación de coherencia de datos
- [ ] Acciones: Aprobar, Rechazar, Observar
- [ ] Campo obligatorio de observaciones al rechazar/observar
- [ ] Historial completo de estados y auditorías
- [ ] Validación de días según diagnóstico CIE-10
- [ ] Sugerencias automáticas de inconsistencias

### RF-013: Gestión de Órdenes de Pago
**Como** usuario con rol ADMIN/APROBADOR  
**Quiero** gestionar órdenes de pago  
**Para** autorizar y registrar pagos de incapacidades aprobadas

**Criterios de Aceptación**:
- [ ] Generación automática desde incapacidad APROBADA
- [ ] Vista de órdenes GENERADA, APROBADA, EN_PROCESO, PAGADA
- [ ] Aprobar orden de pago (solo ADMIN)
- [ ] Registrar pago ejecutado con datos bancarios
- [ ] Anular orden de pago con justificación
- [ ] Exportar órdenes a Excel
- [ ] Integración con sistema bancario (Fase 3)

### RF-014: Gestión de Usuarios
**Como** administrador  
**Quiero** gestionar usuarios del sistema  
**Para** controlar accesos y permisos

**Criterios de Aceptación**:
- [ ] CRUD completo de usuarios
- [ ] Asignación de roles (ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY)
- [ ] Activar/desactivar cuentas
- [ ] Resetear contraseña
- [ ] Ver logs de acceso del usuario
- [ ] Bloquear/desbloquear cuentas manualmente

### RF-015: Gestión de Empresas y Empleados
**Como** usuario ADMIN/EMPRESA  
**Quiero** gestionar empresas y empleados  
**Para** mantener datos actualizados

**Criterios de Aceptación**:
- [ ] CRUD de empresas (razón social, NIT, contacto)
- [ ] CRUD de empleados vinculados a empresas
- [ ] Importación masiva desde CSV/Excel
- [ ] Sincronización con API externa de RRHH
- [ ] Búsqueda y filtros avanzados
- [ ] Estadísticas por empresa (incapacidades, días, montos)

### RF-016: Gestión de Afiliados
**Como** usuario ADMIN  
**Quiero** gestionar afiliados de pólizas de salud  
**Para** validar incapacidades SALUD

**Criterios de Aceptación**:
- [ ] CRUD de afiliados
- [ ] Validación de número de póliza
- [ ] Estado de afiliado (ACTIVO, INACTIVO, SUSPENDIDO)
- [ ] Histórico de incapacidades por afiliado
- [ ] Búsqueda por documento o póliza

### RF-017: Reportes y Exportación
**Como** usuario ADMIN/AUDITOR  
**Quiero** generar reportes personalizados  
**Para** análisis y toma de decisiones

**Criterios de Aceptación**:
- [ ] Reporte de incapacidades por período
- [ ] Reporte de órdenes de pago
- [ ] Reporte de auditoría por auditor
- [ ] Reporte de empresas (top 10 por incapacidades)
- [ ] Exportación a Excel, PDF
- [ ] Filtros avanzados (fecha, tipo, estado, empresa)
- [ ] Gráficas de tendencias

---

## 🎨 Diseño UI/UX

### Layout Principal (Authenticated)

```
┌────────────────────────────────────────────────────────────────┐
│  [LOGO]  Gestión Incapacidades    [Notif] [Avatar ▼]          │
├──────────────┬─────────────────────────────────────────────────┤
│              │                                                 │
│  MENÚ        │  DASHBOARD PRINCIPAL                            │
│              │                                                 │
│  📊 Dashboard│  ┌─────────────┐  ┌─────────────┐              │
│  📋 Incap.   │  │ Pendientes  │  │ En Auditoría│              │
│  💰 Pagos    │  │     24      │  │      18     │              │
│  🏢 Empresas │  └─────────────┘  └─────────────┘              │
│  👥 Afiliados│                                                 │
│  👤 Usuarios │  ┌──────────────────────────────────┐          │
│  📊 Reportes │  │  Incapacidades Recientes         │          │
│  📝 Auditoría│  ├──────────────────────────────────┤          │
│  ⚙️ Config   │  │  INC-001 | Juan Pérez | RADICADA│          │
│              │  │  INC-002 | Ana López  | AUDITORIA│         │
│              │  └──────────────────────────────────┘          │
│              │                                                 │
└──────────────┴─────────────────────────────────────────────────┘
```

### Login Page

```
┌──────────────────────────────────────────────────┐
│                                                  │
│              [LOGO GRANDE]                       │
│                                                  │
│        Sistema Interno de Incapacidades         │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │                                            │ │
│  │  Email: [______________________]          │ │
│  │                                            │ │
│  │  Contraseña: [______________________]     │ │
│  │                                            │ │
│  │  [ ] Recordarme                           │ │
│  │                                            │ │
│  │  [    Iniciar Sesión    ]                 │ │
│  │                                            │ │
│  │  ¿Olvidó su contraseña?                   │ │
│  │                                            │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Dashboard de Auditoría

```
┌──────────────────────────────────────────────────────────────┐
│  Dashboard de Auditoría                     [Filtros ▼]      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Resumen:                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Pendientes  │ │ Hoy         │ │ Venciendo   │           │
│  │     24      │ │      8      │ │      3      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                              │
│  Filtros: [ARL/SALUD ▼] [Fecha ▼] [Empresa ▼] [Buscar...]  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ N° | Fecha | Solicitante | Empresa | Días | Estado | ⚙│ │
│  ├────────────────────────────────────────────────────────┤ │
│  │001│15/01  │ Juan Pérez  │ ABC SA  │  7   │RADICADA│⚙│ │
│  │002│15/01  │ Ana López   │ XYZ SA  │  14  │RADICADA│⚙│ │
│  │003│14/01  │ Carlos Díaz │ DEF SA  │  30  │OBSERVA │⚙│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Anterior] Página 1 de 3 [Siguiente]                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Detalle de Incapacidad (Auditoría)

```
┌──────────────────────────────────────────────────────────────┐
│  ← Volver    Incapacidad INC-SALUD-2026-001234              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [Tabs: Datos Generales | Documentos | Historial]           │
│                                                              │
│  === DATOS GENERALES ===                                     │
│                                                              │
│  Solicitante: Juan Pérez García                             │
│  Documento: CC 1234567890                                    │
│  Email: juan@email.com | Tel: 3001234567                    │
│                                                              │
│  Tipo: SALUD - Enfermedad general                           │
│  Período: 15/01/2026 - 22/01/2026 (7 días)                  │
│  Diagnóstico: J02.9 - Faringitis aguda no especificada      │
│  Descripción: Dolor de garganta intenso...                   │
│                                                              │
│  Médico: Dr. Carlos Ramírez                                  │
│  IPS: Clínica del Norte                                      │
│  EPS: EPS Sura                                               │
│                                                              │
│  Estado actual: RADICADA                                     │
│  Prioridad: NORMAL                                           │
│                                                              │
│  === DOCUMENTOS ADJUNTOS ===                                 │
│  📄 Certificado médico (150KB) [Ver] [Descargar]            │
│  📄 Historia clínica (220KB) [Ver] [Descargar]              │
│                                                              │
│  === VALIDACIONES AUTOMÁTICAS ===                            │
│  ✅ Días coherentes con diagnóstico CIE-10                   │
│  ✅ Documentos obligatorios presentes                        │
│  ⚠️  Fecha de incapacidad hace más de 15 días              │
│                                                              │
│  === ACCIONES DE AUDITORÍA ===                               │
│                                                              │
│  Observaciones: [Textarea - obligatorio si rechaza]          │
│                                                              │
│  [✓ Aprobar] [✗ Rechazar] [⚠ Observar] [Guardar]          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Gestión de Órdenes de Pago

```
┌──────────────────────────────────────────────────────────────┐
│  Órdenes de Pago                      [Nueva Orden +]        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Filtros: [Estado ▼] [Fecha ▼] [Buscar...]                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ N°   │ Incapacidad │ Beneficiario│ Monto  │ Estado  │⚙│ │
│  ├────────────────────────────────────────────────────────┤ │
│  │OP001│ INC-001     │ Juan Pérez  │$350.000│GENERADA │⚙│ │
│  │OP002│ INC-005     │ Ana López   │$700.000│APROBADA │⚙│ │
│  │OP003│ INC-008     │ Carlos Díaz │$450.000│PAGADA   │⚙│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Exportar Excel]                                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Modal: Aprobar Orden de Pago

```
┌──────────────────────────────────────────┐
│  Aprobar Orden de Pago OP-001       [X]  │
├──────────────────────────────────────────┤
│                                          │
│  Incapacidad: INC-SALUD-2026-001234      │
│  Beneficiario: Juan Pérez García         │
│  Documento: CC 1234567890                │
│                                          │
│  Monto a pagar: $350.000                 │
│  Días: 7 días                            │
│                                          │
│  ¿Confirma la aprobación de esta orden? │
│                                          │
│  Observaciones (opcional):               │
│  [_________________________________]     │
│                                          │
│  [Cancelar]  [Aprobar Orden]             │
│                                          │
└──────────────────────────────────────────┘
```

### Gestión de Usuarios

```
┌──────────────────────────────────────────────────────────────┐
│  Gestión de Usuarios                   [Nuevo Usuario +]     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Filtros: [Rol ▼] [Estado ▼] [Buscar...]                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Usuario      │ Email          │ Rol     │ Estado   │⚙│ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ admin        │admin@mail.com  │ ADMIN   │ ACTIVO   │⚙│ │
│  │ auditor1     │aud1@mail.com   │ AUDITOR │ ACTIVO   │⚙│ │
│  │ empresa_abc  │abc@mail.com    │ EMPRESA │ ACTIVO   │⚙│ │
│  │ juan.perez   │juan@mail.com   │ EMPLEADO│ BLOQUEADO│⚙│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitectura de Componentes

### Estructura de Carpetas

```
frontend-sistema-interno/
├── public/
│   ├── logo.svg
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── ui/                    # Shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── table.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── dropdown-menu.tsx
│   │   │   └── ...
│   │   ├── layout/
│   │   │   ├── AppShell.tsx       # Layout principal con sidebar
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Breadcrumbs.tsx
│   │   │   └── Footer.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── ForgotPassword.tsx
│   │   │   ├── ResetPassword.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── dashboard/
│   │   │   ├── StatsCard.tsx
│   │   │   ├── RecentIncapacidades.tsx
│   │   │   ├── ChartIncapacidades.tsx
│   │   │   └── QuickActions.tsx
│   │   ├── incapacidades/
│   │   │   ├── IncapacidadTable.tsx
│   │   │   ├── IncapacidadFilters.tsx
│   │   │   ├── IncapacidadDetail.tsx
│   │   │   ├── AuditoriaForm.tsx
│   │   │   ├── HistorialTimeline.tsx
│   │   │   └── DocumentViewer.tsx
│   │   ├── ordenes-pago/
│   │   │   ├── OrdenPagoTable.tsx
│   │   │   ├── OrdenPagoDetail.tsx
│   │   │   ├── AprobarOrdenModal.tsx
│   │   │   └── RegistrarPagoForm.tsx
│   │   ├── usuarios/
│   │   │   ├── UsuarioTable.tsx
│   │   │   ├── UsuarioForm.tsx
│   │   │   └── RolesBadge.tsx
│   │   ├── empresas/
│   │   │   ├── EmpresaTable.tsx
│   │   │   ├── EmpresaForm.tsx
│   │   │   ├── EmpleadoTable.tsx
│   │   │   └── ImportarCSV.tsx
│   │   ├── reportes/
│   │   │   ├── ReportBuilder.tsx
│   │   │   ├── ReportFilters.tsx
│   │   │   ├── ChartRenderer.tsx
│   │   │   └── ExportButtons.tsx
│   │   └── shared/
│   │       ├── DataTable.tsx       # Tabla genérica reutilizable
│   │       ├── Pagination.tsx
│   │       ├── SearchInput.tsx
│   │       ├── DateRangePicker.tsx
│   │       ├── FilePreview.tsx
│   │       └── NotificationBell.tsx
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── ForgotPasswordPage.tsx
│   │   ├── dashboard/
│   │   │   └── DashboardPage.tsx
│   │   ├── incapacidades/
│   │   │   ├── IncapacidadesListPage.tsx
│   │   │   ├── IncapacidadDetailPage.tsx
│   │   │   └── AuditoriaPage.tsx
│   │   ├── ordenes-pago/
│   │   │   ├── OrdenesPagoListPage.tsx
│   │   │   └── OrdenPagoDetailPage.tsx
│   │   ├── usuarios/
│   │   │   ├── UsuariosListPage.tsx
│   │   │   └── UsuarioDetailPage.tsx
│   │   ├── empresas/
│   │   │   ├── EmpresasListPage.tsx
│   │   │   └── EmpresaDetailPage.tsx
│   │   ├── afiliados/
│   │   │   ├── AfiliadosListPage.tsx
│   │   │   └── AfiliadoDetailPage.tsx
│   │   └── reportes/
│   │       └── ReportesPage.tsx
│   ├── services/
│   │   ├── api.ts                 # Axios con interceptors JWT
│   │   ├── authService.ts
│   │   ├── incapacidadService.ts
│   │   ├── ordenPagoService.ts
│   │   ├── usuarioService.ts
│   │   ├── empresaService.ts
│   │   ├── afiliadoService.ts
│   │   └── reporteService.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── usePermissions.ts
│   │   ├── useIncapacidades.ts
│   │   ├── useOrdenesPago.ts
│   │   ├── useDebounce.ts
│   │   └── usePagination.ts
│   ├── store/                     # Zustand
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── notificationStore.ts
│   ├── schemas/
│   │   ├── authSchema.ts
│   │   ├── auditoriaSchema.ts
│   │   ├── ordenPagoSchema.ts
│   │   └── usuarioSchema.ts
│   ├── types/
│   │   ├── auth.ts
│   │   ├── user.ts
│   │   ├── incapacidad.ts
│   │   ├── ordenPago.ts
│   │   └── api.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   ├── permissions.ts
│   │   ├── constants.ts
│   │   └── exporters.ts          # Excel, PDF
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

---

## 🔐 Autenticación y Autorización

### Flujo de Autenticación

```
1. Usuario ingresa email + password
   ↓
2. POST /api/v1/auth/login
   ↓
3. Backend valida credenciales
   ↓
4. Devuelve: access_token (15 min) + refresh_token (7 días)
   ↓
5. Frontend guarda tokens en httpOnly cookies (ideal)
   o localStorage (alternativa menos segura)
   ↓
6. Guardar info de usuario en Zustand store
   ↓
7. Redireccionar a dashboard según rol
```

### Refresh Token Flow

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true  // Para enviar cookies
});

// Interceptor para agregar token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor para refrescar token
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const { data } = await axios.post('/api/v1/auth/refresh', {
          refresh_token: localStorage.getItem('refresh_token')
        });
        
        localStorage.setItem('access_token', data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        
        return api(originalRequest);
      } catch (refreshError) {
        // Redirigir a login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

### Protected Routes

```typescript
// components/auth/ProtectedRoute.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

interface Props {
  allowedRoles?: string[];
}

export function ProtectedRoute({ allowedRoles }: Props) {
  const { user, isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.rol)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}
```

### RBAC (Role-Based Access Control)

```typescript
// utils/permissions.ts
export enum Permissions {
  // Incapacidades
  INCAPACIDAD_READ = 'incapacidad:read',
  INCAPACIDAD_CREATE = 'incapacidad:create',
  INCAPACIDAD_UPDATE = 'incapacidad:update',
  INCAPACIDAD_AUDIT = 'incapacidad:audit',
  
  // Órdenes de Pago
  ORDEN_PAGO_READ = 'orden_pago:read',
  ORDEN_PAGO_APPROVE = 'orden_pago:approve',
  ORDEN_PAGO_PAY = 'orden_pago:pay',
  
  // Usuarios
  USER_MANAGE = 'user:manage',
  
  // Reportes
  REPORT_GENERATE = 'report:generate',
}

export const ROLE_PERMISSIONS = {
  ADMIN: [
    Permissions.INCAPACIDAD_READ,
    Permissions.INCAPACIDAD_CREATE,
    Permissions.INCAPACIDAD_UPDATE,
    Permissions.INCAPACIDAD_AUDIT,
    Permissions.ORDEN_PAGO_READ,
    Permissions.ORDEN_PAGO_APPROVE,
    Permissions.ORDEN_PAGO_PAY,
    Permissions.USER_MANAGE,
    Permissions.REPORT_GENERATE,
  ],
  AUDITOR: [
    Permissions.INCAPACIDAD_READ,
    Permissions.INCAPACIDAD_AUDIT,
    Permissions.REPORT_GENERATE,
  ],
  APROBADOR: [
    Permissions.INCAPACIDAD_READ,
    Permissions.ORDEN_PAGO_READ,
    Permissions.ORDEN_PAGO_APPROVE,
  ],
  EMPRESA: [
    Permissions.INCAPACIDAD_READ,
    Permissions.INCAPACIDAD_CREATE,
  ],
  READONLY: [
    Permissions.INCAPACIDAD_READ,
    Permissions.ORDEN_PAGO_READ,
  ],
};

// Hook personalizado
export function usePermissions() {
  const { user } = useAuthStore();
  
  const hasPermission = (permission: Permissions) => {
    return ROLE_PERMISSIONS[user.rol]?.includes(permission) ?? false;
  };
  
  return { hasPermission };
}
```

---

## 🔌 Integración con Backend

### Endpoints Principales

```typescript
// Auth
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
POST   /api/v1/auth/change-password
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password

// Incapacidades (con autenticación)
GET    /api/v1/incapacidades           # Lista con filtros
GET    /api/v1/incapacidades/{id}      # Detalle
POST   /api/v1/incapacidades           # Crear (EMPRESA)
PUT    /api/v1/incapacidades/{id}      # Actualizar
DELETE /api/v1/incapacidades/{id}      # Eliminar
POST   /api/v1/incapacidades/{id}/auditar  # Auditar (AUDITOR)
GET    /api/v1/incapacidades/{id}/historial

// Órdenes de Pago
GET    /api/v1/ordenes-pago
GET    /api/v1/ordenes-pago/{id}
POST   /api/v1/ordenes-pago            # Generar desde incapacidad
PUT    /api/v1/ordenes-pago/{id}/aprobar  # Aprobar (ADMIN)
PUT    /api/v1/ordenes-pago/{id}/pagar    # Registrar pago
PUT    /api/v1/ordenes-pago/{id}/anular

// Usuarios
GET    /api/v1/usuarios
GET    /api/v1/usuarios/{id}
POST   /api/v1/usuarios
PUT    /api/v1/usuarios/{id}
DELETE /api/v1/usuarios/{id}
PUT    /api/v1/usuarios/{id}/reset-password

// Empresas
GET    /api/v1/empresas
GET    /api/v1/empresas/{id}
POST   /api/v1/empresas
PUT    /api/v1/empresas/{id}
POST   /api/v1/empresas/import-csv

// Empleados
GET    /api/v1/empleados
GET    /api/v1/empleados/{id}
POST   /api/v1/empleados
PUT    /api/v1/empleados/{id}

// Afiliados
GET    /api/v1/afiliados
GET    /api/v1/afiliados/{id}
POST   /api/v1/afiliados
PUT    /api/v1/afiliados/{id}

// Reportes
POST   /api/v1/reportes/incapacidades
POST   /api/v1/reportes/ordenes-pago
POST   /api/v1/reportes/auditoria
GET    /api/v1/reportes/{id}/export?format=excel|pdf
```

---

## 📊 Dashboard y Métricas

### KPIs Principales

```typescript
interface DashboardMetrics {
  incapacidades: {
    pendientes: number;
    en_auditoria: number;
    aprobadas_hoy: number;
    rechazadas_hoy: number;
    promedio_dias_auditoria: number;
  };
  ordenes_pago: {
    generadas: number;
    aprobadas: number;
    pendientes_pago: number;
    monto_total_mes: number;
  };
  sla: {
    cumplimiento_porcentaje: number;
    vencidas: number;
    proximas_vencer: number;
  };
}
```

### Gráficas

1. **Incapacidades por Estado** (Pie Chart)
2. **Tendencia de Radicaciones** (Line Chart - últimos 30 días)
3. **Top 10 Empresas** (Bar Chart - por cantidad de incapacidades)
4. **Días promedio de auditoría** (Gauge Chart)
5. **Cumplimiento de SLA** (Progress Bar)

---

## 🧪 Testing

### Tests Específicos

```typescript
// tests/auth/LoginForm.test.tsx
describe('LoginForm', () => {
  it('debe mostrar error con credenciales inválidas', async () => {
    render(<LoginForm />);
    
    await userEvent.type(screen.getByLabelText(/email/i), 'wrong@email.com');
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'wrongpass');
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }));
    
    expect(await screen.findByText(/credenciales inválidas/i)).toBeInTheDocument();
  });
  
  it('debe redirigir a dashboard con credenciales válidas', async () => {
    const mockLogin = vi.fn().mockResolvedValue({ user: mockUser, token: 'token' });
    
    render(<LoginForm onLogin={mockLogin} />);
    
    await userEvent.type(screen.getByLabelText(/email/i), 'admin@mail.com');
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }));
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });
});
```

---

## 🚀 Roadmap de Desarrollo (Fase 2)

### Semana 1-2: Autenticación y Layout
- [ ] Setup proyecto Vite + React + TypeScript
- [ ] Configurar TailwindCSS + Shadcn/ui
- [ ] Implementar login con JWT
- [ ] Protected routes con RBAC
- [ ] Layout principal con sidebar
- [ ] Zustand store para auth

### Semana 3-4: Dashboard y Listados
- [ ] Dashboard con métricas
- [ ] Lista de incapacidades con filtros
- [ ] Lista de órdenes de pago
- [ ] Componente DataTable reutilizable
- [ ] Paginación y búsqueda

### Semana 5-6: Auditoría y Órdenes de Pago
- [ ] Detalle de incapacidad
- [ ] Formulario de auditoría (aprobar/rechazar/observar)
- [ ] Gestión de órdenes de pago
- [ ] Preview de documentos
- [ ] Timeline de historial

### Semana 7-8: CRUD Completo
- [ ] Gestión de usuarios
- [ ] Gestión de empresas y empleados
- [ ] Gestión de afiliados
- [ ] Importación CSV
- [ ] Exportación Excel

### Semana 9-10: Reportes y Testing
- [ ] Builder de reportes
- [ ] Gráficas con Recharts
- [ ] Exportación PDF
- [ ] Tests unitarios (>70% coverage)
- [ ] Tests E2E (Playwright)

### Semana 11-12: Pulido y Deploy
- [ ] Optimización de performance
- [ ] Accesibilidad (WCAG 2.1 AA)
- [ ] Responsive design
- [ ] Documentación
- [ ] Deploy a producción

---

## 📦 Dependencias Adicionales

```json
{
  "dependencies": {
    "zustand": "^4.4.0",
    "@tanstack/react-table": "^8.11.0",
    "recharts": "^2.10.0",
    "sonner": "^1.2.0",
    "jspdf": "^2.5.0",
    "xlsx": "^0.18.0",
    "react-dropzone": "^14.2.0"
  }
}
```

---

## 📝 Documentación Relacionada

- [06_FRONTEND_PLAN.md](./06_FRONTEND_PLAN.md) - Plan general de frontend
- [09_COMPONENTES_COMPARTIDOS.md](./09_COMPONENTES_COMPARTIDOS.md) - Library de componentes
- [10_INTEGRACION_BACKEND.md](./10_INTEGRACION_BACKEND.md) - Guía de integración con API
- [03_API_ENDPOINTS.md](./03_API_ENDPOINTS.md) - Documentación completa de endpoints
