# Fase 2: Integración Frontend Portal Externo - Solicitante y Catálogo CIE-10

**Fecha**: 17 de enero de 2026  
**Duración estimada**: 3 días  
**Objetivo**: Integrar nuevas entidades en el wizard de radicación

---

## 📋 Resumen Ejecutivo

Este documento describe la integración frontend para los módulos **Solicitante** y **Catálogo CIE-10** implementados en backend. Se modificará el wizard de radicación del portal externo para incluir:

1. **Paso 0**: Captura de datos del solicitante con autocompletado
2. **Campo CIE-10**: Búsqueda inteligente de diagnósticos

---

## 🎯 Objetivos

### Funcionales
- Capturar datos del solicitante antes de radicar incapacidad
- Reutilizar solicitantes existentes mediante búsqueda por correo
- Implementar autocompletado de códigos CIE-10 con búsqueda en tiempo real
- Validar formato de código CIE-10 contra catálogo oficial
- Mejorar UX con sugerencias mientras el usuario escribe

### Técnicos
- Integrar con API `/solicitantes` y `/catalogos/cie10`
- Usar React Query para data fetching y cache
- Implementar debounce en búsquedas (300ms)
- Validar con Zod según reglas de backend
- Mantener TypeScript strict mode
- Tests >70% cobertura

---

## 🗂️ Estructura de Archivos (Frontend)

```
frontend/portal-externo/
├── src/
│   ├── types/
│   │   ├── solicitante.ts              ✅ NUEVO: Interfaces Solicitante
│   │   └── catalogoCIE10.ts            ✅ NUEVO: Interfaces CIE-10
│   ├── services/
│   │   ├── queries/
│   │   │   ├── useSolicitantes.ts      ✅ NUEVO: React Query hooks
│   │   │   └── useCatalogoCIE10.ts     ✅ NUEVO: React Query hooks
│   │   └── api.ts                      ✅ ACTUALIZAR: Agregar endpoints
│   ├── components/
│   │   ├── wizard/
│   │   │   ├── Step0Solicitante.tsx    ✅ NUEVO: Paso 0 (datos solicitante)
│   │   │   ├── Step1TipoIncapacidad.tsx ✅ ACTUALIZAR: Pasar a Step 1
│   │   │   ├── Step2DatosEmpleado.tsx   ✅ ACTUALIZAR: Pasar a Step 2
│   │   │   ├── Step3DatosIncapacidad.tsx ✅ ACTUALIZAR: Pasar a Step 3 + campo CIE-10 + campos medico
│   │   │   ├── Step4Documentos.tsx      ✅ ACTUALIZAR: Pasar a Step 4
│   │   │   ├── Step5Resumen.tsx         ✅ ACTUALIZAR: Pasar a Step 5
│   │   │   └── IncapacidadWizard.tsx    ✅ ACTUALIZAR: Agregar Step 0
│   │   ├── shared/
│   │   │   ├── SolicitanteAutocomplete.tsx ✅ NUEVO: Componente reutilizable
│   │   │   └── CIE10Autocomplete.tsx       ✅ NUEVO: Componente reutilizable
│   │   └── ui/
│   │       └── ... (shadcn/ui components)
│   ├── schemas/
│   │   ├── solicitante.ts              ✅ NUEVO: Zod validación
│   │   └── incapacidad.ts              ✅ ACTUALIZAR: Campo diagnostico_cie10
│   └── __tests__/
│       ├── components/
│       │   ├── SolicitanteAutocomplete.test.tsx ✅ NUEVO
│       │   └── CIE10Autocomplete.test.tsx       ✅ NUEVO
│       └── services/
│           ├── useSolicitantes.test.ts         ✅ NUEVO
│           └── useCatalogoCIE10.test.ts        ✅ NUEVO
```

---

## 📊 Tipos TypeScript

### Solicitante

```typescript
// types/solicitante.ts

export interface Solicitante {
  id: string;
  correo: string;
  nombres: string;
  apellidos: string;
  telefono: string | null;
  created_at: string;
  updated_at: string;
}

export interface SolicitanteCreate {
  correo: string;
  nombres: string;
  apellidos: string;
  telefono?: string;
}

export interface SolicitanteUpdate {
  nombres?: string;
  apellidos?: string;
  telefono?: string;
}

export interface SearchSolicitanteParams {
  correo: string;
  limit?: number;
}
```

