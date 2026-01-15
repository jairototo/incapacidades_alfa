# Portal Externo - Sistema de Gestión de Incapacidades

Portal público para radicación y consulta de incapacidades médicas, sin autenticación.

## 🚀 Stack Tecnológico

- **React 18** - Framework UI
- **TypeScript 5** - Tipado estático
- **Vite 7** - Build tool y dev server
- **TailwindCSS 4** - Framework CSS utility-first
- **React Query** - Data fetching y cache
- **React Hook Form** - Manejo de formularios
- **Zod** - Validación de esquemas
- **Axios** - Cliente HTTP
- **Vitest** - Testing framework
- **Testing Library** - Testing utilities

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

## 📁 Estructura del Proyecto

```
src/
├── components/
│   ├── ui/              # Componentes base (Button, Card, Input)
│   └── layout/          # Layout principal
├── services/
│   ├── api.ts           # Instancia de Axios
│   └── queries/         # React Query hooks (próximamente)
├── types/
│   └── api.ts           # TypeScript types e interfaces
├── utils/
│   └── cn.ts            # Utilidad para clases Tailwind
├── hooks/               # Custom hooks (próximamente)
├── test/
│   └── setup.ts         # Setup de testing
├── App.tsx              # Componente raíz
├── main.tsx             # Entry point
└── index.css            # Estilos globales + Tailwind
```

## 🧪 Testing

```bash
# Ejecutar tests
npm run test

# Ejecutar tests en modo watch
npm run test:watch

# Generar reporte de cobertura
npm run test:coverage
```

**Objetivo de cobertura**: >70%

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

### Hooks de React Query

```typescript
// services/queries/useIncapacidades.ts
export function useIncapacidades(params?: QueryParams) {
  return useQuery({
    queryKey: ['incapacidades', params],
    queryFn: async () => {
      const { data } = await api.get('/incapacidades', { params });
      return data;
    },
  });
}
```

### Validación con Zod

```typescript
import { z } from 'zod';

const schema = z.object({
  email: z.string().email('Email inválido'),
  nombre: z.string().min(2, 'Mínimo 2 caracteres'),
});

type FormData = z.infer<typeof schema>;
```

## 🔧 Scripts Disponibles

```bash
npm run dev          # Iniciar servidor de desarrollo
npm run build        # Build para producción
npm run preview      # Preview del build de producción
npm run test         # Ejecutar tests
npm run test:watch   # Tests en modo watch
npm run test:coverage # Generar reporte de cobertura
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

### Fase 1 - Portal Externo (En Desarrollo)

- [x] Setup proyecto con Vite + React + TypeScript
- [x] Configuración TailwindCSS + Shadcn/ui
- [x] Componentes UI base (Button, Card, Input)
- [x] Configuración Axios + React Query
- [x] Layout responsive
- [x] Variables de entorno
- [ ] Wizard de radicación (5 pasos)
- [ ] Consulta por número de radicación
- [ ] Upload de documentos
- [ ] Validaciones con Zod
- [ ] Tests unitarios (>70% coverage)

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
