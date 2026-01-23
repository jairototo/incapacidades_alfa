# GitHub Copilot Instructions

## Descripción General del Proyecto

**Sistema de Gestión de Incapacidades** - Plataforma integral para aseguradoras que maneja el ciclo completo de incapacidades médicas desde la radicación hasta el pago, con soporte diferenciado para:
- **Incapacidades ARL** (Administradora de Riesgos Laborales): Con gestión de siniestros/accidentes laborales
- **Incapacidades SALUD**: Con gestión de afiliados y pólizas

### Stack Tecnológico Completo

#### Backend (100% completado) ✅
- **Framework**: FastAPI 0.109+ con Python 3.11+
- **ORM**: SQLAlchemy 2.0 (async/await native)
- **Base de Datos**: PostgreSQL 15+ (UUID primary keys, JSONB, triggers)
- **Cache/Session**: Redis 7+
- **Storage**: MinIO/S3 compatible
- **Task Queue**: Celery + RabbitMQ
- **Migraciones**: Alembic 1.13+
- **Validación**: Pydantic v2.5+
- **Auth**: python-jose (JWT), passlib (bcrypt)
- **Testing**: pytest + pytest-asyncio + pytest-cov (>80% coverage)
- **Logging**: Loguru (structured logging)

#### Frontend - Portal Externo (100% completado) ✅
- **Framework**: React 18 + TypeScript 5
- **Build Tool**: Vite 5
- **Styling**: TailwindCSS 3 + Shadcn/ui
- **Data Fetching**: React Query (@tanstack/react-query)
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios (con interceptors)
- **Routing**: React Router v6 (3 rutas: /, /consultar, /radicar)
- **Testing**: Vitest + Testing Library (>75% coverage, 300+ tests)
- **Deployment**: Vite build (520KB bundle optimizado)
- **Módulos implementados**:
  - ✅ Wizard de radicación (6 pasos: 0-5) - 217 tests
  - ✅ Módulo de consulta pública (4 componentes) - 141 tests
  - ✅ Página Home con navegación
  - ✅ Layout responsive completo

#### Infraestructura
- **Containerización**: Docker 24+ con Docker Compose (8 servicios)
- **Proxy**: Nginx 1.25+
- **CI/CD**: GitHub Actions (configurado)
- **Monitoreo**: Loguru para backend, console logs para frontend

#### Frontend - Sistema Interno (Fase 2 - Planificado)
- **Autenticación**: JWT con Zustand store
- **RBAC**: Control basado en roles (6 roles)
- **Dashboard**: Métricas en tiempo real
- **Tables**: TanStack Table
- **Charts**: Recharts
- **Estado**: Pendiente de implementación

### Puertos Configurados (custom para evitar conflictos)
- **API FastAPI**: `8010`
- **PostgreSQL**: `5442`
- **Redis**: `6389`
- **MinIO API**: `9010` / **Console**: `9011`
- **RabbitMQ AMQP**: `5682` / **Management**: `15682`
- **Flower (Celery)**: `5565`

---

## Arquitectura y Estructura

### Principios Arquitectónicos

1. **Clean Architecture / Hexagonal Pattern** (Backend)
   - Separación estricta de capas: API → Services → Repositories → Models
   - Dependency Injection via FastAPI dependencies
   - Domain-Driven Design (DDD) patterns

2. **Component-Driven Development** (Frontend)
   - Atomic Design con Shadcn/ui como base
   - Componentes reutilizables entre portal externo y sistema interno
   - Storybook para documentación visual (Fase 3)

3. **Async-First** 
   - SQLAlchemy 2.0 async/await
   - FastAPI endpoints async
   - React Query para data fetching asíncrono

### Modelo de Datos (11 Tablas)

**Entidades Principales**:
1. **USUARIO**: Autenticación, roles RBAC (6 roles: ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY), bloqueo por intentos fallidos
2. **REFRESH_TOKEN**: Tokens JWT con hash SHA256 y versioning
3. **EMPRESA**: Empresas ARL con sincronización externa (sync_source, external_id)
4. **EMPLEADO**: Empleados vinculados a empresas (para incapacidades ARL)
5. **AFILIADO**: Afiliados con pólizas de salud (para incapacidades SALUD)
6. **INCAPACIDAD**: Modelo polimórfico (ARL o SALUD) con workflow de estados
7. **SINIESTRO**: Accidentes laborales ARL (relación 1:N con incapacidades)
8. **DOCUMENTO**: Archivos con hashes MD5/SHA256 y almacenamiento MinIO
9. **HISTORIAL_ESTADO**: Auditoría de cambios de estado (polimórfico: incapacidad, siniestro, orden_pago)
10. **ORDEN_PAGO**: Órdenes de pago con workflow (GENERADA → APROBADA → PAGADA)
11. **AUDITORIA_LOG**: Logs de auditoría del sistema