### Catálogo CIE-10

```typescript
// types/catalogoCIE10.ts

export interface CatalogoCIE10 {
  id: string;
  codigo: string;
  descripcion: string;
  created_at: string;
  updated_at: string;
}

export interface SearchCIE10Params {
  query: string;
  limit?: number;
}

export interface CIE10Stats {
  count: number;
}
```

---

## 🔧 Servicios API

### Axios API Client

```typescript
// services/api.ts (actualizar)

import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8010/api/v1',
  timeout: 30000,
});

// Endpoints Solicitantes
export const solicitantesApi = {
  create: (data: SolicitanteCreate) => 
    api.post<Solicitante>('/solicitantes', data),
  
  search: (params: SearchSolicitanteParams) => 
    api.get<Solicitante[]>('/solicitantes/search', { params }),
  
  getById: (id: string) => 
    api.get<Solicitante>(`/solicitantes/${id}`),
  
  update: (id: string, data: SolicitanteUpdate) => 
    api.put<Solicitante>(`/solicitantes/${id}`, data),
  
  delete: (id: string) => 
    api.delete(`/solicitantes/${id}`),
};

// Endpoints Catálogo CIE-10
export const catalogoCIE10Api = {
  search: (params: SearchCIE10Params) => 
    api.get<CatalogoCIE10[]>('/catalogos/cie10', { params }),
  
  getByCodigo: (codigo: string) => 
    api.get<CatalogoCIE10>(`/catalogos/cie10/${codigo}`),
  
  list: (skip: number = 0, limit: number = 100) => 
    api.get<CatalogoCIE10[]>('/catalogos/cie10/all/list', { 
      params: { skip, limit } 
    }),
  
  stats: () => 
    api.get<CIE10Stats>('/catalogos/cie10/stats/count'),
};

export default api;
```

---

## 🪝 React Query Hooks

### Solicitantes

```typescript
// services/queries/useSolicitantes.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { solicitantesApi } from '../api';
import type { Solicitante, SolicitanteCreate, SearchSolicitanteParams } from '@/types/solicitante';
import { toast } from 'sonner';

// Query Keys
export const solicitanteKeys = {
  all: ['solicitantes'] as const,
  search: (params: SearchSolicitanteParams) => ['solicitantes', 'search', params] as const,
  byId: (id: string) => ['solicitantes', id] as const,
};

// Hook: Buscar solicitante por correo (autocomplete)
export function useSearchSolicitantes(params: SearchSolicitanteParams, enabled: boolean = true) {
  return useQuery({
    queryKey: solicitanteKeys.search(params),
    queryFn: async () => {
      const { data } = await solicitantesApi.search(params);
      return data;
    },
    enabled: enabled && params.correo.length >= 3, // Solo buscar si >=3 chars
    staleTime: 5 * 60 * 1000, // 5 minutos
    retry: 1,
  });
}

// Hook: Obtener solicitante por ID
export function useSolicitante(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: solicitanteKeys.byId(id),
    queryFn: async () => {
      const { data } = await solicitantesApi.getById(id);
      return data;
    },
    enabled: enabled && !!id,
  });
}

// Mutation: Crear solicitante
export function useCreateSolicitante() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (newSolicitante: SolicitanteCreate) => {
      const { data } = await solicitantesApi.create(newSolicitante);
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: solicitanteKeys.all });
      toast.success(`Solicitante ${data.nombres} registrado exitosamente`);
    },
    onError: (error: any) => {
      const message = error.response?.data?.error?.message || 'Error al crear solicitante';
      toast.error(message);
    },
  });
}
```

### Catálogo CIE-10

