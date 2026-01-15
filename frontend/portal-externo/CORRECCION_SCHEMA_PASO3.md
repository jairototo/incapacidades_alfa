# Corrección de Schema - Paso 3 del Wizard

**Fecha**: 2026-01-15  
**Estado**: ✅ Completado

## Problema Identificado

El formulario del Paso 3 (Datos de la Incapacidad) incluía campos que **no existen en el schema del backend** (`IncapacidadBase`), marcaba como requeridos campos que en realidad son opcionales, y mostraba campos económicos que son **exclusivos para auditoría interna**.

### Campos Eliminados (no existen en backend)
- `nombre_medico` - No está en IncapacidadBase
- `registro_medico` - No está en IncapacidadBase

### Campos Eliminados (exclusivos de auditoría)
- `valor_dia` - Se diligencia en el sistema interno durante auditoría
- `valor_total` - Se calcula en el sistema interno durante auditoría

**Nota**: Los campos económicos NO deben aparecer en el portal externo de radicación. Estos valores son asignados por el auditor en el sistema interno durante el proceso de revisión.

### Campos Corregidos a Opcional
Los siguientes campos se marcaban como `required` pero son `Optional` en el backend:
- `diagnostico_cie10` (Optional[str], max 10 caracteres)
- `descripcion_diagnostico` (Optional[str])
- `ips` (Optional[str], max 255 caracteres)
- `eps` (Optional[str], max 255 caracteres)

### Campos que Permanecen Requeridos
- `fecha_inicio` (date) ✅
- `fecha_fin` (date) ✅
- `tipo` (TipoIncapacidad) ✅

---

## Cambios Realizados

### 1. Documentación: `07_FRONTEND_FASE1_PORTAL_EXTERNO.md`

**Antes**:
```
Diagnóstico CIE-10: [Búsqueda con autocomplete]
Descripción: [Textarea]

Nombre del médico: [__________]
IPS que emite: [__________]
EPS: [__________]
```

**Después**:
```
Diagnóstico CIE-10: [__________] (opcional, máx 10 caracteres)
Descripción del diagnóstico: [Textarea] (opcional, máx 500 caracteres)

IPS: [__________] (opcional, Institución Prestadora de Salud)
EPS: [__________] (opcional, Entidad Promotora de Salud)
```

---

### 2. Schema de Validación: `radicacionSchema.ts`

#### Cambios en `datosIncapacidadBaseSchema`:

**Eliminados**:
```typescript
nombre_medico: z.string().min(5, ...).max(150, ...).regex(...),
registro_medico: z.string().min(5, ...).max(30, ...),
nombre_ips: z.string().min(3, ...).max(200, ...),
```

**Actualizados a Opcional**:
```typescript
diagnostico_cie10: z.string()
  .max(10, 'El código CIE-10 no puede exceder 10 caracteres')
  .regex(/^[A-Z]\d{2}(\.\d{1,2})?$/, 'Formato CIE-10 inválido. Ejemplo: A00, A00.1')
  .optional()
  .or(z.literal('')),
descripcion_diagnostico: z.string()
  .max(500, 'La descripción no puede exceder 500 caracteres')
  .optional()
  .or(z.literal('')),
ips: z.string()
  .max(255, 'El nombre de la IPS no puede exceder 255 caracteres')
  .optional()
  .or(z.literal('')),
eps: z.string()
  .max(255, 'El nombre de la EPS no puede exceder 255 caracteres')
  .optional()
  .or(z.literal('')),
```

---

### 3. Componente: `DatosIncapacidadForm.tsx`

#### Sección Eliminada:
```tsx
{/* Información del Médico Tratante */}
<div className="border-t pt-6">
  <h3 className="text-lg font-semibold text-gray-900 mb-4">
    Información del Médico Tratante
  </h3>
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <Input label="Nombre del Médico" {...} required />
    <Input label="Registro Médico" {...} required />
  </div>
</div>
```

#### Sección Actualizada (IPS/EPS):
```tsx
{/* ANTES */}
<Input label="Nombre de la IPS" {...register('nombre_ips')} required />
<Input label="EPS" {...register('eps')} required />

{/* DESPUÉS */}
<div className="border-t pt-6">
  <h3 className="text-lg font-semibold text-gray-900 mb-4">
    Información de Atención Médica (Opcional)
  </h3>
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <Input 
      label="IPS" 
      {...register('ips')}  // Renombrado de nombre_ips
      placeholder="Clínica Santa María"
      helperText="Institución Prestadora de Salud"
    />
    <Input 
      label="EPS" 
      {...register('eps')}
      placeholder="Sura EPS"
      helperText="Entidad Promotora de Salud"
    />
  </div>
</div>
```

