# PROMPT SUGERIDO PARA EL SIGUIENTE PASO

## Contexto Actual

Has completado exitosamente la **corrección de servicios del Sistema Interno** basándote en el archivo OpenAPI del backend. Los servicios `authService.ts` e `incapacidadService.ts` ahora están alineados con los endpoints reales implementados.

**Estado del proyecto**:
- ✅ Setup del proyecto (Vite + React 19 + TypeScript)
- ✅ Configuración completa (Vite, TailwindCSS, Shadcn/ui)
- ✅ Tipos TypeScript (auth, enums, incapacidad) - CORREGIDOS
- ✅ Schemas de validación (Zod)
- ✅ Zustand auth store
- ✅ Axios client con JWT interceptors
- ✅ Servicios (authService, incapacidadService) - **CORREGIDOS Y VALIDADOS**
- ✅ Documentación actualizada (04_API_ENDPOINTS.md)
- ✅ Análisis de endpoints faltantes (ENDPOINTS_FALTANTES.md)

**Siguiente paso lógico**: Implementar el sistema de autenticación (LoginForm, LoginPage, ProtectedRoute) para permitir el acceso al Sistema Interno.

---

## Objetivo

Implementar el **Sistema de Autenticación Completo** para el Sistema Interno, incluyendo:
1. Componente LoginForm con validación Zod
2. Página LoginPage con diseño profesional
3. ProtectedRoute para rutas autenticadas
4. Configuración de React Router v6
5. Integración con authService y Zustand store
6. Manejo de errores y mensajes de usuario
7. Tests unitarios con Vitest

---

## Requerimientos Específicos

### 1. LoginForm Component

**Ubicación**: `src/components/auth/LoginForm.tsx`

**Funcionalidad**:
- ✅ Usar React Hook Form con Zod resolver
- ✅ Validación de email y contraseña
- ✅ Mostrar errores inline por campo
- ✅ Botón de submit con estado de loading
- ✅ Link "Olvidé mi contraseña" (placeholder)
- ✅ Integrar con `authService.login()`
- ✅ Actualizar Zustand store al login exitoso
- ✅ Redireccionar a `/dashboard` después del login
- ✅ Mostrar toast de error en caso de fallo

**Schema de Validación**:
```typescript
// src/schemas/loginSchema.ts
import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string()
    .email('Email inválido')
    .min(1, 'El email es requerido'),
  password: z.string()
    .min(6, 'La contraseña debe tener al menos 6 caracteres')
    .min(1, 'La contraseña es requerida'),
});

export type LoginFormData = z.infer<typeof loginSchema>;
```

**UI/UX**:
- Card con shadow y border
- Logo de la empresa en la parte superior
- Inputs con iconos (Mail, Lock)
- Botón primario con spinner cuando loading
- Mensaje de error general si las credenciales son incorrectas
- Responsive (mobile-first)

---

### 2. LoginPage Component

**Ubicación**: `src/pages/auth/LoginPage.tsx`

**Funcionalidad**:
- ✅ Layout centrado verticalmente y horizontalmente
- ✅ Background gradient o imagen corporativa
- ✅ LoginForm centrado con max-width 400px
- ✅ Footer con "© 2026 Sistema de Incapacidades"
- ✅ Redirección automática a `/dashboard` si ya está autenticado (useEffect con navigate)

**Estructura**:
```tsx
<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
  <div className="w-full max-w-md px-4">
    <Card>
      <CardHeader>
        <img src="/logo.svg" alt="Logo" className="h-12 mx-auto mb-4" />
        <CardTitle>Iniciar Sesión</CardTitle>
        <CardDescription>Sistema Interno de Gestión de Incapacidades</CardDescription>
      </CardHeader>
      <CardContent>
        <LoginForm />
      </CardContent>
    </Card>
    <footer className="text-center text-sm text-gray-600 mt-8">
      © 2026 Sistema de Incapacidades. Todos los derechos reservados.
    </footer>
  </div>
</div>
```

---

### 3. ProtectedRoute Component

**Ubicación**: `src/components/auth/ProtectedRoute.tsx`

**Funcionalidad**:
- ✅ Verificar si el usuario está autenticado (Zustand store)
- ✅ Si no está autenticado, redireccionar a `/login`
- ✅ Si está autenticado, renderizar `<Outlet />` (React Router)
- ✅ Opcional: Verificar permisos RBAC si se pasa prop `requiredPermissions`
- ✅ Mostrar loading spinner mientras verifica autenticación

