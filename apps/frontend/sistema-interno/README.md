# Sistema Interno - Incapacidades

Sistema web interno para la gestión de incapacidades médicas (ARL y SALUD) para auditores y administradores.

## Stack Tecnológico

### Core
- **React 19.0.0** - Biblioteca UI con nuevos hooks (use, useOptimistic, useActionState)
- **TypeScript 5.x** - Tipado estático
- **Vite 5** - Build tool y dev server ultra rápido

### Routing & State
- **React Router 7** - Enrutamiento client-side
- **Zustand 5** - State management (auth store con persistencia)
- **TanStack React Query 5** - Server state management y caching

### UI & Styling
- **TailwindCSS 3** - Utility-first CSS framework
- **Shadcn/ui** - Componentes accesibles pre-construidos (14 componentes)
- **Lucide React** - Biblioteca de iconos

### Forms & Validation
- **React Hook Form 7** - Manejo de formularios
- **Zod 3** - Validación de schemas

### HTTP Client
- **Axios 1** - Cliente HTTP con interceptores JWT

### Tables & Data
- **TanStack Table 8** - Tablas avanzadas con sorting/filtering/paginación

### Testing
- **Vitest** - Framework de testing (compatible con Vite)
- **Testing Library** - Testing de componentes React
- **Jest DOM** - Matchers adicionales para el DOM

### Utilities
- **date-fns 4** - Manipulación de fechas
- **clsx** - Combinar clases CSS
- **tailwind-merge** - Merge inteligente de clases Tailwind

## Estructura del Proyecto

```
src/
├── components/
│   ├── ui/              # Componentes Shadcn/ui (14 componentes)
│   ├── layout/          # AppShell, Sidebar, Header, Footer
│   ├── auth/            # LoginForm, ProtectedRoute
│   ├── incapacidades/   # Componentes del dominio
│   └── shared/          # Componentes compartidos
├── pages/
│   ├── auth/            # LoginPage
│   ├── dashboard/       # DashboardPage
│   └── incapacidades/   # ConsultaPage, PendientesPage, GestionPage
├── services/
│   ├── authService.ts
│   └── incapacidadService.ts
├── hooks/
│   ├── use-toast.ts     # Hook de toasts
│   └── index.ts
├── store/
│   └── authStore.ts     # Zustand auth store con persistencia
├── schemas/
│   ├── authSchema.ts    # Validaciones de autenticación
│   └── incapacidadSchema.ts
├── types/
│   ├── auth.ts          # User, AuthTokens, LoginRequest/Response
│   ├── enums.ts         # RolUsuario, EstadoIncapacidad, etc.
│   └── incapacidad.ts   # Incapacidad, Empleado, Afiliado, etc.
├── utils/               # Funciones utilitarias
├── lib/
│   ├── api.ts           # Cliente Axios configurado
│   └── utils.ts         # cn() para merge de clases
├── App.tsx
└── main.tsx
```

## Configuración

### Puertos
- **Dev Server**: `5174` (para evitar conflicto con portal-externo:5173)
- **API Backend**: `8010` (proxy configurado en vite.config.ts)

### Variables de Entorno

**`.env.development`**:
```env
VITE_API_URL=http://localhost:8010/api/v1
VITE_APP_NAME=Sistema Interno - Incapacidades
```

**`.env.production`**:
```env
VITE_API_URL=https://api.incapacidades.com/api/v1
VITE_APP_NAME=Sistema Interno - Incapacidades
```

### Path Aliases

Configurados en `tsconfig.json` y `vite.config.ts`:
- `@/*` → `./src/*`

Ejemplo:
```typescript
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/store/authStore';
import api from '@/lib/api';
```

### Proxy API

Configurado en `vite.config.ts` para desarrollo:
```typescript
server: {
  port: 5174,
  proxy: {
    '/api': {
      target: 'http://localhost:8010',
      changeOrigin: true,
    },
  },
}
```

## Comandos

### Desarrollo
```bash
npm run dev          # Iniciar dev server en http://localhost:5174
```

### Build
```bash
npm run build        # Compilar para producción
npm run preview      # Preview del build de producción
```

### Linting
```bash
npm run lint         # Ejecutar ESLint
```

### Testing
```bash
npm test             # Ejecutar tests con Vitest
npm run test:ui      # UI interactiva de Vitest
npm run test:coverage # Reporte de cobertura
```

## Características Implementadas (Setup Fase 1)