#### Campos Actualizados (removido `required`):
- `diagnostico_cie10`: Removido `required`, actualizado placeholder a "(opcional)"
- `descripcion_diagnostico`: Removido `required`, actualizado placeholder
- `valor_dia`: Removido `required`, actualizado helperText

#### Sección Económica Eliminada:
```tsx
{/* ELIMINADO - Estos campos son exclusivos de auditoría interna */}
// Sección "Información Económica (Opcional)" con campos:
// - valor_dia (CurrencyInput)
// - valor_total (CurrencyInput auto-calculado)
```

**Razón**: Los valores económicos son asignados por el auditor en el sistema interno durante el proceso de revisión, NO durante la radicación inicial en el portal externo.

---

### 4. Tests: `DatosIncapacidadForm.test.tsx`

#### Tests Actualizados:

**1. Test de campos comunes**:
```typescript
// ELIMINADO
expect(screen.getByText('Nombre del Médico')).toBeInTheDocument();
expect(screen.getByText('Registro Médico')).toBeInTheDocument();
expect(screen.getByText('Nombre de la IPS')).toBeInTheDocument();

// CONSERVADO
expect(screen.getByText('IPS')).toBeInTheDocument();
expect(screen.getByText('EPS')).toBeInTheDocument();
```

**3. Test de datos iniciales**:
```typescript
// ANTES
const initialData = {
  nombre_medico: 'Dr. Juan Pérez',
  registro_medico: 'RM-12345',
  nombre_ips: 'Clínica Santa María',
  eps: 'Sura EPS',
  valor_dia: 50000,
  valor_total: 250000,
};

// DESPUÉS
const initialData = {
  ips: 'Clínica Santa María',  // Renombrado
  eps: 'Sura EPS',
  dias_totales: 5,  // Solo campo auto-calculado
};
```

**3. Test de secciones**:
```typescript
// ELIMINADO - Sección del médico
it('debe tener sección de información del médico', () => {
  expect(screen.getByText('Información del Médico Tratante')).toBeInTheDocument();
});

// ELIMINADO - Sección económica
it('debe tener sección de información económica', () => {
  expect(screen.getByText('Información Económica (Opcional)')).toBeInTheDocument();
});

// CONSERVADO - Sección IPS/EPS actualizada
it('debe tener sección de información de atención médica', () => {
  expect(screen.getByText('Información de Atención Médica (Opcional)')).toBeInTheDocument();
});
```

**4. Tests de campos auto-calculados**:
```typescript
// ELIMINADO
it('debe tener campo valor_total deshabilitado', () => {
  // Test eliminado porque valor_total ya no existe
});

it('debe mostrar texto de ayuda en campos auto-calculados', () => {
  expect(screen.getByText(/días × valor/día/)).toBeInTheDocument();
});

// CONSERVADO (actualizado)
it('debe mostrar texto de ayuda en campo dias_totales', () => {
  expect(screen.getByText('Calculado automáticamente')).toBeInTheDocument();
});
```

#### Corrección de Imports:
```typescript
// ANTES
import { render, screen, waitFor } from '@testing-library/react';

// DESPUÉS
import { render, screen } from '@testing-library/react';
```

---

## Validación Final

### ✅ Tests
```bash
Test Files  9 passed (9)
     Tests  93 passed | 2 skipped (95)
  Duration  10.74s
```

**Tests actualizados**:
- `DatosIncapacidadForm.test.tsx`: 15 tests (antes 18)
- Tests eliminados: 3 (valor_total deshabilitado, sección económica, texto ayuda valores)
- Tests conservados: 93 passing

### ✅ Build
```bash
vite v7.3.1 building client environment for production...
✓ 2841 modules transformed.
dist/index.html                   0.46 kB │ gzip:   0.30 kB
dist/assets/index-DFEEz8Tm.css   34.78 kB │ gzip:   7.08 kB
dist/assets/index-BIjIufNs.js   489.96 kB │ gzip: 153.14 kB
✓ built in 7.93s
```

**Sin errores de compilación** ✅  
**Bundle reducido**: -2.28 kB (eliminación de CurrencyInput en Paso 3)