**Relaciones Clave**:
```
EMPRESA 1──N EMPLEADO 1──N INCAPACIDAD (ARL)
                    │1
                    └──N SINIESTRO

AFILIADO 1──N INCAPACIDAD (SALUD)

INCAPACIDAD 1──N DOCUMENTO
            1──N HISTORIAL_ESTADO
            1──1 ORDEN_PAGO

USUARIO (cambiado_por) 1──N HISTORIAL_ESTADO
USUARIO (uploaded_by) 1──N DOCUMENTO
```

### Flujo de Estados (State Machine)

**Incapacidades**:
```
RADICADA → EN_AUDITORIA → {OBSERVADA, APROBADA, RECHAZADA}
                              │          │
                              │          └→ EN_PAGO → PAGADA
                              │
                              └→ (responder) → EN_AUDITORIA
```

**Órdenes de Pago**:
```
GENERADA → APROBADA → EN_PROCESO → PAGADA
    │                       │
    └→ ANULADA ←───────────┘
```

**Validaciones de Transición**:
- Solo **AUDITOR** puede: RADICADA → EN_AUDITORIA
- Solo **AUDITOR/APROBADOR** pueden: EN_AUDITORIA → OBSERVADA/APROBADA/RECHAZADA
- Solo **ADMIN** puede: APROBADA → EN_PAGO (genera orden de pago)
- Cada transición genera registro automático en HISTORIAL_ESTADO

---

## Convenciones de Código

### Backend (Python/FastAPI)

#### Nomenclatura
- **Archivos**: `snake_case.py`
- **Clases**: `PascalCase`
- **Funciones/variables**: `snake_case`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Private**: Prefijo `_` para métodos/atributos privados

