# Prompt para Iniciar Fase 2 - Sistema Interno

**Fecha**: 16 de enero de 2026  
**Contexto**: Fase 1 Portal Externo completada al 100%  
**Próxima meta**: Implementar Dashboard de Auditoría Interna

---

## 📋 Prompt Estructurado para Fase 2

### CONTEXTO

La **Fase 1 del Portal Externo** está completada al 100%, con un wizard de radicación totalmente funcional (5 pasos) que permite:
- Radicar incapacidades ARL y SALUD
- Upload de documentos a MinIO
- Generación de número de radicación
- 217 tests pasando con >75% de cobertura

Ahora debemos implementar la **Fase 2: Sistema Interno**, que será utilizado por usuarios internos de la aseguradora (auditores, aprobadores, administradores) para gestionar el ciclo completo de las incapacidades radicadas.

---

### OBJETIVO

Implementar el **Sistema de Autenticación JWT completo** como primer módulo de la Fase 2, incluyendo:

1. Página de Login con formulario y validaciones
2. Integración con endpoint `/api/v1/auth/login` del backend
3. Almacenamiento seguro de tokens (access + refresh)
4. Interceptors de Axios para agregar JWT automáticamente
5. Refresh token automático cuando access token expira (401)
6. Guards de rutas para proteger páginas privadas
7. Store de autenticación con Zustand
8. Logout con invalidación de tokens
9. Tests completos (>70% cobertura)

---

### REQUERIMIENTOS ESPECÍFICOS

#### 1. Estructura de Carpetas

Crear nueva estructura para el sistema interno:

```
frontend/sistema-interno/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx          # Formulario de login
│   │   │   └── ProtectedRoute.tsx     # Guard para rutas privadas
│   │   ├── layout/
│   │   │   ├── DashboardLayout.tsx    # Layout del dashboard
│   │   │   ├── Header.tsx             # Header con usuario y logout
│   │   │   └── Sidebar.tsx            # Sidebar con navegación
│   │   └── ui/                        # Reutilizar del portal-externo
│   ├── pages/
│   │   ├── LoginPage.tsx              # Página de login
│   │   └── DashboardPage.tsx          # Página principal (placeholder)
│   ├── services/
│   │   └── authService.ts             # Servicio de autenticación
│   ├── store/
│   │   └── authStore.ts               # Zustand store para auth
│   ├── types/
│   │   └── auth.ts                    # Tipos de auth
│   ├── utils/
│   │   └── token.ts                   # Helpers para JWT
│   └── App.tsx                        # Router con rutas protegidas
```

#### 2. Tipos TypeScript (types/auth.ts)

```typescript
export interface LoginRequest {
  username: string;  // Puede ser email o username
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;  // "bearer"
}

export interface User {
  id: string;
  username: string;
  email: string;
  rol: RolUsuario;
  nombre_completo: string;
  estado: EstadoUsuario;
}

export enum RolUsuario {
  ADMIN = 'ADMIN',
  AUDITOR = 'AUDITOR',
  APROBADOR = 'APROBADOR',
  EMPRESA = 'EMPRESA',
  EMPLEADO = 'EMPLEADO',
  READONLY = 'READONLY',
}

export enum EstadoUsuario {
  ACTIVO = 'ACTIVO',
  INACTIVO = 'INACTIVO',
  BLOQUEADO = 'BLOQUEADO',
}

export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
}
```

#### 3. Zustand Store (store/authStore.ts)

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, TokenResponse, User } from '@/types/auth';

