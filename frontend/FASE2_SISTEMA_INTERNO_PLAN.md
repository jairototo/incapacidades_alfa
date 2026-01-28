# Plan de Desarrollo - Fase 2: Sistema Interno

**Fecha de inicio**: 23 de enero de 2026  
**Objetivo**: Dashboard de auditoría y gestión completa de incapacidades  
**Duración estimada**: 4-6 semanas  
**Stack**: React 19.2 + TypeScript 5.3 + Vite 5 + TailwindCSS + Zustand

---

## 📋 Tabla de Contenidos

1. [Setup Inicial del Proyecto](#1-setup-inicial-del-proyecto)
2. [Sistema de Autenticación](#2-sistema-de-autenticación)
3. [Layout Principal](#3-layout-principal)
4. [Módulo Incapacidades - Consulta](#4-módulo-incapacidades---consulta)
5. [Módulo Incapacidades - Pendientes](#5-módulo-incapacidades---pendientes)
6. [Gestión de Incapacidad](#6-gestión-de-incapacidad)
7. [Testing y Calidad](#7-testing-y-calidad)

---

## 1. Setup Inicial del Proyecto

### 1.1 Crear Estructura del Proyecto

**Ubicación**: `/opt/apps/incapacidades_vs/frontend/sistema-interno/`

**Comandos de Inicialización**:
```bash
# Desde /opt/apps/incapacidades_vs/frontend
npm create vite@latest sistema-interno -- --template react-ts

cd sistema-interno

# Instalar dependencias core
npm install react@19.2.0 react-dom@19.2.0
npm install react-router-dom@6
npm install @tanstack/react-query@5
npm install zustand@4
npm install axios@1
npm install zod@3
npm install react-hook-form@7
npm install @hookform/resolvers

# Instalar TailwindCSS + Shadcn/ui
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p

# Shadcn/ui setup
npx shadcn-ui@latest init
# Seleccionar:
# - Style: Default
# - Base color: Slate
# - CSS variables: Yes

# Instalar componentes Shadcn/ui necesarios
npx shadcn-ui@latest add button input label card table dropdown-menu dialog sheet badge alert toast separator

# TanStack Table para grids
npm install @tanstack/react-table@8

# Recharts para gráficas (Fase 2 avanzada)
npm install recharts@2

# Date handling
npm install date-fns@3

# Dev dependencies
npm install -D @types/node
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install -D eslint-plugin-react-hooks
```

### 1.2 Configuración de Vite

**Archivo**: `vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5174, // Diferente al portal externo (5173)
    proxy: {
      '/api': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
    },
  },
});
```

### 1.3 Configuración de TypeScript

**Archivo**: `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 1.4 Configuración de TailwindCSS

**Archivo**: `tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

### 1.5 Variables de Entorno

**Archivo**: `.env.development`

```env
VITE_API_URL=http://localhost:8010/api/v1
VITE_APP_NAME=Sistema Interno - Incapacidades
```

**Archivo**: `.env.production`

```env
VITE_API_URL=https://api.incapacidades.com/api/v1
VITE_APP_NAME=Sistema Interno - Incapacidades
```

### 1.6 Estructura de Carpetas Inicial

```bash
mkdir -p src/{components/{ui,layout,auth,incapacidades,shared},pages/{auth,dashboard,incapacidades},services,hooks,store,schemas,types,utils,lib}
```

**Resultado**:
```
src/
├── components/
│   ├── ui/              # Shadcn/ui components
│   ├── layout/          # AppShell, Sidebar, Header, Footer
│   ├── auth/            # LoginForm, ProtectedRoute
│   ├── incapacidades/   # Componentes del módulo
│   └── shared/          # DataTable, Pagination, etc.
├── pages/
│   ├── auth/            # LoginPage
│   ├── dashboard/       # DashboardPage
│   └── incapacidades/   # ConsultaPage, PendientesPage, etc.
├── services/            # API services
├── hooks/               # Custom hooks
├── store/               # Zustand stores
├── schemas/             # Zod schemas
├── types/               # TypeScript types
├── utils/               # Utilidades
└── lib/                 # Configuraciones
```

### ✅ Criterios de Aceptación - Setup
- [ ] Proyecto creado con Vite + React 19 + TypeScript
- [ ] TailwindCSS configurado correctamente
- [ ] Shadcn/ui inicializado con 10+ componentes
- [ ] Alias `@` funcionando para imports
- [ ] Variables de entorno configuradas
- [ ] Dev server corriendo en puerto 5174
- [ ] Proxy API funcionando (`/api` → `http://localhost:8010`)

---

## 2. Sistema de Autenticación

### 2.1 Types y Schemas

**Archivo**: `src/types/auth.ts`

```typescript
export interface User {
  id: string;
  username: string;
  email: string;
  nombres: string;
  apellidos: string;
  rol: RolUsuario;
  estado: EstadoUsuario;
  created_at: string;
  last_login?: string;
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

export interface LoginCredentials {
  username: string;
  password: string;
  remember?: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}
```

**Archivo**: `src/schemas/authSchema.ts`

```typescript
import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string()
    .min(3, 'El usuario debe tener al menos 3 caracteres')
    .max(50, 'El usuario no puede exceder 50 caracteres'),
  password: z.string()
    .min(6, 'La contraseña debe tener al menos 6 caracteres')
    .max(100, 'La contraseña no puede exceder 100 caracteres'),
  remember: z.boolean().optional(),
});

export type LoginFormData = z.infer<typeof loginSchema>;
```

### 2.2 Zustand Auth Store

**Archivo**: `src/store/authStore.ts`

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthTokens } from '@/types/auth';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  
  // Actions
  login: (user: User, tokens: AuthTokens) => void;
  logout: () => void;
  updateAccessToken: (token: string) => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: (user, tokens) => set({
        user,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        isAuthenticated: true,
      }),

      logout: () => set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
      }),

      updateAccessToken: (token) => set({ accessToken: token }),

      updateUser: (userData) => set((state) => ({
        user: state.user ? { ...state.user, ...userData } : null,
      })),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
```

### 2.3 Axios Client con Interceptores

**Archivo**: `src/lib/api.ts`

```typescript
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/store/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8010/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Agregar JWT
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Refresh token automático
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Si es 401 y no es retry, intentar refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = useAuthStore.getState().refreshToken;
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const { data } = await axios.post(
          `${import.meta.env.VITE_API_URL}/auth/refresh`,
          null,
          {
            headers: {
              Authorization: `Bearer ${refreshToken}`,
            },
          }
        );

        useAuthStore.getState().updateAccessToken(data.access_token);

        // Reintentar request original
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh falló, logout
        useAuthStore.getState().logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

### 2.4 Auth Service

**Archivo**: `src/services/authService.ts`

```typescript
import api from '@/lib/api';
import type { LoginCredentials, AuthResponse, User } from '@/types/auth';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const { data } = await api.post<{
      access_token: string;
      refresh_token: string;
      token_type: string;
      user: User;
    }>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    return {
      user: data.user,
      tokens: {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_type: data.token_type,
      },
    };
  },

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    }
  },

  async getCurrentUser(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};
```

### 2.5 Login Form Component

**Archivo**: `src/components/auth/LoginForm.tsx`

```typescript
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';

import { loginSchema, type LoginFormData } from '@/schemas/authSchema';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/store/authStore';

export function LoginForm() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setError(null);
      const response = await authService.login(data);
      
      login(response.user, response.tokens);
      
      // Redirigir según rol
      const redirectPath = getRedirectPath(response.user.rol);
      navigate(redirectPath);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Error al iniciar sesión';
      setError(message);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <Label htmlFor="username">Usuario o Email</Label>
        <Input
          id="username"
          {...register('username')}
          placeholder="usuario@ejemplo.com"
          disabled={isSubmitting}
        />
        {errors.username && (
          <p className="text-sm text-red-500">{errors.username.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Contraseña</Label>
        <Input
          id="password"
          type="password"
          {...register('password')}
          placeholder="••••••••"
          disabled={isSubmitting}
        />
        {errors.password && (
          <p className="text-sm text-red-500">{errors.password.message}</p>
        )}
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox id="remember" {...register('remember')} />
        <Label
          htmlFor="remember"
          className="text-sm font-normal cursor-pointer"
        >
          Recordarme
        </Label>
      </div>

      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        Iniciar Sesión
      </Button>

      <div className="text-center">
        <a
          href="/forgot-password"
          className="text-sm text-blue-600 hover:underline"
        >
          ¿Olvidó su contraseña?
        </a>
      </div>
    </form>
  );
}

function getRedirectPath(rol: string): string {
  switch (rol) {
    case 'ADMIN':
    case 'AUDITOR':
      return '/dashboard';
    case 'APROBADOR':
      return '/ordenes-pago';
    case 'EMPRESA':
      return '/incapacidades/consulta';
    default:
      return '/dashboard';
  }
}
```

### 2.6 Login Page

**Archivo**: `src/pages/auth/LoginPage.tsx`

```typescript
import { LoginForm } from '@/components/auth/LoginForm';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            {/* Logo aquí */}
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
              SI
            </div>
          </div>
          <CardTitle className="text-2xl font-bold">
            Sistema Interno de Incapacidades
          </CardTitle>
          <CardDescription>
            Ingrese sus credenciales para acceder
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm />
        </CardContent>
      </Card>
    </div>
  );
}
```

### 2.7 Protected Route Component

**Archivo**: `src/components/auth/ProtectedRoute.tsx`

```typescript
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import type { RolUsuario } from '@/types/auth';

interface ProtectedRouteProps {
  allowedRoles?: RolUsuario[];
}

export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.rol)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}
```

### ✅ Criterios de Aceptación - Autenticación
- [ ] Formulario de login funcional con validación Zod
- [ ] Login exitoso guarda tokens en Zustand store
- [ ] Redirección automática según rol del usuario
- [ ] Refresh token automático en 401
- [ ] Logout revoca tokens y limpia store
- [ ] ProtectedRoute bloquea rutas no autorizadas
- [ ] Tests: 15+ tests (LoginForm, authService, authStore)

---

## 3. Layout Principal

### 3.1 AppShell Component

**Archivo**: `src/components/layout/AppShell.tsx`

```typescript
import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Footer } from './Footer';

export function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
        
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>

        <Footer />
      </div>
    </div>
  );
}
```

### 3.2 Sidebar Component

**Archivo**: `src/components/layout/Sidebar.tsx`

```typescript
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  FileText,
  DollarSign,
  Building2,
  Users,
  UserCircle,
  BarChart3,
  Settings,
  ChevronDown,
  ChevronRight,
  Search,
  ClipboardList,
} from 'lucide-react';

interface MenuItem {
  label: string;
  icon: React.ElementType;
  href?: string;
  children?: MenuItem[];
  roles?: string[];
}

const menuItems: MenuItem[] = [
  {
    label: 'Dashboard',
    icon: LayoutDashboard,
    href: '/dashboard',
  },
  {
    label: 'Incapacidades',
    icon: FileText,
    children: [
      {
        label: 'Consulta',
        icon: Search,
        href: '/incapacidades/consulta',
        roles: ['ADMIN', 'AUDITOR'],
      },
      {
        label: 'Pendientes',
        icon: ClipboardList,
        href: '/incapacidades/pendientes',
        roles: ['ADMIN', 'AUDITOR'],
      },
    ],
  },
  {
    label: 'Órdenes de Pago',
    icon: DollarSign,
    href: '/ordenes-pago',
    roles: ['ADMIN', 'APROBADOR'],
  },
  {
    label: 'Empresas',
    icon: Building2,
    href: '/empresas',
    roles: ['ADMIN'],
  },
  {
    label: 'Afiliados',
    icon: Users,
    href: '/afiliados',
    roles: ['ADMIN'],
  },
  {
    label: 'Usuarios',
    icon: UserCircle,
    href: '/usuarios',
    roles: ['ADMIN'],
  },
  {
    label: 'Reportes',
    icon: BarChart3,
    href: '/reportes',
    roles: ['ADMIN', 'AUDITOR'],
  },
  {
    label: 'Configuración',
    icon: Settings,
    href: '/configuracion',
    roles: ['ADMIN'],
  },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen }: SidebarProps) {
  const location = useLocation();
  const [expandedItems, setExpandedItems] = useState<string[]>(['Incapacidades']);

  const toggleExpanded = (label: string) => {
    setExpandedItems((prev) =>
      prev.includes(label)
        ? prev.filter((item) => item !== label)
        : [...prev, label]
    );
  };

  const isActive = (href?: string) => {
    if (!href) return false;
    return location.pathname === href || location.pathname.startsWith(href);
  };

  const renderMenuItem = (item: MenuItem, level = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.label);
    const Icon = item.icon;

    if (hasChildren) {
      return (
        <div key={item.label} className="space-y-1">
          <button
            onClick={() => toggleExpanded(item.label)}
            className={cn(
              'flex items-center w-full px-3 py-2 text-sm font-medium rounded-md transition-colors',
              'hover:bg-slate-100 text-slate-700',
              isActive(item.href) && 'bg-blue-50 text-blue-600'
            )}
            style={{ paddingLeft: `${12 + level * 16}px` }}
          >
            <Icon className="mr-3 h-5 w-5" />
            <span className="flex-1 text-left">{item.label}</span>
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>

          {isExpanded && (
            <div className="space-y-1">
              {item.children.map((child) => renderMenuItem(child, level + 1))}
            </div>
          )}
        </div>
      );
    }

    return (
      <Link
        key={item.label}
        to={item.href || '#'}
        className={cn(
          'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
          'hover:bg-slate-100 text-slate-700',
          isActive(item.href) && 'bg-blue-50 text-blue-600'
        )}
        style={{ paddingLeft: `${12 + level * 16}px` }}
      >
        <Icon className="mr-3 h-5 w-5" />
        {item.label}
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        'w-64 bg-white border-r border-slate-200 flex flex-col transition-all duration-300',
        !isOpen && 'hidden lg:flex'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-200">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
            SI
          </div>
          <span className="font-semibold text-slate-900">
            Sistema Interno
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {menuItems.map((item) => renderMenuItem(item))}
      </nav>
    </aside>
  );
}
```

### 3.3 Header Component

**Archivo**: `src/components/layout/Header.tsx`

```typescript
import { Menu, Bell, User, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/authService';

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await authService.logout();
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={onMenuClick}
          className="lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </Button>

        <div>
          <h1 className="text-lg font-semibold text-slate-900">
            Gestión de Incapacidades
          </h1>
          <p className="text-sm text-slate-500">
            Bienvenido, {user?.nombres}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* Notificaciones */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <Badge
            variant="destructive"
            className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
          >
            3
          </Badge>
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <User className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">{user?.nombres} {user?.apellidos}</p>
                <p className="text-xs text-slate-500">{user?.email}</p>
                <Badge variant="outline" className="w-fit text-xs">
                  {user?.rol}
                </Badge>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate('/perfil')}>
              <User className="mr-2 h-4 w-4" />
              Perfil
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate('/configuracion')}>
              <User className="mr-2 h-4 w-4" />
              Configuración
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-red-600">
              <LogOut className="mr-2 h-4 w-4" />
              Cerrar Sesión
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
```

### 3.4 Footer Component

**Archivo**: `src/components/layout/Footer.tsx`

```typescript
export function Footer() {
  return (
    <footer className="h-12 bg-white border-t border-slate-200 flex items-center justify-center px-6">
      <p className="text-sm text-slate-500">
        © 2026 Sistema de Gestión de Incapacidades. Todos los derechos reservados.
      </p>
    </footer>
  );
}
```

### ✅ Criterios de Aceptación - Layout
- [ ] AppShell renderiza correctamente con Header, Sidebar, Footer
- [ ] Sidebar colapsa/expande en mobile
- [ ] Menú de Incapacidades tiene submenús (Consulta, Pendientes)
- [ ] Navegación activa resalta el ítem actual
- [ ] Header muestra nombre del usuario y rol
- [ ] Dropdown de usuario funciona (Perfil, Logout)
- [ ] Footer visible en todas las páginas
- [ ] Layout responsive (mobile, tablet, desktop)

---

## 4. Módulo Incapacidades - Consulta

### 4.1 Types de Incapacidad (Sistema Interno)

**Archivo**: `src/types/incapacidad.ts`

```typescript
export interface Incapacidad {
  id: string;
  numero: string;
  tipo: TipoIncapacidad;
  estado: EstadoIncapacidad;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  diagnostico_cie10: string;
  diagnostico_descripcion: string;
  valor_total: number;
  
  // Solicitante
  solicitante: Solicitante;
  
  // ARL
  empleado?: Empleado;
  empresa?: Empresa;
  siniestro?: Siniestro;
  
  // SALUD
  afiliado?: Afiliado;
  
  // Auditoría
  observaciones?: string;
  auditor?: Usuario;
  fecha_auditoria?: string;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

export enum TipoIncapacidad {
  ARL = 'ARL',
  SALUD = 'SALUD',
}

export enum EstadoIncapacidad {
  RADICADA = 'RADICADA',
  EN_AUDITORIA = 'EN_AUDITORIA',
  OBSERVADA = 'OBSERVADA',
  APROBADA = 'APROBADA',
  RECHAZADA = 'RECHAZADA',
  EN_PAGO = 'EN_PAGO',
  PAGADA = 'PAGADA',
  ANULADA = 'ANULADA',
}

export interface Solicitante {
  tipo_documento: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  email: string;
  telefono: string;
}

export interface Empleado {
  id: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  cargo: string;
  empresa: Empresa;
}

export interface Empresa {
  id: string;
  nit: string;
  razon_social: string;
  email_contacto: string;
}

export interface Afiliado {
  id: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  numero_poliza: string;
  estado: string;
}

export interface Siniestro {
  id: string;
  numero: string;
  fecha_ocurrencia: string;
  descripcion: string;
  estado: string;
}

export interface Usuario {
  id: string;
  username: string;
  nombres: string;
  apellidos: string;
  rol: string;
}

export interface HistorialEstado {
  id: string;
  estado_anterior: EstadoIncapacidad;
  estado_nuevo: EstadoIncapacidad;
  observacion: string;
  cambiado_por: Usuario;
  fecha_cambio: string;
}

export interface Documento {
  id: string;
  nombre: string;
  tipo: string;
  tamano: number;
  url_descarga: string;
  uploaded_at: string;
}
```

### 4.2 Consulta Service

**Archivo**: `src/services/incapacidadService.ts`

```typescript
import api from '@/lib/api';
import type { Incapacidad, HistorialEstado, Documento } from '@/types/incapacidad';

export interface ConsultaIncapacidadParams {
  numero?: string;
  tipo_documento?: string;
  numero_documento?: string;
  empresa_nit?: string;
  empleado_documento?: string;
  tipo?: 'ARL' | 'SALUD';
  estado?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
  skip?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export const incapacidadService = {
  async consultar(params: ConsultaIncapacidadParams): Promise<PaginatedResponse<Incapacidad>> {
    const { data } = await api.get<PaginatedResponse<Incapacidad>>('/incapacidades', {
      params,
    });
    return data;
  },

  async getById(id: string): Promise<Incapacidad> {
    const { data } = await api.get<Incapacidad>(`/incapacidades/${id}`);
    return data;
  },

  async getHistorial(id: string): Promise<HistorialEstado[]> {
    const { data } = await api.get<HistorialEstado[]>(`/incapacidades/${id}/historial`);
    return data;
  },

  async getDocumentos(id: string): Promise<Documento[]> {
    const { data } = await api.get<Documento[]>(`/incapacidades/${id}/documentos`);
    return data;
  },

  async cambiarEstado(
    id: string,
    nuevoEstado: string,
    observacion?: string
  ): Promise<Incapacidad> {
    const { data } = await api.post<Incapacidad>(`/incapacidades/${id}/cambiar-estado`, {
      nuevo_estado: nuevoEstado,
      observacion,
    });
    return data;
  },
};
```

### 4.3 Consulta Filters Component

**Archivo**: `src/components/incapacidades/ConsultaFilters.tsx`

```typescript
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import type { ConsultaIncapacidadParams } from '@/services/incapacidadService';

interface ConsultaFiltersProps {
  onSearch: (params: ConsultaIncapacidadParams) => void;
  isLoading?: boolean;
}

export function ConsultaFilters({ onSearch, isLoading }: ConsultaFiltersProps) {
  const { register, handleSubmit, reset, setValue, watch } = useForm<ConsultaIncapacidadParams>();

  const onSubmit = (data: ConsultaIncapacidadParams) => {
    // Filtrar campos vacíos
    const params = Object.entries(data).reduce((acc, [key, value]) => {
      if (value !== '' && value !== undefined) {
        acc[key] = value;
      }
      return acc;
    }, {} as any);

    onSearch(params);
  };

  const handleReset = () => {
    reset();
    onSearch({});
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Número de Radicación */}
            <div className="space-y-2">
              <Label htmlFor="numero">Número de Radicación</Label>
              <Input
                id="numero"
                {...register('numero')}
                placeholder="INC-ARL-20260123-0001"
              />
            </div>

            {/* Tipo */}
            <div className="space-y-2">
              <Label htmlFor="tipo">Tipo</Label>
              <Select onValueChange={(value) => setValue('tipo', value as any)}>
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Todos</SelectItem>
                  <SelectItem value="ARL">ARL</SelectItem>
                  <SelectItem value="SALUD">SALUD</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Estado */}
            <div className="space-y-2">
              <Label htmlFor="estado">Estado</Label>
              <Select onValueChange={(value) => setValue('estado', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Todos</SelectItem>
                  <SelectItem value="RADICADA">Radicada</SelectItem>
                  <SelectItem value="EN_AUDITORIA">En Auditoría</SelectItem>
                  <SelectItem value="OBSERVADA">Observada</SelectItem>
                  <SelectItem value="APROBADA">Aprobada</SelectItem>
                  <SelectItem value="RECHAZADA">Rechazada</SelectItem>
                  <SelectItem value="EN_PAGO">En Pago</SelectItem>
                  <SelectItem value="PAGADA">Pagada</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Documento Empleado */}
            <div className="space-y-2">
              <Label htmlFor="empleado_documento">Documento Empleado</Label>
              <Input
                id="empleado_documento"
                {...register('empleado_documento')}
                placeholder="1234567890"
              />
            </div>

            {/* NIT Empresa */}
            <div className="space-y-2">
              <Label htmlFor="empresa_nit">NIT Empresa</Label>
              <Input
                id="empresa_nit"
                {...register('empresa_nit')}
                placeholder="900123456"
              />
            </div>

            {/* Fecha Inicio */}
            <div className="space-y-2">
              <Label htmlFor="fecha_inicio">Fecha Inicio</Label>
              <Input
                id="fecha_inicio"
                type="date"
                {...register('fecha_inicio')}
              />
            </div>

            {/* Fecha Fin */}
            <div className="space-y-2">
              <Label htmlFor="fecha_fin">Fecha Fin</Label>
              <Input
                id="fecha_fin"
                type="date"
                {...register('fecha_fin')}
              />
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleReset}
              disabled={isLoading}
            >
              Limpiar
            </Button>
            <Button type="submit" disabled={isLoading}>
              <Search className="mr-2 h-4 w-4" />
              Buscar
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
```

### 4.4 Data Table Component (Genérico Reutilizable)

**Archivo**: `src/components/shared/DataTable.tsx`

```typescript
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  isLoading?: boolean;
  emptyMessage?: string;
}

export function DataTable<TData, TValue>({
  columns,
  data,
  isLoading,
  emptyMessage = 'No hay datos para mostrar',
}: DataTableProps<TData, TValue>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                {emptyMessage}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
```

### 4.5 Consulta Page

**Archivo**: `src/pages/incapacidades/ConsultaPage.tsx`

```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Eye } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/shared/DataTable';
import { ConsultaFilters } from '@/components/incapacidades/ConsultaFilters';
import { incapacidadService, type ConsultaIncapacidadParams } from '@/services/incapacidadService';
import type { Incapacidad } from '@/types/incapacidad';
import { formatCurrency, formatDate } from '@/utils/formatters';

const columns: ColumnDef<Incapacidad>[] = [
  {
    accessorKey: 'numero',
    header: 'N° Radicación',
  },
  {
    accessorKey: 'tipo',
    header: 'Tipo',
    cell: ({ row }) => (
      <Badge variant={row.original.tipo === 'ARL' ? 'default' : 'secondary'}>
        {row.original.tipo}
      </Badge>
    ),
  },
  {
    accessorKey: 'solicitante',
    header: 'Solicitante',
    cell: ({ row }) => (
      <div>
        <p className="font-medium">
          {row.original.solicitante.nombres} {row.original.solicitante.apellidos}
        </p>
        <p className="text-sm text-slate-500">
          {row.original.solicitante.numero_documento}
        </p>
      </div>
    ),
  },
  {
    accessorKey: 'empresa',
    header: 'Empresa',
    cell: ({ row }) => row.original.empresa?.razon_social || '-',
  },
  {
    accessorKey: 'fecha_inicio',
    header: 'Fecha Inicio',
    cell: ({ row }) => formatDate(row.original.fecha_inicio),
  },
  {
    accessorKey: 'dias_totales',
    header: 'Días',
    cell: ({ row }) => `${row.original.dias_totales} días`,
  },
  {
    accessorKey: 'valor_total',
    header: 'Valor',
    cell: ({ row }) => formatCurrency(row.original.valor_total),
  },
  {
    accessorKey: 'estado',
    header: 'Estado',
    cell: ({ row }) => (
      <Badge variant={getEstadoBadgeVariant(row.original.estado)}>
        {row.original.estado.replace('_', ' ')}
      </Badge>
    ),
  },
  {
    id: 'actions',
    header: 'Acciones',
    cell: ({ row }) => {
      const navigate = useNavigate();
      return (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(`/incapacidades/${row.original.id}`)}
        >
          <Eye className="h-4 w-4 mr-2" />
          Ver
        </Button>
      );
    },
  },
];

export function ConsultaPage() {
  const [params, setParams] = useState<ConsultaIncapacidadParams>({
    skip: 0,
    limit: 20,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['incapacidades', 'consulta', params],
    queryFn: () => incapacidadService.consultar(params),
  });

  const handleSearch = (newParams: ConsultaIncapacidadParams) => {
    setParams({ ...newParams, skip: 0, limit: 20 });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Consulta de Incapacidades</h1>
        <p className="text-slate-500 mt-1">
          Busque incapacidades por número, documento, empresa o rango de fechas
        </p>
      </div>

      <ConsultaFilters onSearch={handleSearch} isLoading={isLoading} />

      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold">
            Resultados ({data?.total || 0})
          </h2>
        </div>
        <div className="p-6">
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            emptyMessage="No se encontraron incapacidades con los filtros aplicados"
          />
        </div>
      </div>
    </div>
  );
}

function getEstadoBadgeVariant(estado: string) {
  switch (estado) {
    case 'APROBADA':
      return 'default';
    case 'RECHAZADA':
      return 'destructive';
    case 'OBSERVADA':
      return 'outline';
    case 'PAGADA':
      return 'default';
    default:
      return 'secondary';
  }
}
```

### ✅ Criterios de Aceptación - Consulta
- [ ] Filtros múltiples (número, tipo, estado, documento, empresa, fechas)
- [ ] Tabla con columnas: número, tipo, solicitante, empresa, fecha, días, valor, estado
- [ ] Botón "Ver" en cada fila lleva al detalle
- [ ] Estados con colores (badges)
- [ ] Loading state mientras consulta API
- [ ] Empty state cuando no hay resultados
- [ ] Solo accesible para roles ADMIN y AUDITOR
- [ ] Tests: 10+ tests (filtros, tabla, navegación)

---

## 5. Módulo Incapacidades - Pendientes

### 5.1 Pendientes Page

**Archivo**: `src/pages/incapacidades/PendientesPage.tsx`

```typescript
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { FileText, Clock } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/shared/DataTable';
import { incapacidadService } from '@/services/incapacidadService';
import type { Incapacidad } from '@/types/incapacidad';
import { formatDate, formatRelativeDate } from '@/utils/formatters';

const columns: ColumnDef<Incapacidad>[] = [
  {
    accessorKey: 'numero',
    header: 'N° Radicación',
    cell: ({ row }) => (
      <div className="flex items-center space-x-2">
        <FileText className="h-4 w-4 text-slate-400" />
        <span className="font-mono text-sm">{row.original.numero}</span>
      </div>
    ),
  },
  {
    accessorKey: 'created_at',
    header: 'Fecha Radicación',
    cell: ({ row }) => (
      <div>
        <p className="font-medium">{formatDate(row.original.created_at)}</p>
        <p className="text-sm text-slate-500 flex items-center">
          <Clock className="h-3 w-3 mr-1" />
          {formatRelativeDate(row.original.created_at)}
        </p>
      </div>
    ),
  },
  {
    accessorKey: 'solicitante',
    header: 'Solicitante',
    cell: ({ row }) => (
      <div>
        <p className="font-medium">
          {row.original.solicitante.nombres} {row.original.solicitante.apellidos}
        </p>
        <p className="text-sm text-slate-500">
          {row.original.solicitante.numero_documento}
        </p>
      </div>
    ),
  },
  {
    accessorKey: 'tipo',
    header: 'Tipo',
    cell: ({ row }) => (
      <Badge variant={row.original.tipo === 'ARL' ? 'default' : 'secondary'}>
        {row.original.tipo}
      </Badge>
    ),
  },
  {
    accessorKey: 'empresa',
    header: 'Empresa',
    cell: ({ row }) => row.original.empresa?.razon_social || '-',
  },
  {
    accessorKey: 'dias_totales',
    header: 'Días',
    cell: ({ row }) => (
      <span className="font-semibold">{row.original.dias_totales}</span>
    ),
  },
  {
    accessorKey: 'estado',
    header: 'Estado',
    cell: ({ row }) => (
      <Badge variant="outline">{row.original.estado.replace('_', ' ')}</Badge>
    ),
  },
  {
    id: 'actions',
    header: 'Acciones',
    cell: ({ row }) => {
      const navigate = useNavigate();
      return (
        <Button
          variant="default"
          size="sm"
          onClick={() => navigate(`/incapacidades/${row.original.id}/gestionar`)}
        >
          Gestionar
        </Button>
      );
    },
  },
];

export function PendientesPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['incapacidades', 'pendientes'],
    queryFn: () =>
      incapacidadService.consultar({
        estado: 'RADICADA,EN_AUDITORIA,OBSERVADA',
        skip: 0,
        limit: 100,
      }),
    refetchInterval: 30000, // Refetch cada 30 segundos
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Incapacidades Pendientes
          </h1>
          <p className="text-slate-500 mt-1">
            Gestione las incapacidades que requieren auditoría
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-blue-600">{data?.total || 0}</p>
          <p className="text-sm text-slate-500">Pendientes</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            emptyMessage="¡Excelente! No hay incapacidades pendientes de gestión."
          />
        </div>
      </div>
    </div>
  );
}
```

### ✅ Criterios de Aceptación - Pendientes
- [ ] Lista solo incapacidades en estado RADICADA, EN_AUDITORIA, OBSERVADA
- [ ] Contador de pendientes visible
- [ ] Botón "Gestionar" en cada fila
- [ ] Refetch automático cada 30 segundos
- [ ] Ordenamiento por fecha de radicación (más antigua primero)
- [ ] Solo accesible para roles ADMIN y AUDITOR
- [ ] Tests: 8+ tests

---

## 6. Gestión de Incapacidad

### 6.1 Detalle de Incapacidad Page

**Archivo**: `src/pages/incapacidades/GestionarPage.tsx`

```typescript
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, FileText, History, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';

import { IncapacidadDetalle } from '@/components/incapacidades/IncapacidadDetalle';
import { DocumentosViewer } from '@/components/incapacidades/DocumentosViewer';
import { HistorialTimeline } from '@/components/incapacidades/HistorialTimeline';
import { GestionActions } from '@/components/incapacidades/GestionActions';

import { incapacidadService } from '@/services/incapacidadService';

export function GestionarPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('detalle');

  const { data: incapacidad, isLoading } = useQuery({
    queryKey: ['incapacidad', id],
    queryFn: () => incapacidadService.getById(id!),
    enabled: !!id,
  });

  const { data: historial } = useQuery({
    queryKey: ['incapacidad', id, 'historial'],
    queryFn: () => incapacidadService.getHistorial(id!),
    enabled: !!id,
  });

  const { data: documentos } = useQuery({
    queryKey: ['incapacidad', id, 'documentos'],
    queryFn: () => incapacidadService.getDocumentos(id!),
    enabled: !!id,
  });

  const cambiarEstadoMutation = useMutation({
    mutationFn: ({ nuevoEstado, observacion }: { nuevoEstado: string; observacion?: string }) =>
      incapacidadService.cambiarEstado(id!, nuevoEstado, observacion),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      queryClient.invalidateQueries({ queryKey: ['incapacidades'] });
      toast({
        title: 'Estado actualizado',
        description: 'La incapacidad ha sido actualizada correctamente',
      });
      navigate('/incapacidades/pendientes');
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'No se pudo actualizar el estado',
        variant: 'destructive',
      });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!incapacidad) {
    return <div>Incapacidad no encontrada</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              Gestión de Incapacidad
            </h1>
            <p className="text-slate-500 mt-1 font-mono">{incapacidad.numero}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="detalle">
            <FileText className="h-4 w-4 mr-2" />
            Datos Generales
          </TabsTrigger>
          <TabsTrigger value="documentos">
            <FileText className="h-4 w-4 mr-2" />
            Documentos
          </TabsTrigger>
          <TabsTrigger value="historial">
            <History className="h-4 w-4 mr-2" />
            Historial
          </TabsTrigger>
        </TabsList>

        <TabsContent value="detalle" className="space-y-6">
          <IncapacidadDetalle incapacidad={incapacidad} />
          
          {/* Acciones de Gestión */}
          {['RADICADA', 'EN_AUDITORIA', 'OBSERVADA'].includes(incapacidad.estado) && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Acciones de Auditoría</h3>
              <GestionActions
                incapacidad={incapacidad}
                onAction={cambiarEstadoMutation.mutate}
                isLoading={cambiarEstadoMutation.isPending}
              />
            </Card>
          )}
        </TabsContent>

        <TabsContent value="documentos">
          <DocumentosViewer documentos={documentos || []} />
        </TabsContent>

        <TabsContent value="historial">
          <HistorialTimeline historial={historial || []} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### 6.2 Gestion Actions Component

**Archivo**: `src/components/incapacidades/GestionActions.tsx`

```typescript
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import type { Incapacidad } from '@/types/incapacidad';

const gestionSchema = z.object({
  observacion: z.string().optional(),
});

interface GestionActionsProps {
  incapacidad: Incapacidad;
  onAction: (data: { nuevoEstado: string; observacion?: string }) => void;
  isLoading?: boolean;
}

export function GestionActions({ incapacidad, onAction, isLoading }: GestionActionsProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(gestionSchema),
  });

  const onSubmit = (data: any) => {
    if (!selectedAction) return;
    onAction({ nuevoEstado: selectedAction, observacion: data.observacion });
  };

  const needsObservation = selectedAction === 'RECHAZADA' || selectedAction === 'OBSERVADA';

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Button
          type="button"
          variant={selectedAction === 'APROBADA' ? 'default' : 'outline'}
          className="h-24 flex flex-col items-center justify-center space-y-2"
          onClick={() => setSelectedAction('APROBADA')}
        >
          <CheckCircle className="h-8 w-8" />
          <span>Aprobar</span>
        </Button>

        <Button
          type="button"
          variant={selectedAction === 'OBSERVADA' ? 'default' : 'outline'}
          className="h-24 flex flex-col items-center justify-center space-y-2"
          onClick={() => setSelectedAction('OBSERVADA')}
        >
          <AlertCircle className="h-8 w-8" />
          <span>Observar</span>
        </Button>

        <Button
          type="button"
          variant={selectedAction === 'RECHAZADA' ? 'destructive' : 'outline'}
          className="h-24 flex flex-col items-center justify-center space-y-2"
          onClick={() => setSelectedAction('RECHAZADA')}
        >
          <XCircle className="h-8 w-8" />
          <span>Rechazar</span>
        </Button>
      </div>

      {selectedAction && (
        <div className="space-y-2">
          <Label htmlFor="observacion">
            Observaciones {needsObservation && <span className="text-red-500">*</span>}
          </Label>
          <Textarea
            id="observacion"
            {...register('observacion')}
            placeholder="Describa las razones de su decisión..."
            rows={4}
            required={needsObservation}
          />
          {errors.observacion && (
            <p className="text-sm text-red-500">{errors.observacion.message}</p>
          )}
        </div>
      )}

      {selectedAction && (
        <div className="flex justify-end space-x-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => setSelectedAction(null)}
            disabled={isLoading}
          >
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Procesando...' : 'Confirmar'}
          </Button>
        </div>
      )}
    </form>
  );
}
```

### ✅ Criterios de Aceptación - Gestión
- [ ] Tabs: Datos Generales, Documentos, Historial
- [ ] Botones: Aprobar, Observar, Rechazar
- [ ] Campo observaciones obligatorio para Rechazar/Observar
- [ ] Preview de documentos (PDF, imágenes)
- [ ] Timeline de historial de estados
- [ ] Cambio de estado actualiza tabla de pendientes
- [ ] Solo disponible para estados RADICADA, EN_AUDITORIA, OBSERVADA
- [ ] Tests: 20+ tests

---

## 7. Testing y Calidad

### 7.1 Setup de Testing

**Archivo**: `vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

**Archivo**: `src/test/setup.ts`

```typescript
import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
```

### 7.2 Test Coverage Goals

| Módulo | Cobertura Mínima | Tests Estimados |
|--------|------------------|-----------------|
| Auth (Login, Store) | 80% | 15 tests |
| Layout (Sidebar, Header) | 70% | 10 tests |
| Consulta (Filters, Table) | 75% | 12 tests |
| Pendientes (Page) | 70% | 8 tests |
| Gestión (Actions, Detail) | 80% | 20 tests |
| **Total** | **75%** | **65+ tests** |

### ✅ Criterios de Aceptación - Testing
- [ ] 65+ tests pasando
- [ ] Cobertura global >75%
- [ ] Tests de componentes críticos (LoginForm, GestionActions)
- [ ] Tests de servicios (authService, incapacidadService)
- [ ] Tests de stores (authStore)
- [ ] Mocks de API con MSW (opcional)

---

## 📦 Resumen de Entregables

### Semana 1-2: Setup + Autenticación + Layout
- [ ] Proyecto configurado con React 19 + TypeScript
- [ ] Sistema de autenticación completo
- [ ] Layout con sidebar, header, footer
- [ ] Tests: 25+ tests

### Semana 3-4: Módulo Incapacidades
- [ ] Página de consulta con filtros
- [ ] Página de pendientes
- [ ] Gestión de incapacidad completa
- [ ] Tests: 40+ tests

### Semana 5: Refinamiento y Testing
- [ ] Corrección de bugs
- [ ] Incremento de cobertura de tests
- [ ] Optimizaciones de performance
- [ ] Documentación técnica

---

## 🎯 Comandos Rápidos

```bash
# Desarrollo
npm run dev

# Tests
npm run test
npm run test:watch
npm run test:coverage

# Build
npm run build
npm run preview

# Lint
npm run lint
```

---

**Próximos pasos después de completar esta fase**:
1. Módulo de Órdenes de Pago
2. Gestión de Usuarios
3. Reportes y Analytics
4. Optimizaciones y mejoras de UX