#### Clean Architecture - Capas
1. **api/v1/endpoints/**: Endpoints REST (FastAPI routers) - Solo recepción y validación
2. **services/**: Lógica de negocio + workflow + validaciones
3. **db/repositories/**: Acceso a datos (CRUD genérico + queries específicas)
4. **models/**: Modelos SQLAlchemy (ORM)
5. **schemas/**: Schemas Pydantic (validación request/response)
6. **core/**: Configuración, seguridad, excepciones, logging

#### Async First
```python
# SIEMPRE usar async/await para I/O operations
async def get_incapacidad(db: AsyncSession, id: UUID) -> Incapacidad:
    result = await db.execute(select(Incapacidad).where(Incapacidad.id == id))
    return result.scalar_one_or_none()
```

#### Dependency Injection
```python
# Usar FastAPI dependencies
from app.core.security import get_current_user, PermissionChecker, Permissions

@router.post(
    "/", 
    response_model=IncapacidadResponse,
    dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_CREATE]))]
)
async def create_incapacidad(
    incapacidad: IncapacidadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
```

#### Modelos SQLAlchemy 2.0
```python
# SIEMPRE heredar de BaseModel
from app.models.base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Empresa(BaseModel):
    __tablename__ = "empresa"
    
    nit: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Relaciones con lazy="selectin" para async
    empleados: Mapped[List["Empleado"]] = relationship(
        back_populates="empresa",
        lazy="selectin"
    )
```

#### Schemas Pydantic v2
```python
# Separar por operación: Base, Create, Update, Response
from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime

class EmpresaBase(BaseModel):
    nit: str
    razon_social: str

class EmpresaCreate(EmpresaBase):
    email_contacto: str
    telefono: str | None = None

class EmpresaUpdate(BaseModel):
    razon_social: str | None = None
    email_contacto: str | None = None
    telefono: str | None = None

class EmpresaResponse(EmpresaBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Validadores con @field_validator
class IncapacidadCreate(BaseModel):
    diagnostico_cie10: str
    
    @field_validator('diagnostico_cie10')
    @classmethod
    def validate_cie10(cls, v: str) -> str:
        if not re.match(r'^[A-Z]\d{2}(\.\d{1,2})?$', v):
            raise ValueError('Código CIE-10 inválido')
        return v.upper()
```

#### Endpoints API
```python
# Estructura estándar
router = APIRouter(prefix="/empresas", tags=["empresas"])

@router.get("/", response_model=List[EmpresaResponse])
async def list_empresas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Listar empresas con paginación"""
    service = EmpresaService(db)
    return await service.list_empresas(skip=skip, limit=limit)

# Manejo de errores con excepciones custom
from app.core.exceptions import NotFoundException

@router.get("/{id}", response_model=EmpresaResponse)
async def get_empresa(
    id: UUID,
    db: AsyncSession = Depends(get_db)
):
    service = EmpresaService(db)
    empresa = await service.get_empresa(id)
    
    if not empresa:
        raise NotFoundException(f"Empresa {id} no encontrada")
    
    return empresa
```

#### Seguridad y RBAC
```python
# Usar PermissionChecker para proteger endpoints
from app.core.security import PermissionChecker, Permissions

@router.post(
    "/", 
    dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_CREATE]))]
)
async def create_incapacidad(...):
    pass

# JWT con access token (15 min) y refresh token (7 días)
# Token versioning: incrementar token_version en Usuario para invalidar todos los tokens
# Refresh tokens almacenados con hash SHA256 en BD
```

#### Testing
```python
# Tests unitarios y de integración con pytest
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_empresa(client: AsyncClient, db_session, test_user_admin):
    """Test creación de empresa"""
    response = await client.post(
        "/api/v1/empresas",
        json={"nit": "900123456", "razon_social": "Test SA"},
        headers={"Authorization": f"Bearer {test_user_admin.access_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["nit"] == "900123456"
    
# Objetivo: >80% cobertura global
```

#### Logging
```python
from app.core.logging import logger

# Usar niveles apropiados
logger.debug("Query SQL ejecutada", extra={"query": str(query)})
logger.info("Incapacidad creada", extra={"id": str(incapacidad.id), "user_id": str(current_user.id)})
logger.warning("Token próximo a expirar", extra={"user_id": str(user.id), "expires_at": token.expires_at})
logger.error("Error al procesar pago", extra={"incapacidad_id": str(incap_id), "error": str(e)})
```

#### Docstrings
```python
# Usar Google style
def cambiar_estado_incapacidad(
    incapacidad_id: UUID, 
    nuevo_estado: EstadoIncapacidad,
    observacion: str | None = None,
    current_user: Usuario
) -> Incapacidad:
    """
    Cambiar estado de incapacidad con validaciones de transición.
    
    Args:
        incapacidad_id: ID de la incapacidad
        nuevo_estado: Estado objetivo
        observacion: Comentario opcional del cambio
        current_user: Usuario que realiza el cambio
        
    Returns:
        Incapacidad con estado actualizado
        
    Raises:
        NotFoundException: Si la incapacidad no existe
        ValidationException: Si la transición no es válida
        PermissionException: Si el usuario no tiene permisos
    """
```

---

### Frontend (React/TypeScript)

#### Nomenclatura
- **Archivos Componentes**: `PascalCase.tsx`
- **Archivos Utilidades**: `camelCase.ts`
- **Custom Hooks**: `useCamelCase.ts`
- **Tipos/Interfaces**: `PascalCase`
- **Constantes**: `UPPER_SNAKE_CASE`

#### Estructura de Componentes
```typescript
// components/IncapacidadForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const formSchema = z.object({
  fecha_inicio: z.date(),
  fecha_fin: z.date(),
  diagnostico_cie10: z.string().regex(/^[A-Z]\d{2}(\.\d{1,2})?$/, 'CIE-10 inválido'),
  dias_totales: z.number().int().positive(),
});

type FormData = z.infer<typeof formSchema>;

export function IncapacidadForm({ onSubmit }: Props) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* campos */}
    </form>
  );
}
```

#### React Query Patterns
```typescript
// services/queries/useIncapacidades.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api';