```typescript
// services/queries/useCatalogoCIE10.ts

import { useQuery } from '@tanstack/react-query';
import { catalogoCIE10Api } from '../api';
import type { SearchCIE10Params } from '@/types/catalogoCIE10';

// Query Keys
export const cie10Keys = {
  all: ['cie10'] as const,
  search: (params: SearchCIE10Params) => ['cie10', 'search', params] as const,
  byCodigo: (codigo: string) => ['cie10', codigo] as const,
  stats: () => ['cie10', 'stats'] as const,
};

// Hook: Buscar códigos CIE-10 (autocomplete)
export function useSearchCIE10(query: string, limit: number = 20) {
  return useQuery({
    queryKey: cie10Keys.search({ query, limit }),
    queryFn: async () => {
      const { data } = await catalogoCIE10Api.search({ query, limit });
      return data;
    },
    enabled: query.length >= 3, // Min 3 caracteres
    staleTime: 10 * 60 * 1000, // 10 minutos (datos estáticos)
    retry: 1,
  });
}

// Hook: Obtener código exacto
export function useCIE10ByCodigo(codigo: string, enabled: boolean = true) {
  return useQuery({
    queryKey: cie10Keys.byCodigo(codigo),
    queryFn: async () => {
      const { data } = await catalogoCIE10Api.getByCodigo(codigo);
      return data;
    },
    enabled: enabled && !!codigo,
    staleTime: 10 * 60 * 1000,
  });
}

// Hook: Estadísticas
export function useCIE10Stats() {
  return useQuery({
    queryKey: cie10Keys.stats(),
    queryFn: async () => {
      const { data } = await catalogoCIE10Api.stats();
      return data;
    },
    staleTime: 30 * 60 * 1000, // 30 minutos
  });
}
```

---

## 🎨 Componentes UI

### SolicitanteAutocomplete

```typescript
// components/shared/SolicitanteAutocomplete.tsx

import { useState, useEffect } from 'react';
import { useSearchSolicitantes } from '@/services/queries/useSolicitantes';
import { Command, CommandInput, CommandList, CommandItem, CommandEmpty } from '@/components/ui/command';
import { useDebounce } from '@/hooks/useDebounce';
import type { Solicitante } from '@/types/solicitante';

interface SolicitanteAutocompleteProps {
  value: Solicitante | null;
  onChange: (solicitante: Solicitante | null) => void;
  onEmailChange: (email: string) => void;
}

export function SolicitanteAutocomplete({ value, onChange, onEmailChange }: SolicitanteAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);
  
  const { data: solicitantes, isLoading } = useSearchSolicitantes(
    { correo: debouncedSearch, limit: 10 },
    debouncedSearch.length >= 3
  );

  useEffect(() => {
    onEmailChange(searchTerm);
  }, [searchTerm, onEmailChange]);

  return (
    <Command>
      <CommandInput
        placeholder="Buscar por correo electrónico..."
        value={searchTerm}
        onValueChange={setSearchTerm}
      />
      <CommandList>
        {isLoading && <CommandEmpty>Buscando...</CommandEmpty>}
        {!isLoading && solicitantes?.length === 0 && searchTerm.length >= 3 && (
          <CommandEmpty>No se encontraron solicitantes. Registre uno nuevo.</CommandEmpty>
        )}
        {solicitantes?.map((solicitante) => (
          <CommandItem
            key={solicitante.id}
            value={solicitante.correo}
            onSelect={() => onChange(solicitante)}
          >
            <div className="flex flex-col">
              <span className="font-medium">{solicitante.correo}</span>
              <span className="text-sm text-muted-foreground">
                {solicitante.nombres} {solicitante.apellidos}
              </span>
            </div>
          </CommandItem>
        ))}
      </CommandList>
    </Command>
  );
}
```

### CIE10Autocomplete

```typescript
// components/shared/CIE10Autocomplete.tsx

import { useState } from 'react';
import { useSearchCIE10 } from '@/services/queries/useCatalogoCIE10';
import { Command, CommandInput, CommandList, CommandItem, CommandEmpty } from '@/components/ui/command';
import { useDebounce } from '@/hooks/useDebounce';
import type { CatalogoCIE10 } from '@/types/catalogoCIE10';

interface CIE10AutocompleteProps {
  value: CatalogoCIE10 | null;
  onChange: (cie10: CatalogoCIE10 | null) => void;
}

export function CIE10Autocomplete({ value, onChange }: CIE10AutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState(value?.codigo || '');
  const debouncedSearch = useDebounce(searchTerm, 300);
  
  const { data: codigos, isLoading } = useSearchCIE10(debouncedSearch);

  return (
    <Command>
      <CommandInput
        placeholder="Buscar código CIE-10 o descripción..."
        value={searchTerm}
        onValueChange={setSearchTerm}
      />
      <CommandList className="max-h-[200px]">
        {isLoading && <CommandEmpty>Buscando en catálogo...</CommandEmpty>}
        {!isLoading && codigos?.length === 0 && searchTerm.length >= 3 && (
          <CommandEmpty>No se encontraron códigos CIE-10</CommandEmpty>
        )}
        {codigos?.map((codigo) => (
          <CommandItem
            key={codigo.id}
            value={codigo.codigo}
            onSelect={() => onChange(codigo)}
          >
            <div className="flex flex-col">
              <span className="font-mono font-medium">{codigo.codigo}</span>
              <span className="text-sm text-muted-foreground truncate">
                {codigo.descripcion}
              </span>
            </div>
          </CommandItem>
        ))}
      </CommandList>
    </Command>
  );
}
```