**Implementación**:
```tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  requiredPermissions?: string[];
}

export function ProtectedRoute({ requiredPermissions }: ProtectedRouteProps) {
  const { accessToken, user } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Verificar token válido
    if (accessToken) {
      // Opcional: Validar token no expirado
      setIsLoading(false);
    } else {
      setIsLoading(false);
    }
  }, [accessToken]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  // Verificar permisos RBAC (opcional)
  if (requiredPermissions && user) {
    const hasPermission = requiredPermissions.every(permission =>
      user.permisos?.includes(permission)
    );
    
    if (!hasPermission) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return <Outlet />;
}
```

---

### 4. React Router Configuration

**Ubicación**: `src/router/index.tsx`

**Rutas**:
```tsx
import { createBrowserRouter } from 'react-router-dom';
import LoginPage from '@/pages/auth/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import IncapacidadesPage from '@/pages/incapacidades/IncapacidadesPage';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'incapacidades',
        element: <IncapacidadesPage />,
      },
      // Agregar más rutas aquí
    ],
  },
  {
    path: '/unauthorized',
    element: <UnauthorizedPage />,
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
```

**Actualizar `src/main.tsx`**:
```tsx
import { RouterProvider } from 'react-router-dom';
import { router } from './router';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster />
    </QueryClientProvider>
  </React.StrictMode>
);
```

---

### 5. Integración con authService y Zustand

**En LoginForm**:
```tsx
import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import { toast } from '@/components/ui/use-toast';

export function LoginForm() {
  const navigate = useNavigate();
  const { login: setAuthState } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      const response = await authService.login(data);
      
      // Actualizar Zustand store
      setAuthState(
        { 
          access_token: response.access_token, 
          refresh_token: response.refresh_token 
        },
        response.user
      );

      toast({
        title: 'Bienvenido',
        description: `Sesión iniciada como ${response.user.nombres}`,
      });

      navigate('/dashboard');
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Error de autenticación',
        description: error.response?.data?.detail || 'Credenciales incorrectas',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return <form onSubmit={form.handleSubmit(onSubmit)}>...</form>;
}
```

---

### 6. Manejo de Errores

**Errores del Backend**:
- `401 Unauthorized`: Credenciales incorrectas
- `403 Forbidden`: Cuenta bloqueada
- `422 Validation Error`: Formato de datos inválido
- `500 Server Error`: Error del servidor

**Mensajes de Usuario**:
```typescript
const errorMessages: Record<number, string> = {
  401: 'Email o contraseña incorrectos',
  403: 'Tu cuenta ha sido bloqueada. Contacta al administrador.',
  422: 'Por favor verifica los datos ingresados',
  500: 'Error del servidor. Intenta nuevamente más tarde.',
};

const message = errorMessages[error.response?.status] || 'Error desconocido';
```

---

### 7. Tests Unitarios

**Ubicación**: `src/components/auth/__tests__/LoginForm.test.tsx`

**Tests a implementar**:
```typescript
describe('LoginForm', () => {
  it('should render login form with email and password fields', () => {});
  it('should show validation errors when fields are empty', () => {});
  it('should show error when email is invalid', () => {});
  it('should show error when password is too short', () => {});
  it('should call authService.login on submit', () => {});
  it('should navigate to dashboard on successful login', () => {});
  it('should show toast error on failed login', () => {});
  it('should disable submit button while loading', () => {});
});
```

**Cobertura esperada**: >80%

---

## Criterios de Aceptación

- [ ] LoginForm se renderiza correctamente con todos los campos
- [ ] Validación de Zod funciona en tiempo real
- [ ] Login exitoso actualiza Zustand store
- [ ] Login exitoso redirecciona a `/dashboard`
- [ ] Login fallido muestra toast de error con mensaje apropiado
- [ ] ProtectedRoute bloquea acceso sin autenticación
- [ ] ProtectedRoute redirecciona a `/login` si no hay token
- [ ] React Router configurado con rutas principales
- [ ] Tests pasan con >80% de cobertura
- [ ] No hay errores de TypeScript
- [ ] No hay warnings en consola
- [ ] Diseño responsive (mobile, tablet, desktop)

---

## Consideraciones Técnicas

### Seguridad
- **Nunca almacenar contraseñas** en localStorage o sessionStorage
- Tokens JWT almacenados en Zustand (persisted con `zustand/middleware/persist`)
- Refresh token automático con interceptor de Axios
- Logout limpia todos los tokens del store

### Performance
- Lazy loading de rutas con `React.lazy()`
- Debounce en validaciones de formulario (opcional)
- Optimistic updates en Zustand store