export function useIncapacidades(params?: QueryParams) {
  return useQuery({
    queryKey: ['incapacidades', params],
    queryFn: async () => {
      const { data } = await api.get('/incapacidades', { params });
      return data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
}

export function useCreateIncapacidad() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (newIncapacidad: CreateIncapacidadDTO) => {
      const { data } = await api.post('/incapacidades', newIncapacidad);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidades'] });
      toast.success('Incapacidad creada exitosamente');
    },
    onError: (error) => {
      toast.error(`Error: ${error.message}`);
    },
  });
}
```

#### Axios con JWT Interceptors
```typescript
// services/api.ts
import axios from 'axios';
import { getAccessToken, refreshToken, logout } from '@/store/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8010/api/v1',
  timeout: 30000,
});

// Request interceptor - agregar JWT
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - refresh token automático
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const newToken = await refreshToken();
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch {
        logout();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
```

#### Type Safety
```typescript
// types/api.ts
export interface IncapacidadResponse {
  id: string;
  numero: string;
  tipo: TipoIncapacidad;
  estado: EstadoIncapacidad;
  fecha_inicio: string; // ISO date
  fecha_fin: string;
  dias_totales: number;
  valor_total: number;
  empleado?: EmpleadoResponse;
  afiliado?: AfiliadoResponse;
  created_at: string;
  updated_at: string;
}

export enum EstadoIncapacidad {
  RADICADA = 'RADICADA',
  EN_AUDITORIA = 'EN_AUDITORIA',
  OBSERVADA = 'OBSERVADA',
  APROBADA = 'APROBADA',
  RECHAZADA = 'RECHAZADA',
  EN_PAGO = 'EN_PAGO',
  PAGADA = 'PAGADA',
}

export enum TipoIncapacidad {
  ARL = 'ARL',
  SALUD = 'SALUD',
}
```

#### Zustand Store (Auth)
```typescript
// store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  login: (tokens: Tokens, user: User) => void;
  logout: () => void;
  refreshAccessToken: () => Promise<string>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      
      login: (tokens, user) => set({ 
        accessToken: tokens.access_token, 
        refreshToken: tokens.refresh_token,
        user 
      }),
      
      logout: () => set({ 
        accessToken: null, 
        refreshToken: null, 
        user: null 
      }),
      
      refreshAccessToken: async () => {
        const { refreshToken } = get();
        const { data } = await api.post('/auth/refresh', null, {
          headers: { Authorization: `Bearer ${refreshToken}` }
        });
        
        set({ accessToken: data.access_token });
        return data.access_token;
      },
    }),
    { name: 'auth-storage' }
  )
);
```

---

## Referencias Rápidas

### Enums Principales
Ubicación: `app/utils/enums.py` (17 enumeraciones)

**Tipos de Incapacidad**:
- `TipoIncapacidad`: ARL, SALUD
- `SubtipoIncapacidadARL`: ACCIDENTE_TRABAJO, ENFERMEDAD_LABORAL, ACCIDENTE_TRAYECTO
- `SubtipoIncapacidadSalud`: ENFERMEDAD_GENERAL, MATERNIDAD, LICENCIA

**Estados y Workflow**:
- `EstadoIncapacidad`: RADICADA, EN_AUDITORIA, OBSERVADA, APROBADA, RECHAZADA, EN_PAGO, PAGADA, ANULADA
- `EstadoOrdenPago`: GENERADA, APROBADA, RECHAZADA, EN_PROCESO, PAGADA, ANULADA
- `EstadoSiniestro`: REPORTADO, EN_INVESTIGACION, CERRADO, ANULADO
- `EstadoAfiliado`: ACTIVO, INACTIVO, SUSPENDIDO

**Usuarios y Seguridad**:
- `RolUsuario`: ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY
- `EstadoUsuario`: ACTIVO, INACTIVO, BLOQUEADO

**Otros**:
- `TipoDocumento`: CEDULA, PASAPORTE, CEDULA_EXTRANJERIA, etc.
- `TipoPoliza`: INDIVIDUAL, FAMILIAR, COLECTIVA
- `TipoDocumentoArchivo`: INCAPACIDAD_MEDICA, HISTORIA_CLINICA, SOPORTE_ARL, etc.
- `TipoCuenta`: AHORROS, CORRIENTE
- `AccionAuditoria`: CREATE, UPDATE, DELETE, APPROVE, REJECT, etc.
- `Prioridad`: BAJA, NORMAL, ALTA, URGENTE

### Comandos Útiles

```bash
# Desarrollo
docker compose up -d                    # Iniciar todos los servicios
docker compose logs -f api              # Ver logs de la API
docker compose restart api              # Reiniciar solo la API
docker compose down                     # Detener todos los servicios

