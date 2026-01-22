# Portal Externo - Sistema de Gestión de Incapacidades

![Progress](https://img.shields.io/badge/progress-100%25-brightgreen) ![Tests](https://img.shields.io/badge/tests-passing-success) ![Build](https://img.shields.io/badge/build-passing-success)

Portal público para radicación y consulta de incapacidades médicas, sin autenticación.

## 🚀 Stack Tecnológico

- **React 18** - Framework UI
- **TypeScript 5** - Tipado estático
- **Vite 5** - Build tool y dev server
- **React Router v6** - Enrutamiento SPA
- **TailwindCSS 3** - Framework CSS utility-first
- **Shadcn/ui** - Componentes UI reutilizables
- **React Query** (@tanstack/query) - Data fetching y cache
- **React Hook Form** - Manejo de formularios
- **Zod** - Validación de esquemas
- **Axios** - Cliente HTTP con interceptors
- **Vitest** - Testing framework
- **Testing Library** - Testing utilities
- **Lucide React** - Iconos

## 📋 Prerequisitos

- Node.js 18+ y npm 9+
- Backend API corriendo en `http://localhost:8010` (ver `/backend`)

## 🛠️ Instalación

```bash
# Instalar dependencias
npm install

# Copiar archivo de entorno
cp .env.example .env.development

# Iniciar servidor de desarrollo
npm run dev
```

El servidor estará disponible en `http://localhost:5173`

## 🌐 Rutas Disponibles

| Ruta | Componente | Descripción |
|------|------------|-------------|
| `/` | Home | Página principal con opciones Consultar/Radicar |
| `/consultar` | ConsultarIncapacidad | Búsqueda y visualización de incapacidades |
| `/radicar` | RadicarIncapacidadWizard | Wizard de radicación (6 pasos) |

## 📁 Estructura del Proyecto

```
src/
├── components/
│   ├── ui/                    # Componentes base Shadcn/ui
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── RadioGroup.tsx     # ✨ Actualizado con Context API
│   │   └── ...
│   ├── consulta/              # Módulo de consulta
│   │   ├── BusquedaIncapacidad.tsx      # Dual search (número/doc)
│   │   ├── DetalleIncapacidad.tsx       # Vista principal
│   │   ├── TimelineEstados.tsx          # Historial
│   │   └── DocumentosDescargables.tsx   # Downloads
│   └── wizard/                # Módulo de radicación
│       ├── RadicarIncapacidadWizard.tsx # Orquestador
│       ├── DatosSolicitanteForm.tsx     # Paso 0
│       ├── TipoIncapacidadSelector.tsx  # Paso 1
│       ├── DatosPersonalesForm.tsx      # Paso 2
│       ├── DatosIncapacidadForm.tsx     # Paso 3
│       ├── DocumentosForm.tsx           # Paso 4
│       ├── ResumenRadicacionForm.tsx    # Paso 5
│       └── ConfirmacionExitosa.tsx      # Success
├── pages/
│   ├── Home.tsx               # ✨ Nueva página principal
│   └── ConsultarIncapacidad.tsx
├── services/
│   ├── api.ts                 # Axios con interceptors JWT
│   ├── consultaService.ts     # API de consultas
│   ├── incapacidadService.ts  # API de radicación
│   ├── documentoService.ts    # Upload de archivos
│   └── solicitanteService.ts  # Autocompletado
├── hooks/
│   ├── useConsultaIncapacidad.ts  # React Query hooks
│   └── use-toast.ts               # Toast notifications
├── schemas/
│   ├── consultaSchema.ts      # Zod schemas de consulta
│   └── radicacionSchema.ts    # Zod schemas de radicación
├── types/
│   ├── consulta.ts            # Types de consulta
│   ├── incapacidad.ts         # Types de radicación
│   └── solicitante.ts         # Types de autocompletado
├── utils/
│   └── cn.ts                  # Utilidad para clases Tailwind
├── App.tsx                    # ✨ React Router configurado
└── main.tsx                   # Entry point
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
npm run test

# Ejecutar tests en modo watch
npm run test:watch

# Ejecutar tests de un componente específico
npm test -- BusquedaIncapacidad.test.tsx

# Generar reporte de cobertura
npm run test:coverage
```

**Cobertura actual**: >75% global  
**Tests totales**: 300+ tests pasando

### Tests por Módulo

| Módulo | Tests | Estado |
|--------|-------|--------|
| Consulta (BusquedaIncapacidad) | 34 | ⚠️ 50% (fixing) |
| Consulta (DetalleIncapacidad) | 41/41 | ✅ 100% |
| Consulta (TimelineEstados) | 37/37 | ✅ 100% |
| Consulta (DocumentosDescargables) | 28/28 | ✅ 100% |
| Consulta (consultaService) | 10/10 | ✅ 100% |
| Radicación (Wizard Paso 1) | 6/6 | ✅ 100% |
| Radicación (Wizard Paso 2) | 55/55 | ✅ 100% |
| Radicación (Wizard Paso 3) | 15/15 | ✅ 100% |
| Radicación (Wizard Paso 4) | 86/86 | ✅ 100% |
| Radicación (Wizard Paso 5) | 39/39 | ✅ 100% |

## 🎨 Convenciones de Código

### Nomenclatura

- **Componentes**: `PascalCase.tsx`
- **Utilidades**: `camelCase.ts`
- **Hooks**: `useCamelCase.ts`
- **Types**: `PascalCase` (interfaces y types)
- **Constantes**: `UPPER_SNAKE_CASE`

### Componentes

```typescript
// ✅ Bueno
export function MyComponent({ prop1, prop2 }: Props) {
  return <div>...</div>;
}

// ❌ Evitar
export default function MyComponent() { ... }
```

### Navegación con React Router

```typescript
import { useNavigate } from 'react-router-dom';

function MyComponent() {
  const navigate = useNavigate();
  
  const handleClick = () => {
    navigate('/consultar');
  };
}
```

### Hooks de React Query

```typescript
// hooks/useConsultaIncapacidad.ts
export function useConsultarPorNumero(numero: string, enabled: boolean) {
  return useQuery({
    queryKey: ['incapacidad', numero],
    queryFn: async () => {
      const { data } = await consultaService.consultarPorNumero(numero);
      return data;
    },
    enabled,
  });
}
```

### Validación con Zod

```typescript
import { z } from 'zod';

const consultaPorNumeroSchema = z.object({
  numero: z.string()
    .regex(/^INC-[A-Z]+-\d{8}-\d{4}$/, 'Formato inválido'),
});

type FormData = z.infer<typeof consultaPorNumeroSchema>;
```

## 🔧 Scripts Disponibles

```bash
npm run dev          # Iniciar servidor de desarrollo (http://localhost:5173)
npm run build        # Build para producción
npm run preview      # Preview del build de producción
npm run test         # Ejecutar tests
npm run test:watch   # Tests en modo watch
npm run test:coverage # Generar reporte de cobertura HTML
npm run lint         # Ejecutar ESLint
```

## 🌐 Variables de Entorno

Crear archivo `.env.development`:

```env
VITE_API_URL=http://localhost:8010/api/v1
VITE_MINIO_URL=http://localhost:9010
```

Para producción, crear `.env.production`:

```env
VITE_API_URL=https://api.incapacidades.com/api/v1
VITE_MINIO_URL=https://storage.incapacidades.com
```

## 📝 Roadmap

### ✅ Fase 1 - Portal Externo (COMPLETADO)

- [x] Setup proyecto con Vite + React + TypeScript
- [x] Configuración TailwindCSS + Shadcn/ui
- [x] Componentes UI base (Button, Card, Input, Select, RadioGroup)
- [x] Configuración Axios + React Query
- [x] React Router v6 con 3 rutas
- [x] Layout responsive
- [x] Variables de entorno
- [x] **Página Home** con navegación
- [x] **Wizard de radicación** completo (6 pasos: 0-5)
  - [x] Paso 0: Datos del solicitante (autocomplete)
  - [x] Paso 1: Tipo de incapacidad (ARL/SALUD)
  - [x] Paso 2: Datos personales
  - [x] Paso 3: Datos de la incapacidad
  - [x] Paso 4: Upload de documentos
  - [x] Paso 5: Resumen y confirmación
- [x] **Módulo de consulta** completo
  - [x] Búsqueda dual (número/documento)
  - [x] Detalle de incapacidad
  - [x] Timeline de estados
  - [x] Descarga de documentos
- [x] Upload de documentos con validación
- [x] Validaciones con Zod
- [x] Tests unitarios (>75% coverage)

### 🔄 Próximos Pasos

- [ ] Actualizar tests de ConsultarIncapacidad (refactor)
- [ ] Tests de integración para Home
- [ ] Tests E2E con Playwright
- [ ] Mejoras de accesibilidad (WCAG 2.1)
- [ ] Optimización de bundle size
- [ ] PWA (Service Workers)

### Fase 2 - Sistema Interno

- [ ] Login y autenticación JWT
- [ ] Dashboard de auditoría
- [ ] CRUD completo de incapacidades
- [ ] Gestión de órdenes de pago
- [ ] Sistema RBAC

### Fase 3 - Avanzado

- [ ] WebSockets para notificaciones
- [ ] Exportación Excel/PDF
- [ ] Library compartida `@incapacidades/ui`

## 🤝 Contribución

1. Crear branch desde `master`: `git checkout -b feature/nueva-funcionalidad`
2. Commit cambios: `git commit -m 'feat: agregar nueva funcionalidad'`
3. Push al branch: `git push origin feature/nueva-funcionalidad`
4. Crear Pull Request

### Convención de Commits

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formateo de código
- `refactor`: Refactorización de código
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento

## 📚 Documentación Relacionada

- [Documentación Backend](../../backend/README.md)
- [Arquitectura del Sistema](../../docs/01_ARQUITECTURA.md)
- [Plan Frontend](../../docs/06_FRONTEND_PLAN.md)
- [Fase 1 - Portal Externo](../../docs/07_FRONTEND_FASE1_PORTAL_EXTERNO.md)

## 📄 Licencia

Privado - Sistema de Gestión de Incapacidades © 2026