---

## Schema Backend de Referencia

### `IncapacidadBase` (Pydantic Schema)

```python
class IncapacidadBase(BaseModel):
    tipo: TipoIncapacidad  # REQUERIDO
    subtipo: Optional[str] = None  # Opcional
    fecha_inicio: date  # REQUERIDO
    fecha_fin: date  # REQUERIDO
    diagnostico_cie10: Optional[str] = Field(None, max_length=10)  # Opcional
    descripcion_diagnostico: Optional[str] = None  # Opcional
    eps: Optional[str] = Field(None, max_length=255)  # Opcional
    ips: Optional[str] = Field(None, max_length=255)  # Opcional
    # CAMPOS DE AUDITORÍA (no en radicación inicial):
    valor_dia: Optional[Decimal] = Field(None, ge=0)  # Solo auditoría
    valor_total: Optional[Decimal] = Field(None, ge=0)  # Solo auditoría
    observaciones: Optional[str] = None  # Opcional
    prioridad: Prioridad = Prioridad.NORMAL  # Opcional con default

    @field_validator('fecha_fin')
    @classmethod
    def validate_fecha_fin(cls, v: date, info: ValidationInfo) -> date:
        if 'fecha_inicio' in info.data and v < info.data['fecha_inicio']:
            raise ValueError('fecha_fin debe ser >= fecha_inicio')
        return v
```

**Nota**: 
- `dias_totales` no está en `IncapacidadBase`, se calcula automáticamente en el backend.
- `valor_dia` y `valor_total` están en el schema pero **NO se envían desde el portal externo**. Se asignan durante la auditoría en el sistema interno.

---

## Resumen de Alineación Frontend-Backend

| Campo | Backend | Frontend Antes | Frontend Después |
|-------|---------|----------------|------------------|
| `tipo` | Required | ✅ Required | ✅ Required |
| `fecha_inicio` | Required | ✅ Required | ✅ Required |
| `fecha_fin` | Required | ✅ Required | ✅ Required |
| `diagnostico_cie10` | Optional | ❌ Required | ✅ Optional |
| `descripcion_diagnostico` | Optional | ❌ Required | ✅ Optional |
| `ips` | Optional | ❌ Required (como nombre_ips) | ✅ Optional (renombrado) |
| `eps` | Optional | ❌ Required | ✅ Optional |
| `valor_dia` | Optional (auditoría) | ❌ Visible y Required | ✅ Eliminado (portal externo) |
| `valor_total` | Optional (auditoría) | ❌ Visible y Required | ✅ Eliminado (portal externo) |
| `nombre_medico` | ❌ No existe | ❌ Required | ✅ Eliminado |
| `registro_medico` | ❌ No existe | ❌ Required | ✅ Eliminado |

**Separación Portal Externo vs Sistema Interno**:
- **Portal Externo** (radicación): Solo datos médicos básicos (fechas, diagnóstico, IPS/EPS)
- **Sistema Interno** (auditoría): Valores económicos asignados por el auditor

---

## Archivos Modificados

1. **Documentación**:
   - `/docs/07_FRONTEND_FASE1_PORTAL_EXTERNO.md`

2. **Código fuente**:
   - `/frontend/portal-externo/src/schemas/radicacionSchema.ts`
   - `/frontend/portal-externo/src/components/wizard/DatosIncapacidadForm.tsx`

3. **Tests**:
   - `/frontend/portal-externo/src/components/wizard/__tests__/DatosIncapacidadForm.test.tsx`

---

## Próximos Pasos

✅ **COMPLETADO**: Alineación de schema del Paso 3 con backend

**Siguiente**: Implementar **Paso 4** del wizard (Upload de Documentos)

### Especificaciones Paso 4:
- Drag & drop de archivos
- Validación de tipos permitidos (PDF, JPG, PNG)
- Validación de tamaño máximo (5MB por archivo)
- Preview de archivos subidos
- Eliminar archivos antes de envío
- Tipos de documento:
  - Incapacidad médica (requerido)
  - Historia clínica (opcional)
  - Soportes adicionales (opcional)

---

**Autor**: GitHub Copilot  
**Revisado**: ✅ 2026-01-15  
**Actualizaciones**:
- 2026-01-14: Corrección inicial de schema (eliminación campos médico, campos opcionales)
- 2026-01-15: Eliminación de campos económicos (exclusivos de auditoría)