# Base de Datos
docker compose exec postgres psql -U incapacidades_user -d incapacidades_db

# Migraciones
docker compose exec api alembic upgrade head                    # Aplicar migraciones
docker compose exec api alembic revision --autogenerate -m "..."  # Crear migración
docker compose exec api alembic current                         # Ver versión actual
docker compose exec api alembic downgrade -1                    # Rollback

# Tests
docker compose exec api pytest                                  # Todos los tests
docker compose exec api pytest tests/test_auth_service.py       # Test específico
docker compose exec api pytest --cov=app --cov-report=html      # Reporte HTML

# Linting y Formateo
docker compose exec api black app/                              # Formatear código
docker compose exec api isort app/                              # Ordenar imports
docker compose exec api flake8 app/                             # Linter

# MinIO (Storage)
# Acceder a consola: http://localhost:9011
# Credenciales: minioadmin / minioadmin

# RabbitMQ (Queue)
# Acceder a management: http://localhost:15682
# Credenciales: guest / guest

# Flower (Celery Monitor)
# Acceder a UI: http://localhost:5565
```

---

## Estado Actual del Proyecto (23 de enero de 2026)

### Progreso Global: 100% (Fase 1) 🚀

| Componente | Completado | Pendiente | Prioridad |
|------------|------------|-----------|-----------|
| Arquitectura | 100% | - | ✅ |
| Modelo de Datos | 100% | - | ✅ |
| Documentación Backend | 100% | - | ✅ |
| Documentación Frontend | 100% | - | ✅ |
| Infraestructura | 100% | - | ✅ |
| Modelos SQLAlchemy | 11/11 (100%) | - | ✅ |
| Schemas Pydantic | 11/11 (100%) | - | ✅ |
| Repositories | 11/11 (100%) | - | ✅ |
| Services | 11/11 (100%) | - | ✅ |
| API Endpoints | 11/11 (100%) | - | ✅ |
| Autenticación JWT | 100% | - | ✅ |
| Sistema Storage MinIO | 100% | - | ✅ |
| Módulo Documentos | 100% | - | ✅ |
| Módulo Órdenes Pago | 100% | - | ✅ |
| Módulo Usuarios | 100% | - | ✅ |
| Tests Backend | 87% | Incrementar a >90% | 🟡 Media |
| **Frontend - Portal Externo** | **100%** | **-** | **✅** |

### Módulos 100% Completados ✅

#### Backend (11 módulos)

1. **Autenticación JWT** (20 tests, 87% cobertura)
   - Login, logout, refresh, change-password
   - Token versioning y revocación
   - Bloqueo automático por intentos fallidos

2. **Gestión de Documentos** (11 tests, 85% cobertura)
   - Upload/download con MinIO
   - Validación de archivos (extensión, MIME, tamaño)
   - Hashing MD5/SHA256
   - Presigned URLs

3. **Historial de Estados** (17 tests)
   - Patrón polimórfico
   - Auto-generación en transiciones
   - Consulta de auditoría

4. **Gestión de Incapacidades** (endpoints completos)
   - CRUD completo
   - Workflow ARL/SALUD
   - Soporte polimórfico empleado/afiliado

5. **Gestión de Órdenes de Pago** (endpoints completos)
   - Generación automática desde incapacidades aprobadas
   - Workflow: GENERADA → APROBADA → PAGADA/ANULADA
   - Integración con historial de estados

6. **Gestión de Usuarios** (endpoints completos)
   - CRUD completo con roles RBAC
   - Activar/desactivar cuentas
   - Reset de contraseña

7. **Gestión de Empresas, Empleados, Afiliados, Siniestros** (todos completos)

#### Frontend Portal Externo (2 módulos principales)

8. **Wizard de Radicación** (217 tests pasando, 100%)
   - Paso 0: Datos del solicitante con autocomplete
   - Paso 1: Tipo de incapacidad (ARL/SALUD selector)
   - Paso 2: Datos personales del empleado/afiliado
   - Paso 3: Datos de la incapacidad (fechas, diagnóstico CIE-10)
   - Paso 4: Upload de documentos (drag & drop, validaciones)
   - Paso 5: Resumen y confirmación
   - Confirmación exitosa con número de radicación

9. **Módulo de Consulta Pública** (141 tests pasando, 93%)
   - BusquedaIncapacidad: búsqueda dual (número/documento)
   - DetalleIncapacidad: información completa (41 tests)
   - TimelineEstados: historial visual (37 tests)
   - DocumentosDescargables: descarga de archivos (28 tests)
   - ConsultarIncapacidad: página de integración (23 tests)

10. **Página Home y Routing** (funcional, tests pendientes)
    - React Router v6 con 3 rutas (/, /consultar, /radicar)
    - Navegación entre módulos
    - Layout responsive compartido

### Infraestructura Operativa ✅
- PostgreSQL 15 con 11 tablas + índices optimizados
- Redis 7 para cache y sesiones
- MinIO para almacenamiento de documentos
- RabbitMQ + Celery para tareas asíncronas
- Docker Compose con 8 servicios healthy

---

## Prioridades Actuales

### ✅ Fase 1 - Portal Externo COMPLETADO (100%)

#### Backend (100%) ✅
- ✅ Todos los modelos, schemas, repositories, services y endpoints
- ✅ Autenticación JWT completa
- ✅ Sistema de storage con MinIO
- ✅ Tests: 87% cobertura (objetivo: >90%)

#### Frontend Portal Externo (100%) ✅
- ✅ Setup inicial proyecto React + Vite + TypeScript
- ✅ Configuración TailwindCSS + Shadcn/ui
- ✅ Wizard de radicación de incapacidades (6 pasos: 0-5)
  - ✅ Paso 0: Datos del solicitante con autocomplete
  - ✅ Paso 1: Tipo de incapacidad (ARL/SALUD)
  - ✅ Paso 2: Datos personales del empleado/afiliado
  - ✅ Paso 3: Datos de la incapacidad
  - ✅ Paso 4: Upload de documentos
  - ✅ Paso 5: Resumen y confirmación
- ✅ Módulo de consulta pública (4 componentes)
  - ✅ BusquedaIncapacidad: búsqueda dual (número/documento)
  - ✅ DetalleIncapacidad: vista completa
  - ✅ TimelineEstados: historial visual
  - ✅ DocumentosDescargables: descarga de archivos
- ✅ Página Home con navegación
- ✅ React Router v6 con 3 rutas (/, /consultar, /radicar)
- ✅ Integración con API (Axios + React Query)
- ✅ Validaciones con Zod
- ✅ Tests con Vitest + Testing Library (>75%, 300+ tests)

### 🔄 Próximos Pasos - Mejoras y Optimizaciones

#### Opción A: Completar Tests Pendientes (1-2 semanas)
- [ ] Completar tests de BusquedaIncapacidad (12/22 → 22/22)
- [ ] Completar tests de ConsultarIncapacidad (refactoring por cambios)
- [ ] Tests de integración para Home
- [ ] Incrementar cobertura backend a >90%

#### Opción B: Fase 2 - Sistema Interno (4-6 semanas)
#### Opción B: Fase 2 - Sistema Interno (4-6 semanas)
**Objetivo**: Dashboard de auditoría completo

**Tareas**:
1. Sistema de autenticación (login, guards, interceptors)
2. Dashboard con métricas en tiempo real
3. CRUD completo de incapacidades con workflow
4. Gestión de órdenes de pago
5. Gestión de usuarios y roles (RBAC)
6. Gestión de empresas, empleados, afiliados, siniestros
7. Sistema de permisos por rol
8. Reportes y exportación (Excel, PDF)

#### Opción C: Fase 3 - Funcionalidades Avanzadas (2-3 semanas)
**Tareas**:
1. Notificaciones en tiempo real (WebSockets)
2. Analytics avanzados
3. Firma digital de documentos
4. Integración con sistemas externos
5. Migración a monorepo (Turborepo/Nx)
6. Library compartida `@incapacidades/ui`

---

## Notas Importantes para el Agente de Desarrollo

### Principios Fundamentales
- Asegúrate de seguir la estructura de Clean Architecture en todo momento
- Prioriza el uso de funciones asíncronas para todas las operaciones de I/O
- Actualiza la documentación interna y los docstrings conforme avances en el desarrollo
- Ejecuta los tests después de cada implementación significativa
- Mantén la cobertura de tests por encima del 80%

### Modelo de Datos - Consideraciones Especiales

#### Soporte Polimórfico ARL/SALUD
- **Incapacidades ARL**: Requieren `empleado_id` + `empresa_id` + opcional `siniestro_id`
- **Incapacidades SALUD**: Requieren `afiliado_id` (no empleado/empresa)
- **Validación**: Constraint CHECK en base de datos asegura exclusividad
- **Schemas**: `IncapacidadARLCreate` vs `IncapacidadSaludCreate` separados

#### Sistema de Tokens Mejorado
- **Refresh Tokens**: Almacenados con hash SHA256 en base de datos
- **Token Versioning**: Campo `token_version` en Usuario para invalidación masiva
- **Revocación**: Campo `revoked` en RefreshToken para logout individual
- **Expiración**: Access token 15 min, Refresh token 7 días

#### Historial de Estados Polimórfico
- **Relación genérica**: Usando `entity_type` + `entity_id` (UUID genérico)
- **Soporta**: Incapacidad, Siniestro, OrdenPago (extensible)
- **Auto-generación**: Cada transición de estado crea registro automático

### Patrones de Diseño Implementados
1. **Repository Pattern**: Abstracción de acceso a datos con BaseRepository genérico
2. **Service Layer**: Lógica de negocio separada de controllers
3. **Dependency Injection**: FastAPI dependencies para DB, Auth, Permissions
4. **Factory Pattern**: Creación de entidades con validación en services
5. **Strategy Pattern**: Diferentes validadores según tipo (ARL vs SALUD)

### Entrega de Resultados

Al finalizar cada requerimiento o tarea, SIEMPRE debes entregar:

1. **Resumen Ejecutivo**: Breve descripción de lo completado (2-3 líneas)

2. **Cambios Realizados**: Lista de archivos modificados/creados con descripción

3. **Validación**: 
   - Resultado de tests ejecutados
   - Verificación de que no se introdujeron errores
   - Confirmación de que el código sigue los estándares del proyecto

4. **Actualización Documentación**: Si aplica, actualizar `docs/` y `ESTADO_PROYECTO.md`

5. **Próximos Pasos Sugeridos**: Proporcionar 2-3 opciones de continuación lógica

6. **Prompt Estructurado**: Generar un prompt completo y detallado para el siguiente paso, siguiendo este formato:

```markdown
### PROMPT SUGERIDO PARA EL SIGUIENTE PASO

