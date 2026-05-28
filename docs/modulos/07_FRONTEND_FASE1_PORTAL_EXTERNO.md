# Fase 1: Portal Externo - Radicación y Consulta de Incapacidades

**Objetivo**: Portal público para radicación y consulta de incapacidades SIN autenticación.

---

## 📋 Requerimientos Funcionales

### RF-001: Radicación de Incapacidad
**Como** empleado/afiliado  
**Quiero** radicar una incapacidad médica  
**Para** iniciar el proceso de reclamación sin necesidad de usuario/contraseña

**Criterios de Aceptación**:
- [ ] Formulario intuitivo paso a paso (wizard)
- [ ] Validación en tiempo real de campos
- [ ] Selección de tipo: ARL o SALUD
- [ ] Upload de certificado médico (PDF, max 10MB)
- [ ] Generación de número de radicación único
- [ ] Envío de confirmación por email (opcional)
- [ ] Impresión de comprobante de radicación

### RF-002: Consulta de Estado
**Como** empleado/afiliado  
**Quiero** consultar el estado de mi incapacidad  
**Para** hacer seguimiento sin autenticación

**Criterios de Aceptación**:
- [ ] Búsqueda por número de radicación
- [ ] Búsqueda por documento de identidad + fecha
- [ ] Visualización de timeline de estados
- [ ] Descarga de documentos adjuntos
- [ ] Información de contacto para soporte

---

## 🎨 Diseño UI/UX

### Página Principal
```
┌──────────────────────────────────────────────────┐
│  [LOGO]    Sistema de Incapacidades    [Ayuda]  │
├──────────────────────────────────────────────────┤
│                                                  │
│        Gestión de Incapacidades Médicas         │
│                                                  │
│  ┌────────────────┐   ┌────────────────┐        │
│  │  Radicar       │   │   Consultar    │        │
│  │  Incapacidad   │   │   Estado       │        │
│  │                │   │                │        │
│  │  [Nuevo Icon]  │   │  [Search Icon] │        │
│  └────────────────┘   └────────────────┘        │
│                                                  │
│  Pasos del proceso:                              │
│  1. Radicación → 2. Auditoría → 3. Pago         │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Formulario de Radicación (Wizard 5 pasos)

**Paso 1: Tipo de Incapacidad**
```
Seleccione el tipo de incapacidad:

○ ARL (Accidente de trabajo / Enfermedad laboral)
○ SALUD (Enfermedad general / Maternidad)

[Cancelar]  [Siguiente →]
```

**Paso 2: Datos del Solicitante**
```
Tipo de documento: [Dropdown: CC, CE, PA, etc.]
Número de documento: [__________]
Nombres completos: [__________]
Apellidos completos: [__________]
Email: [__________] (opcional)
Teléfono: [__________]

[← Atrás]  [Siguiente →]
```

**Paso 3: Datos de la Incapacidad**
```
Fecha de inicio: [DD/MM/YYYY] (requerido)
Fecha de fin: [DD/MM/YYYY] (requerido)
Días totales: [Auto-calculado]

Diagnóstico CIE-10: [__________] (opcional, máx 10 caracteres)
Descripción del diagnóstico: [Textarea] (opcional, máx 500 caracteres)

IPS: [__________] (opcional, Institución Prestadora de Salud)
EPS: [__________] (opcional, Entidad Promotora de Salud)

[← Atrás]  [Siguiente →]
```

**Paso 4: Datos Específicos**

*Si es ARL:*
```
Empresa: [Búsqueda con autocomplete]
NIT: [Auto-completado]
Cargo: [__________]
Fecha de ingreso: [DD/MM/YYYY]

¿Está asociada a un siniestro? [Sí/No]
  Si sí → Número de siniestro: [__________]

[← Atrás]  [Siguiente →]
```

*Si es SALUD:*
```
Número de póliza: [__________]
Tipo de póliza: [Individual/Familiar/Colectiva]