### UX
- Transiciones suaves entre páginas
- Feedback visual inmediato (loading spinners, toasts)
- Mensajes de error claros y accionables
- Autocompletado de browser habilitado en inputs

---

## Ejemplo de Uso/Salida Esperada

### Flujo de Usuario

1. **Usuario accede a `/dashboard` sin estar autenticado**:
   ```
   [ProtectedRoute] → Verifica accessToken
   [ProtectedRoute] → No hay token
   [ProtectedRoute] → <Navigate to="/login" replace />
   ```

2. **Usuario llena LoginForm y hace submit**:
   ```
   [LoginForm] → Validar con Zod ✅
   [LoginForm] → authService.login({ username, password })
   [authService] → POST /api/v1/auth/login
   [Backend] → 200 OK { access_token, refresh_token, user }
   [LoginForm] → useAuthStore().login(tokens, user)
   [Zustand] → Actualizar state + localStorage
   [LoginForm] → navigate('/dashboard')
   [ProtectedRoute] → Verificar accessToken ✅
   [ProtectedRoute] → <Outlet /> (renderiza DashboardPage)
   ```

3. **Usuario cierra sesión**:
   ```
   [Header] → onClick logout button
   [authService] → logout(refreshToken)
   [Backend] → 204 No Content (token revocado)
   [Zustand] → useAuthStore().logout()
   [Zustand] → Limpiar state + localStorage
   [App] → navigate('/login')
   ```

---

## Archivos a Crear/Modificar

### Crear
1. `src/schemas/loginSchema.ts`
2. `src/components/auth/LoginForm.tsx`
3. `src/pages/auth/LoginPage.tsx`
4. `src/components/auth/ProtectedRoute.tsx`
5. `src/router/index.tsx`
6. `src/pages/DashboardPage.tsx` (placeholder)
7. `src/pages/UnauthorizedPage.tsx`
8. `src/pages/NotFoundPage.tsx`
9. `src/components/auth/__tests__/LoginForm.test.tsx`
10. `src/components/auth/__tests__/ProtectedRoute.test.tsx`

### Modificar
1. `src/main.tsx` (agregar RouterProvider)
2. `src/App.tsx` (limpiar, ya no se usará)

---

## Dependencias Adicionales

**Ya instaladas** (verificar):
- `react-router-dom` ✅
- `react-hook-form` ✅
- `@hookform/resolvers` ✅
- `zod` ✅
- `lucide-react` ✅ (para iconos)

**Si falta alguna**:
```bash
npm install react-router-dom@6 @hookform/resolvers zod lucide-react
```

---

## Prompt para GitHub Copilot

```
Implementar sistema de autenticación completo para el Sistema Interno basándote en este plan:

1. Crear LoginForm component con React Hook Form + Zod validation
2. Crear LoginPage con diseño profesional usando Shadcn/ui
3. Crear ProtectedRoute component para proteger rutas autenticadas
4. Configurar React Router v6 con rutas principales (login, dashboard, incapacidades)
5. Integrar con authService (ya corregido según OpenAPI)
6. Actualizar Zustand authStore al login exitoso
7. Implementar manejo de errores con toasts
8. Crear tests unitarios con Vitest (>80% cobertura)

Requisitos:
- Login exitoso debe redireccionar a /dashboard
- Login fallido debe mostrar toast de error
- ProtectedRoute debe bloquear acceso sin token
- Diseño responsive con TailwindCSS
- Validación en tiempo real con Zod
- TypeScript estricto (no any's)

Archivos base:
- authService: /src/services/authService.ts (YA CORREGIDO)
- authStore: /src/store/authStore.ts
- API client: /src/lib/api.ts (con interceptors JWT)

Seguir estructura del archivo FASE2_SISTEMA_INTERNO_PLAN.md (Sección 2: Autenticación)
```

---

## Tiempo Estimado

- **LoginForm + LoginPage**: 3-4 horas
- **ProtectedRoute**: 1-2 horas
- **React Router Config**: 1 hora
- **Tests**: 2-3 horas
- **Debugging + Refinamiento**: 2 horas

**Total**: 9-12 horas (1.5 días de desarrollo)

---

## Recursos de Referencia

- **React Router v6 Docs**: https://reactrouter.com/en/main
- **React Hook Form Docs**: https://react-hook-form.com/
- **Zod Docs**: https://zod.dev/
- **Shadcn/ui Components**: https://ui.shadcn.com/
- **OpenAPI Spec**: `/opt/apps/incapacidades_vs/docs/openapi.json`
- **Correcciones Previas**: `frontend/sistema-interno/RESUMEN_CORRECCIONES.md`

---

**Fin del Prompt**