**Contexto**: [Explicar el contexto actual y por qué este es el siguiente paso lógico]

**Objetivo**: [Describir claramente qué se debe lograr]

**Requerimientos específicos**:
- [Requerimiento 1 con detalles técnicos]
- [Requerimiento 2 con detalles técnicos]
- [Requerimiento 3 con detalles técnicos]

**Criterios de aceptación**:
- [ ] [Criterio verificable 1]
- [ ] [Criterio verificable 2]
- [ ] [Criterio verificable 3]

**Consideraciones técnicas**:
- [Patrones, dependencias, validaciones]
- [Integración con módulos existentes]

**Tests esperados**:
- [Tipo de tests a crear y cobertura esperada]

**Ejemplo de uso/salida esperada**:
[Código de ejemplo o descripción de la funcionalidad]
```

---

## Documentación de Referencia

Toda la documentación del proyecto está disponible en la carpeta `/docs`:

- **00_RESUMEN_PROYECTO.md**: Visión general del sistema
- **01_ARQUITECTURA.md**: Arquitectura completa (backend + frontend)
- **02_MODELO_DATOS.md**: Diagrama ER y definiciones de tablas
- **03_API_ENDPOINTS.md**: Especificación de 50+ endpoints REST
- **04_FLUJO_ESTADOS.md**: Máquina de estados y validaciones
- **05_STACK_Y_ESTRUCTURA.md**: Stack tecnológico detallado
- **06_FRONTEND_PLAN.md**: Plan de desarrollo frontend en 3 fases
- **07_FRONTEND_FASE1_PORTAL_EXTERNO.md**: Especificaciones portal público
- **08_FRONTEND_FASE2_SISTEMA_INTERNO.md**: Especificaciones dashboard interno
- **09_COMPONENTES_COMPARTIDOS.md**: Library de componentes reutilizables
- **10_INTEGRACION_BACKEND.md**: Guía de integración frontend-backend

**Estado del proyecto**: Ver `ESTADO_PROYECTO.md` (actualizado el 23 de enero de 2026)

---

**Última actualización**: 23 de enero de 2026  
**Versión**: 1.0.0-beta