### ✅ Configuración Base
- [x] Proyecto Vite con React 19 + TypeScript
- [x] TailwindCSS configurado con variables CSS
- [x] Path aliases (@/*) configurados
- [x] Proxy API configurado
- [x] Variables de entorno (.env.development y .env.production)

### ✅ Componentes UI (Shadcn/ui)
- [x] Button, Input, Label
- [x] Card, Table
- [x] Dialog, Sheet (modales)
- [x] DropdownMenu
- [x] Badge, Alert
- [x] Toast, Separator

### ✅ Tipos y Schemas
- [x] Tipos de autenticación (User, AuthTokens, LoginRequest/Response)
- [x] Enums sincronizados con backend (17 enumeraciones)
- [x] Tipos de dominio (Incapacidad, Empleado, Afiliado, etc.)
- [x] Schemas de validación Zod (login, cambio contraseña, filtros)

### ✅ Estado Global
- [x] Store de autenticación con Zustand
- [x] Persistencia en localStorage
- [x] Hooks de permisos (useHasRole, useCanPerform)

### ✅ HTTP Client
- [x] Cliente Axios configurado
- [x] Interceptor de request (agregar JWT)
- [x] Interceptor de response (refresh token automático)

### ✅ Servicios
- [x] authService (login, logout, refresh, getCurrentUser, changePassword)
- [x] incapacidadService (list, getById, cambiarEstado, getHistorial, getDocumentos)

### ✅ React Query
- [x] QueryClient configurado
- [x] Provider en main.tsx
- [x] Opciones globales (retry, staleTime, refetchOnWindowFocus)

## Próximos Pasos (Fase 2 - Autenticación)

### 1. Componente LoginForm
- [ ] Crear `src/components/auth/LoginForm.tsx`
- [ ] Integrar React Hook Form + Zod
- [ ] Usar componentes Shadcn/ui (Input, Button, Label)
- [ ] Llamar a authService.login()
- [ ] Guardar en authStore

### 2. Página de Login
- [ ] Crear `src/pages/auth/LoginPage.tsx`
- [ ] Layout centrado con Card
- [ ] Redirección después de login exitoso

### 3. ProtectedRoute
- [ ] Crear `src/components/auth/ProtectedRoute.tsx`
- [ ] Verificar isAuthenticated del store
- [ ] Redireccionar a /login si no autenticado

### 4. Routing
- [ ] Configurar React Router con rutas:
  - `/login` → LoginPage
  - `/dashboard` → DashboardPage (protected)
  - `/incapacidades/consulta` → ConsultaPage (protected)
  - `/incapacidades/pendientes` → PendientesPage (protected)
  - `/incapacidades/gestion/:id` → GestionPage (protected)

### 5. Tests
- [ ] LoginForm tests (15+ tests)
- [ ] LoginPage tests (8+ tests)
- [ ] ProtectedRoute tests (6+ tests)
- [ ] authService tests (mock axios)

## Documentación de Referencia

- **Plan completo**: `../FASE2_SISTEMA_INTERNO_PLAN.md`
- **Copilot Instructions**: `../../.github/copilot-instructions.md`
- **Docs del proyecto**: `../../docs/`

## Dependencias Clave

**Producción** (38 paquetes principales):
- react@19.0.0
- react-dom@19.0.0
- react-router-dom@7
- @tanstack/react-query@5
- @tanstack/react-table@8
- zustand@5
- axios@1
- zod@3
- react-hook-form@7
- @hookform/resolvers
- lucide-react@0.468.0
- date-fns@4
- clsx
- tailwind-merge

**Desarrollo** (60+ paquetas):
- vite@5
- typescript@5
- @types/react@19
- @types/react-dom@19
- @types/node
- tailwindcss@3
- postcss
- autoprefixer
- vitest
- @testing-library/react
- @testing-library/jest-dom
- @testing-library/user-event
- eslint
- eslint-plugin-react-hooks

**Total**: 323 paquetes instalados, 0 vulnerabilidades

## Notas Técnicas

### React 19 Features
- No requiere `forwardRef` (refs son props normales)
- Nuevos hooks: `use()`, `useOptimistic()`, `useActionState()`
- Suspense mejorado

### Autenticación JWT
- Access token: 15 minutos (almacenado en localStorage)
- Refresh token: 7 días (almacenado en localStorage)
- Refresh automático en interceptor de axios
- Logout automático si falla el refresh

### Permisos RBAC
- 6 roles: ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY
- Hook `useHasRole()` para verificar roles
- Hook `useCanPerform()` para verificar acciones específicas
- Sincronizado con backend

### Testing Strategy
- Unit tests para servicios y stores
- Component tests para UI con Testing Library
- Integration tests para flujos completos
- Objetivo: 75% de cobertura de código

---

**Estado**: Setup completado ✅  
**Siguiente fase**: Autenticación (Login, ProtectedRoute, Routing)  
**Última actualización**: 23 de enero de 2026