---

## 📝 Schemas de Validación (Zod)

### Solicitante

```typescript
// schemas/solicitante.ts

import { z } from 'zod';

export const solicitanteSchema = z.object({
  correo: z
    .string()
    .min(1, 'El correo es requerido')
    .email('Formato de correo inválido')
    .toLowerCase(),
  
  nombres: z
    .string()
    .min(2, 'Mínimo 2 caracteres')
    .max(100, 'Máximo 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, 'Solo letras y espacios'),
  
  apellidos: z
    .string()
    .min(2, 'Mínimo 2 caracteres')
    .max(100, 'Máximo 100 caracteres')
    .regex(/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/, 'Solo letras y espacios'),
  
  telefono: z
    .string()
    .regex(/^\d{7,20}$/, 'Teléfono debe tener 7-20 dígitos')
    .optional()
    .or(z.literal('')),
});

export type SolicitanteFormData = z.infer<typeof solicitanteSchema>;
```

### Actualización de Incapacidad

```typescript
// schemas/incapacidad.ts (actualizar)

import { z } from 'zod';

export const incapacidadSchema = z.object({
  // ... otros campos existentes ...
  
  diagnostico_cie10: z
    .string()
    .min(1, 'El código CIE-10 es requerido')
    .regex(/^[A-Z]\d{2}(\.\d{1,2})?$/, 'Formato CIE-10 inválido')
    .transform(val => val.toUpperCase()),
  
  solicitante_id: z.string().uuid().optional(), // Opcional si lo radica internamente
});
```

---

## 🧪 Tests

### Tests de Hooks (React Query)

```typescript
// __tests__/services/useSolicitantes.test.ts

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSearchSolicitantes } from '@/services/queries/useSolicitantes';
import { solicitantesApi } from '@/services/api';
import { vi } from 'vitest';

vi.mock('@/services/api');

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('useSearchSolicitantes', () => {
  it('should search solicitantes by email', async () => {
    const mockData = [
      { id: '1', correo: 'test@example.com', nombres: 'Test', apellidos: 'User', telefono: null }
    ];
    
    vi.mocked(solicitantesApi.search).mockResolvedValue({ data: mockData });
    
    const { result } = renderHook(
      () => useSearchSolicitantes({ correo: 'test', limit: 10 }, true),
      { wrapper }
    );
    
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    
    expect(result.current.data).toEqual(mockData);
    expect(solicitantesApi.search).toHaveBeenCalledWith({ correo: 'test', limit: 10 });
  });
  
  it('should not search with less than 3 characters', () => {
    const { result } = renderHook(
      () => useSearchSolicitantes({ correo: 'ab', limit: 10 }, true),
      { wrapper }
    );
    
    expect(result.current.fetchStatus).toBe('idle');
  });
});
```

### Tests de Componentes

```typescript
// __tests__/components/SolicitanteAutocomplete.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SolicitanteAutocomplete } from '@/components/shared/SolicitanteAutocomplete';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';

const queryClient = new QueryClient();

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('SolicitanteAutocomplete', () => {
  it('should render search input', () => {
    render(
      <SolicitanteAutocomplete value={null} onChange={vi.fn()} onEmailChange={vi.fn()} />,
      { wrapper }
    );
    
    expect(screen.getByPlaceholderText(/buscar por correo/i)).toBeInTheDocument();
  });
  
  it('should show results after typing', async () => {
    const onChange = vi.fn();
    const onEmailChange = vi.fn();
    
    render(
      <SolicitanteAutocomplete value={null} onChange={onChange} onEmailChange={onEmailChange} />,
      { wrapper }
    );
    
    const input = screen.getByPlaceholderText(/buscar por correo/i);
    fireEvent.change(input, { target: { value: 'test@example.com' } });
    
    await waitFor(() => {
      expect(onEmailChange).toHaveBeenCalledWith('test@example.com');
    });
  });
});
```