[← Atrás]  [Siguiente →]
```

**Paso 5: Documentos Adjuntos**
```
Certificado médico (obligatorio):
┌────────────────────────────────┐
│  [📄 Arrastre archivo aquí]   │
│  o haga clic para seleccionar  │
│  PDF, JPG, PNG - Máx 10MB      │
└────────────────────────────────┘

Documentos adicionales (opcional):
- Historia clínica
- Fórmula médica
- Otros soportes

[← Atrás]  [Radicar Incapacidad]
```

**Confirmación**
```
✅ Incapacidad radicada exitosamente

Número de radicación: INC-SALUD-2026-001234

Guarde este número para consultas futuras.

Timeline estimado:
• Radicada: Hoy
• En auditoría: 1-2 días hábiles
• Respuesta: 5-10 días hábiles

[Descargar comprobante PDF]  [Consultar estado]  [Radicar otra]
```

### Consulta de Estado

```
┌──────────────────────────────────────────────────┐
│  Consultar Estado de Incapacidad                 │
├──────────────────────────────────────────────────┤
│                                                  │
│  Opción 1: Por número de radicación              │
│  Número: [INC-____________]  [Buscar]            │
│                                                  │
│  ─── O ───                                       │
│                                                  │
│  Opción 2: Por documento de identidad            │
│  Tipo doc: [CC ▼]  Número: [__________]         │
│  Fecha incapacidad: [DD/MM/YYYY]  [Buscar]      │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Resultado de Búsqueda**
```
┌──────────────────────────────────────────────────┐
│  Incapacidad INC-SALUD-2026-001234               │
├──────────────────────────────────────────────────┤
│  Solicitante: Juan Pérez García                  │
│  Tipo: SALUD - Enfermedad general                │
│  Período: 15/01/2026 - 22/01/2026 (7 días)      │
│  Estado actual: EN_AUDITORIA                     │
│                                                  │
│  Timeline:                                        │
│  ✅ Radicada: 15/01/2026 10:30 AM                │
│  🔄 En auditoría: 15/01/2026 2:45 PM            │
│  ⏳ Pendiente aprobación                         │
│  ⏳ Pendiente pago                               │
│                                                  │
│  Documentos:                                      │
│  📄 Certificado médico (150KB)  [Descargar]     │
│  📄 Historia clínica (220KB)  [Descargar]       │
│                                                  │
│  Observaciones:                                  │
│  Ninguna por el momento                          │
│                                                  │
│  [Imprimir]  [Volver]                           │
└──────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitectura de Componentes

### Estructura de Carpetas
```
frontend-portal-externo/
├── public/
│   └── logo.svg
├── src/
│   ├── components/
│   │   ├── ui/              # Componentes base (Shadcn/ui)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   └── card.tsx
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── PageContainer.tsx
│   │   ├── radicacion/
│   │   │   ├── WizardRadicacion.tsx
│   │   │   ├── Paso1TipoIncapacidad.tsx
│   │   │   ├── Paso2DatosSolicitante.tsx
│   │   │   ├── Paso3DatosIncapacidad.tsx
│   │   │   ├── Paso4DatosEspecificos.tsx
│   │   │   ├── Paso5Documentos.tsx
│   │   │   └── ConfirmacionRadicacion.tsx
│   │   ├── consulta/
│   │   │   ├── FormularioConsulta.tsx
│   │   │   ├── ResultadoBusqueda.tsx
│   │   │   ├── TimelineEstados.tsx
│   │   │   └── ListaDocumentos.tsx
│   │   └── shared/
│   │       ├── FileUploader.tsx
│   │       ├── AutocompleteCIE10.tsx
│   │       ├── BusquedaEmpresa.tsx
│   │       └── LoadingSpinner.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── RadicacionPage.tsx
│   │   └── ConsultaPage.tsx
│   ├── services/
│   │   ├── api.ts              # Axios instance
│   │   ├── incapacidadService.ts
│   │   ├── empresaService.ts
│   │   ├── documentoService.ts
│   │   └── catalogoService.ts
│   ├── hooks/
│   │   ├── useRadicacion.ts
│   │   ├── useConsulta.ts
│   │   └── useFileUpload.ts
│   ├── schemas/
│   │   ├── radicacionSchema.ts  # Zod schemas
│   │   └── consultaSchema.ts
│   ├── types/
│   │   ├── incapacidad.ts
│   │   ├── documento.ts
│   │   └── api.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Colores Principales
- Azul principal (#003087 o similar): Usado en logotipo, encabezados y llamadas a acción, evocando solidez financiera.[2]
- Blanco (#FFFFFF): Fondo predominante para legibilidad y secciones clave.[4]
- Gris claro (#F5F5F5 o neutros): En separadores y textos secundarios.[2]

## Colores Secundarios
- Verde ocasional (#00A651): En iconos de éxito o seguros de vida, para resaltar beneficios.[6]

---
_______________
## 🔌 Integración con Backend

### Endpoints Utilizados

#### 1. Radicación de Incapacidad
```typescript
POST /api/v1/incapacidades

Request:
{
  "tipo": "ARL" | "SALUD",
  "empleado_id": "uuid",  // Si es ARL
  "empresa_id": "uuid",   // Si es ARL
  "afiliado_id": "uuid",  // Si es SALUD
  "fecha_inicio": "2026-01-15",
  "fecha_fin": "2026-01-22",
  "dias_totales": 7,
  "diagnostico_cie10": "J02.9",
  "descripcion_diagnostico": "Faringitis aguda",
  "eps": "EPS Sura",
  "ips": "Clínica del Norte",
  "prioridad": "NORMAL"
}

Response 201:
{
  "id": "uuid",
  "numero": "INC-SALUD-2026-001234",
  "estado": "RADICADA",
  "created_at": "2026-01-15T10:30:00Z",
  ...
}
```

#### 2. Upload de Documentos
```typescript
POST /api/v1/documentos/upload
Content-Type: multipart/form-data

FormData:
- file: File
- incapacidad_id: uuid
- tipo_documento: "INCAPACIDAD_MEDICA"

Response 201:
{
  "documento": {
    "id": "uuid",
    "nombre_archivo": "certificado.pdf",
    ...
  },
  "url_descarga": "http://..."
}
```

#### 3. Consulta de Incapacidad
```typescript
GET /api/v1/incapacidades?numero={numero}
// o
GET /api/v1/incapacidades?documento={doc}&fecha={fecha}

Response 200:
{
  "items": [
    {
      "id": "uuid",
      "numero": "INC-SALUD-2026-001234",
      "estado": "EN_AUDITORIA",
      "timeline": [...],
      "documentos": [...],
      ...
    }
  ],
  "total": 1
}
```

#### 4. Búsqueda de Empresas (autocomplete)
```typescript
GET /api/v1/empresas?search={query}&limit=10

Response 200:
{
  "items": [
    {
      "id": "uuid",
      "razon_social": "Constructora ABC",
      "nit": "900123456-1"
    }
  ]
}
```

#### 5. Catálogo CIE-10 (autocomplete)
```typescript
GET /api/v1/catalogos/cie10?search={query}&limit=20

Response 200:
[
  {
    "codigo": "J02.9",
    "descripcion": "Faringitis aguda no especificada"
  }
]
```_______________

---

## ✅ Validaciones del Formulario

### Validaciones con Zod

```typescript
// schemas/radicacionSchema.ts
import { z } from 'zod';

export const paso2Schema = z.object({
  tipo_documento: z.enum(['CC', 'CE', 'PA', 'TI']),
  numero_documento: z.string()
    .min(6, 'Mínimo 6 dígitos')
    .max(15, 'Máximo 15 dígitos')
    .regex(/^[0-9]+$/, 'Solo números'),
  nombres: z.string()
    .min(3, 'Mínimo 3 caracteres')
    .max(100),
  apellidos: z.string()
    .min(3, 'Mínimo 3 caracteres')
    .max(100),
  email: z.string()
    .email('Email inválido')
    .optional()
    .or(z.literal('')),
  telefono: z.string()
    .regex(/^[0-9]{10}$/, 'Debe tener 10 dígitos')
});

export const paso3Schema = z.object({
  fecha_inicio: z.date(),
  fecha_fin: z.date(),
  diagnostico_cie10: z.string()
    .regex(/^[A-Z][0-9]{2}\.[0-9]$/, 'Formato CIE-10 inválido'),
  descripcion_diagnostico: z.string()
    .min(10, 'Mínimo 10 caracteres')
    .max(500),
  nombre_medico: z.string().min(5),
  ips: z.string().min(3),
  eps: z.string().min(3)
}).refine(data => data.fecha_fin >= data.fecha_inicio, {
  message: "Fecha fin debe ser mayor o igual a fecha inicio",
  path: ["fecha_fin"]
});
```

### Validaciones de Negocio

- **Fechas**: Fecha inicio no puede ser futura > 1 mes
- **Días totales**: Máximo 180 días continuos
- **Documentos**: Al menos certificado médico obligatorio
- **Empresa (ARL)**: Debe existir en BD y estar activa
- **Afiliado (SALUD)**: Póliza debe estar vigente

---

## 🧪 Testing

### Tests Unitarios (Vitest)
```typescript
// Ejemplo: WizardRadicacion.test.tsx
describe('WizardRadicacion', () => {
  it('debe avanzar al siguiente paso al hacer clic en Siguiente', () => {
    render(<WizardRadicacion />);
    
    const tipoARLRadio = screen.getByLabelText(/ARL/);
    fireEvent.click(tipoARLRadio);
    
    const btnSiguiente = screen.getByText(/Siguiente/);
    fireEvent.click(btnSiguiente);
    
    expect(screen.getByText(/Datos del Solicitante/)).toBeInTheDocument();
  });
});
```

### Tests de Integración (Playwright)
```typescript
// e2e/radicacion.spec.ts
test('flujo completo de radicación', async ({ page }) => {
  await page.goto('/radicar');
  
  // Paso 1
  await page.click('text=SALUD');
  await page.click('text=Siguiente');
  
  // Paso 2
  await page.selectOption('[name="tipo_documento"]', 'CC');
  await page.fill('[name="numero_documento"]', '1234567890');
  // ...
  
  // Verificar confirmación
  await expect(page.locator('text=/INC-SALUD-/')).toBeVisible();
});
```

---

## 📦 Dependencias Principales

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.0",
    "react-hook-form": "^7.49.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.0",
    "lucide-react": "^0.300.0",
    "date-fns": "^3.0.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/node": "^20.10.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "vitest": "^1.1.0",
    "@testing-library/react": "^14.1.0",
    "playwright": "^1.40.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.0"
  }
}
```

---

## 🎯 Criterios de Aceptación Final

### Funcionales
- [x] Formulario de radicación funcional con 5 pasos
- [x] Validaciones en tiempo real
- [x] Upload de archivos hasta 10MB
- [x] Consulta por número o documento
- [x] Visualización de timeline de estados
- [x] Descarga de documentos adjuntos

### No Funcionales
- [x] Tiempo de carga < 3 segundos
- [x] Responsive en móvil, tablet y desktop
- [x] Accesibilidad WCAG 2.1 nivel AA
- [x] Compatibilidad: Chrome, Firefox, Safari, Edge
- [x] Tests unitarios > 70% coverage
- [x] Tests E2E para flujos críticos

### UX
- [x] Diseño intuitivo y profesional
- [x] Feedback visual en cada acción
- [x] Mensajes de error claros
- [x] Loading states apropiados
- [x] Confirmación de acciones importantes

---

## 📝 Documentación de Apoyo

### Para el Desarrollador
- Storybook de componentes
- Guía de estilos (Figma/Adobe XD)
- OpenAPI/Swagger del backend
- Guía de contribución

### Para el Usuario Final
- Manual de usuario (radicación)
- FAQ
- Video tutorial (2-3 minutos)
- Soporte por chat/email