interface AuthStore extends AuthState {
  // Acciones
  login: (tokens: TokenResponse, user: User) => void;
  logout: () => void;
  setAccessToken: (token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Estado inicial
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      // Acciones
      login: (tokens, user) => set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        user,
        isAuthenticated: true,
      }),

      logout: () => set({
        accessToken: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
      }),

      setAccessToken: (token) => set({ accessToken: token }),

      clearAuth: () => set({
        accessToken: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
      }),
    }),
    {
      name: 'auth-storage', // LocalStorage key
      partialize: (state) => ({
        // Solo persistir tokens y user, no isAuthenticated
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
);
```

#### 4. Servicio de Autenticación (services/authService.ts)

```typescript
import api from './api';
import { LoginRequest, TokenResponse, User } from '@/types/auth';

/**
 * Login con username/email y password
 */
export async function login(credentials: LoginRequest): Promise<{ tokens: TokenResponse; user: User }> {
  // Backend espera form-data (OAuth2PasswordRequestForm)
  const formData = new FormData();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  const { data: tokens } = await api.post<TokenResponse>('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

  // Obtener datos del usuario con el token
  const { data: user } = await api.get<User>('/auth/me', {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });

  return { tokens, user };
}

/**
 * Logout - invalida el refresh token en backend
 */
export async function logout(): Promise<void> {
  await api.post('/auth/logout');
}

/**
 * Refresh access token usando refresh token
 */
export async function refreshAccessToken(refreshToken: string): Promise<string> {
  const { data } = await api.post<TokenResponse>(
    '/auth/refresh',
    {},
    {
      headers: { Authorization: `Bearer ${refreshToken}` },
    }
  );

  return data.access_token;
}

/**
 * Obtener datos del usuario actual
 */
export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>('/auth/me');
  return data;
}
```

#### 5. Axios Interceptors (services/api.ts)

**IMPORTANTE**: Actualizar el archivo `api.ts` existente para:
- Agregar access token automáticamente en cada request
- Manejar 401 (token expirado) con refresh automático
- Logout si refresh falla

```typescript
import axios, { InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/store/authStore';
import { refreshAccessToken } from './authService';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8010/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - agregar JWT automáticamente
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { accessToken } = useAuthStore.getState();
    
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - refresh token automático
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si es 401 y no hemos reintentado aún
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const { refreshToken } = useAuthStore.getState();
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Obtener nuevo access token
        const newAccessToken = await refreshAccessToken(refreshToken);
        
        // Actualizar store
        useAuthStore.getState().setAccessToken(newAccessToken);
        
        // Reintentar request original con nuevo token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Si el refresh falla, hacer logout
        useAuthStore.getState().clearAuth();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

#### 6. Componente LoginForm (components/auth/LoginForm.tsx)

Características:
- React Hook Form con Zod validation
- Campos: username (email o username), password
- Estados: loading, error
- Mostrar errores del backend (credenciales inválidas, cuenta bloqueada)
- Redirect a dashboard después de login exitoso
- Recordar credenciales (checkbox opcional)

**Schema de validación**:
```typescript
const loginSchema = z.object({
  username: z.string().min(3, 'Mínimo 3 caracteres').max(50, 'Máximo 50 caracteres'),
  password: z.string().min(6, 'Mínimo 6 caracteres'),
});
```

#### 7. Guard de Rutas (components/auth/ProtectedRoute.tsx)

```typescript
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: RolUsuario[];
}

export function ProtectedRoute({ children, requiredRoles }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Verificar roles si se especifican
  if (requiredRoles && user && !requiredRoles.includes(user.rol)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
}
```

#### 8. Router (App.tsx)

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

---

### CRITERIOS DE ACEPTACIÓN

**Funcionales**:
- [ ] Usuario puede hacer login con username/password
- [ ] Tokens se almacenan en localStorage via Zustand persist
- [ ] Access token se agrega automáticamente a todos los requests
- [ ] Cuando access token expira (401), se ejecuta refresh automático
- [ ] Si refresh falla, se hace logout y redirect a /login
- [ ] Usuario puede hacer logout (invalida tokens en backend)
- [ ] Rutas protegidas redirigen a /login si no autenticado
- [ ] Opcional: Validación de roles para rutas específicas
- [ ] Mostrar errores apropiados (credenciales incorrectas, cuenta bloqueada)

**Técnicos**:
- [ ] 0 errores TypeScript
- [ ] Build exitoso con `npm run build`
- [ ] Tests pasando >70% cobertura
- [ ] Componentes siguiendo convenciones del proyecto
- [ ] Uso de Zustand para estado global de auth
- [ ] Interceptors de Axios configurados correctamente
- [ ] LocalStorage para persistencia de sesión

**Testing**:
- [ ] `LoginForm.test.tsx` - Mínimo 10 tests
  - Renderizado del formulario
  - Validación de campos
  - Submit exitoso
  - Errores del backend
  - Estado de loading
- [ ] `authService.test.ts` - Mínimo 8 tests
  - Login exitoso
  - Login con credenciales inválidas
  - Refresh token exitoso
  - Refresh token inválido
  - Logout
  - getCurrentUser
- [ ] `ProtectedRoute.test.tsx` - Mínimo 5 tests
  - Redirect si no autenticado
  - Render children si autenticado
  - Validación de roles
- [ ] `authStore.test.ts` - Mínimo 6 tests
  - Estado inicial
  - Login action
  - Logout action
  - Persistencia en localStorage

---

### CONSIDERACIONES TÉCNICAS

#### Seguridad
- **NO** almacenar passwords en ningún lugar
- Access token expira en 15 minutos
- Refresh token expira en 7 días
- Tokens se invalidan en logout
- HTTPS obligatorio en producción

#### Backend Endpoints Disponibles
- `POST /api/v1/auth/login` - Form-data (username, password)
- `POST /api/v1/auth/logout` - Invalida refresh token
- `POST /api/v1/auth/refresh` - Bearer token en header
- `GET /api/v1/auth/me` - Datos del usuario actual
- `POST /api/v1/auth/change-password` - Cambiar contraseña

#### Dependencias a Instalar
```bash
npm install zustand
npm install react-router-dom
```

#### Reutilización de Componentes
- Reutilizar `Button`, `Input`, `Card` del portal-externo
- Copiar helpers como `cn()` de `lib/utils.ts`
- Mantener consistencia visual con TailwindCSS

---

### TESTS ESPERADOS

**Total mínimo**: 29 tests

| Archivo | Tests | Cobertura |
|---------|-------|-----------|
| LoginForm.test.tsx | 10 | >80% |
| authService.test.ts | 8 | >85% |
| ProtectedRoute.test.tsx | 5 | >90% |
| authStore.test.ts | 6 | >90% |

---

### EJEMPLO DE USO/SALIDA ESPERADA

#### Flujo de Login Exitoso

1. Usuario accede a `/dashboard` sin autenticación
2. ProtectedRoute detecta `isAuthenticated: false`
3. Redirect automático a `/login`
4. Usuario completa formulario:
   ```
   Username: admin@incapacidades.com
   Password: ********
   ```
5. Click en "Iniciar Sesión"
6. Loading state mientras se llama a `/auth/login`
7. Respuesta exitosa con tokens:
   ```json
   {
     "access_token": "eyJ...",
     "refresh_token": "eyJ...",
     "token_type": "bearer"
   }
   ```
8. Segunda llamada a `/auth/me` para obtener datos del usuario
9. Store actualizado con tokens + user
10. Redirect a `/dashboard`
11. DashboardPage renderiza correctamente

#### Flujo de Refresh Automático

1. Usuario autenticado navega en dashboard
2. Access token expira (15 minutos)
3. Siguiente request devuelve 401
4. Interceptor detecta 401
5. Llama a `/auth/refresh` con refresh token
6. Recibe nuevo access token
7. Actualiza store
8. Reintenta request original exitosamente
9. Usuario no percibe interrupción

#### Flujo de Logout

1. Usuario hace click en botón "Cerrar Sesión"
2. Llamada a `/auth/logout` (invalida refresh token en BD)
3. Store se limpia (`clearAuth()`)
4. LocalStorage se borra
5. Redirect a `/login`

---

### DOCUMENTACIÓN A CREAR

Al finalizar, crear:
- `frontend/sistema-interno/AUTH_COMPLETADO.md` con:
  - Resumen de implementación
  - Componentes creados
  - Flujos de autenticación
  - Tests implementados
  - Próximos pasos (Dashboard)

---

### NOTAS ADICIONALES

- Este es el **módulo base** para todo el sistema interno
- Una vez completado, facilita la implementación de:
  - Dashboard con métricas
  - CRUD de incapacidades
  - Gestión de usuarios
  - Reportes
- Priorizar **seguridad** y **UX fluida** (sin interrupciones por refresh)
- Mantener **consistencia** con el portal externo en estilos

---

**Prompt creado**: 16 de enero de 2026  
**Estado**: Listo para implementación  
**Estimación**: 2-3 días de desarrollo