---

## 🚀 Integración en Wizard

### Step 0: Datos del Solicitante

```typescript
// components/wizard/Step0Solicitante.tsx

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { solicitanteSchema, type SolicitanteFormData } from '@/schemas/solicitante';
import { SolicitanteAutocomplete } from '@/components/shared/SolicitanteAutocomplete';
import { useCreateSolicitante } from '@/services/queries/useSolicitantes';
import type { Solicitante } from '@/types/solicitante';

interface Step0SolicitanteProps {
  onNext: (solicitante: Solicitante) => void;
}

export function Step0Solicitante({ onNext }: Step0SolicitanteProps) {
  const [selectedSolicitante, setSelectedSolicitante] = useState<Solicitante | null>(null);
  const [emailSearch, setEmailSearch] = useState('');
  
  const createMutation = useCreateSolicitante();
  
  const { register, handleSubmit, formState: { errors }, setValue } = useForm<SolicitanteFormData>({
    resolver: zodResolver(solicitanteSchema),
  });

  const handleSolicitanteSelect = (solicitante: Solicitante | null) => {
    setSelectedSolicitante(solicitante);
    
    if (solicitante) {
      setValue('correo', solicitante.correo);
      setValue('nombres', solicitante.nombres);
      setValue('apellidos', solicitante.apellidos);
      setValue('telefono', solicitante.telefono || '');
    }
  };

  const onSubmit = async (data: SolicitanteFormData) => {
    if (selectedSolicitante) {
      onNext(selectedSolicitante);
    } else {
      const newSolicitante = await createMutation.mutateAsync(data);
      onNext(newSolicitante);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Datos del Solicitante</h2>
        <p className="text-muted-foreground">
          Busque su correo o registre uno nuevo
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Correo Electrónico
          </label>
          <SolicitanteAutocomplete
            value={selectedSolicitante}
            onChange={handleSolicitanteSelect}
            onEmailChange={(email) => {
              setEmailSearch(email);
              setValue('correo', email);
            }}
          />
          {errors.correo && (
            <p className="text-sm text-destructive mt-1">{errors.correo.message}</p>
          )}
        </div>

        {(selectedSolicitante || emailSearch.length >= 3) && !selectedSolicitante && (
          <>
            <div>
              <label className="block text-sm font-medium mb-2">Nombres</label>
              <input
                {...register('nombres')}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Juan Carlos"
              />
              {errors.nombres && (
                <p className="text-sm text-destructive mt-1">{errors.nombres.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Apellidos</label>
              <input
                {...register('apellidos')}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Pérez Gómez"
              />
              {errors.apellidos && (
                <p className="text-sm text-destructive mt-1">{errors.apellidos.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Teléfono (opcional)
              </label>
              <input
                {...register('telefono')}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="3001234567"
              />
              {errors.telefono && (
                <p className="text-sm text-destructive mt-1">{errors.telefono.message}</p>
              )}
            </div>
          </>
        )}
      </div>

      <button
        type="submit"
        disabled={createMutation.isPending}
        className="w-full py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
      >
        {createMutation.isPending ? 'Guardando...' : 'Continuar'}
      </button>
    </form>
  );
}
```

### Step 3: Integración CIE-10

```typescript
// components/wizard/Step3DatosIncapacidad.tsx (actualizar)

import { CIE10Autocomplete } from '@/components/shared/CIE10Autocomplete';
import type { CatalogoCIE10 } from '@/types/catalogoCIE10';

// ... dentro del componente ...

const [selectedCIE10, setSelectedCIE10] = useState<CatalogoCIE10 | null>(null);

// ... en el JSX ...

<div>
  <label className="block text-sm font-medium mb-2">
    Diagnóstico CIE-10 *
  </label>
  <CIE10Autocomplete
    value={selectedCIE10}
    onChange={(cie10) => {
      setSelectedCIE10(cie10);
      setValue('diagnostico_cie10', cie10?.codigo || '');
    }}
  />
  {errors.diagnostico_cie10 && (
    <p className="text-sm text-destructive mt-1">
      {errors.diagnostico_cie10.message}
    </p>
  )}
  
  {selectedCIE10 && (
    <div className="mt-2 p-3 bg-muted rounded-md">
      <p className="text-sm">
        <span className="font-mono font-semibold">{selectedCIE10.codigo}</span>
        {' - '}
        <span>{selectedCIE10.descripcion}</span>
      </p>
    </div>
  )}
</div>
```

---

## ✅ Checklist de Implementación

### Tarea 1: Setup Inicial (1 hora)
- [ ] Crear tipos TypeScript (solicitante.ts, catalogoCIE10.ts)
- [ ] Agregar endpoints a api.ts
- [ ] Crear React Query hooks (useSolicitantes.ts, useCatalogoCIE10.ts)

### Tarea 2: Componentes Compartidos (2 horas)
- [ ] Implementar SolicitanteAutocomplete
- [ ] Implementar CIE10Autocomplete
- [ ] Crear hook useDebounce (si no existe)

### Tarea 3: Schemas de Validación (30 min)
- [ ] Crear solicitanteSchema (Zod)
- [ ] Actualizar incapacidadSchema con diagnostico_cie10

### Tarea 4: Wizard - Paso 0 (2 horas)
- [ ] Crear Step0Solicitante.tsx
- [ ] Integrar SolicitanteAutocomplete
- [ ] Validar con Zod
- [ ] Manejo de estados (existente vs nuevo)

### Tarea 5: Wizard - Campo CIE-10 (1 hora)
- [ ] Actualizar Step3DatosIncapacidad.tsx
- [ ] Integrar CIE10Autocomplete
- [ ] Mostrar código seleccionado con descripción

### Tarea 6: Actualizar Wizard Principal (1 hora)
- [ ] Renumerar pasos (0-5 en lugar de 0-4)
- [ ] Agregar lógica para Step 0
- [ ] Pasar solicitante_id a payload final

### Tarea 7: Tests (2 horas)
- [ ] Tests para useSolicitantes hook
- [ ] Tests para useCatalogoCIE10 hook
- [ ] Tests para SolicitanteAutocomplete
- [ ] Tests para CIE10Autocomplete

### Tarea 8: Validación E2E (1 hora)
- [ ] Probar flujo completo: buscar solicitante → crear incapacidad
- [ ] Probar flujo: registrar nuevo solicitante → crear incapacidad
- [ ] Probar búsqueda CIE-10 por código
- [ ] Probar búsqueda CIE-10 por descripción

---

## 🐛 Casos de Uso y Escenarios

### Escenario 1: Solicitante Existente
1. Usuario ingresa correo en Step 0
2. Aparece en autocompletado
3. Selecciona y campos se prellenan
4. Continúa al Step 1 (tipo incapacidad)

### Escenario 2: Solicitante Nuevo
1. Usuario ingresa correo no registrado
2. No aparece en autocompletado
3. Sistema muestra campos de registro
4. Completa nombres, apellidos, teléfono
5. Sistema crea solicitante al continuar

### Escenario 3: Búsqueda CIE-10 por Código
1. Usuario escribe "A00" en Step 3
2. Aparecen todos los códigos A00, A00.0, A00.1, etc.
3. Selecciona "A00 - Cólera"
4. Campo se rellena con código

### Escenario 4: Búsqueda CIE-10 por Descripción
1. Usuario escribe "diabetes" en Step 3
2. Aparecen E10, E11, E12, etc.
3. Selecciona "E10 - Diabetes mellitus insulinodependiente"
4. Campo se rellena

---

## 📈 Métricas de Éxito

| Métrica | Objetivo |
|---------|----------|
| **Tests Coverage** | >70% |
| **Tiempo de Búsqueda** | <500ms |
| **UX Autocompletado** | 3+ caracteres, debounce 300ms |
| **Validación** | 100% esquemas Zod |
| **Errores API** | Manejo completo con toast |

---

## 📚 Próximos Pasos (Fase 3)

1. **Estadísticas**: Dashboard con solicitantes más frecuentes
2. **Notificaciones**: Email al solicitante cuando cambia estado
3. **Historial**: Ver incapacidades radicadas por solicitante
4. **Exportación**: Reporte de códigos CIE-10 más usados

---

**Documentación completa**: ✅ 17 de enero de 2026  
**Estado**: Lista para implementación  
**Próxima acción**: Iniciar Tarea 1 (Setup Inicial)
