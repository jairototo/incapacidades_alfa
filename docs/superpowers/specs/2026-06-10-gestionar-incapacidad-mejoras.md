# Spec: Mejoras de gestión de incapacidades — bandeja de pendientes + vista gestionar

**Fecha:** 2026-06-10  
**Rama:** `iniciando_desarrollo_para_produccion`  
**Estado:** Aprobado

---

## Contexto

Tras implementar el flujo unificado de promoción `pre-incapacidad → incapacidad`, existen cuatro brechas de usabilidad en el sistema interno que necesitan resolverse:

1. La columna "Empleado" en la bandeja de pendientes muestra vacío cuando el empleado no existe en la BD (el dato crudo está solo en `pre_incapacidad`).
2. La vista de gestión no muestra las validaciones que se detectaron durante la promoción.
3. El tab de Auditoría no da contexto rápido de la incapacidad — el auditor tiene que cambiar de tab.
4. El tab "Detalle Completo" debe convertirse en el panel de validaciones.

---

## Cambios requeridos

### Cambio 1 — Backend: fallback de empleado y empresa en `/incapacidades/pendientes`

**Archivo:** `app/api/v1/endpoints/incapacidades.py` + `app/schemas/incapacidad.py` + `app/services/incapacidad_service.py`

**Problema:** `IncapacidadPendienteResponse` hereda de `IncapacidadInDB`, que solo tiene `empleado` (objeto relacional). Si `empleado_id` es NULL, la columna queda vacía. Mismo problema para `empresa` cuando viene de pre-radicación sin match en BD.

**Solución:**

Agregar dos campos opcionales a `IncapacidadPendienteResponse`:

```python
class EmpleadoFallback(BaseModel):
    nombres: str
    numero_documento: str

class EmpresaFallback(BaseModel):
    nit: str
    nombre: str

class IncapacidadPendienteResponse(IncapacidadInDB):
    dias_desde_radicacion: int
    dias_en_estado_actual: int
    empleado_fallback: Optional[EmpleadoFallback] = None
    empresa_fallback: Optional[EmpresaFallback] = None
```

En `listar_incapacidades_pendientes` (endpoint), después de construir la lista de resultados, para cada incapacidad con `empleado_id IS NULL`, hacer un SELECT a `pre_incapacidad` por `incapacidad_id = incapacidad.id` y extraer `empleado_nombres`, `empleado_numero_documento`, `empresa_nit`, `empresa_nombre`. Poblar `empleado_fallback` y `empresa_fallback` cuando aplique.

La lógica de fallback debe hacerse en el endpoint (no en el service) mediante un batch query único contra `pre_incapacidad` para no introducir N+1.

---

### Cambio 2 — Backend: nuevo endpoint `GET /incapacidades/{id}/validaciones`

**Archivo:** `app/api/v1/endpoints/incapacidades.py` + `app/db/repositories/validation_inconsistencia_repository.py`

**Problema:** No existe endpoint para consultar los issues de `validation_inconsistencia` asociados a una incapacidad desde el sistema interno.

**Solución:**

Nuevo método en `ValidationInconsistenciaRepository`:

```python
async def get_by_incapacidad(self, incapacidad_id: UUID) -> list[ValidationInconsistencia]:
    """Retorna issues con incapacidad_id = incapacidad_id OR
       cuyo pre_incapacidad.incapacidad_id = incapacidad_id."""
    # Subquery: pre_incapacidad_ids cuyo incapacidad_id coincide
    subq = select(PreIncapacidad.id).where(PreIncapacidad.incapacidad_id == incapacidad_id)
    query = select(ValidationInconsistencia).where(
        or_(
            ValidationInconsistencia.incapacidad_id == incapacidad_id,
            ValidationInconsistencia.pre_incapacidad_id.in_(subq),
        )
    ).order_by(ValidationInconsistencia.fecha_deteccion)
    result = await self.db.execute(query)
    return result.scalars().all()
```

Nuevo schema de respuesta:

```python
class ValidacionesResponse(BaseModel):
    issues: list[ValidationInconsistenciaRead]
    has_errors: bool
    has_fraud_alert: bool
    total: int
```

Nuevo endpoint:

```
GET /api/v1/incapacidades/{incapacidad_id}/validaciones
Response: ValidacionesResponse
Auth: INCAPACIDAD_READ (AUDITOR, APROBADOR, ADMIN)
```

---

### Cambio 3 — Frontend: columna "Empleado" en bandeja de pendientes

**Archivo:** `src/pages/incapacidades/PendientesPage.tsx` + `src/types/incapacidad.ts`

Actualizar el type:

```ts
interface IncapacidadPendiente extends Incapacidad {
  dias_desde_radicacion: number
  dias_en_estado_actual: number
  empleado_fallback?: { nombres: string; numero_documento: string } | null
  empresa_fallback?: { nit: string; nombre: string } | null
}
```

Actualizar la columna "Empleado / Afiliado":

- `empleado` presente → comportamiento actual
- `!empleado && empleado_fallback` → mostrar `empleado_fallback.nombres` + `empleado_fallback.numero_documento` con badge pequeño gris `"Sin ficha"` al lado
- Ninguno → mostrar `—`

Igual para la columna "Empresa": si `!empresa && empresa_fallback` → mostrar `empresa_fallback.nombre` + `NIT: empresa_fallback.nit` con badge `"Sin ficha"`.

---

### Cambio 4 — Frontend: strip de contexto en tab Auditoría

**Archivo:** `src/pages/incapacidades/GestionarPage.tsx`

Agregar fetch de validaciones al `GestionarPage`:

```ts
const { data: validaciones } = useQuery({
  queryKey: ['incapacidad', id, 'validaciones'],
  queryFn: () => incapacidadService.getValidaciones(id!),
  enabled: !!id,
})
```

Extraer `hasFraudAlert = validaciones?.has_fraud_alert ?? false`.

Al inicio del `TabsContent value="auditoria"`, antes del `AuditoriaFormulario`, insertar un `IncapacidadContextStrip`:

```
┌──────────────────────────────────────────────────────────────────┐
│ [Empleado: Pedro Promo · CC 7777777]  [Empresa: Acme · NIT 9010] │
│ [CIE-10: M54.5 · Lumbalgia]  [01 jun → 07 jun · 7 días]         │
└──────────────────────────────────────────────────────────────────┘
```

El bloque "Empleado" tiene borde **ámbar** si `!incapacidad.empleado` (no está en BD) y borde **rojo** con ícono `AlertTriangle` si además `hasFraudAlert`.

El componente `IncapacidadContextStrip` se crea en `src/components/incapacidades/IncapacidadContextStrip.tsx`.

Props:
```ts
interface IncapacidadContextStripProps {
  incapacidad: Incapacidad
  hasFraudAlert: boolean
  empleadoFallback?: { nombres: string; numero_documento: string } | null
}
```

Texto compacto: `text-sm`, padding `p-3`, sin cards grandes, fondo `bg-slate-50`.

---

### Cambio 5 — Frontend: tab "Validaciones" (renombrado desde "Detalle Completo")

**Archivos:** `src/pages/incapacidades/GestionarPage.tsx` + nuevo `src/components/incapacidades/ValidacionesPanel.tsx`

Renombrar el `TabsTrigger` de `value="detalle"` → label **"Validaciones"**. Reemplazar `<IncapacidadDetalle>` en ese tab por `<ValidacionesPanel>`.

`ValidacionesPanel` recibe `{ issues: ValidationInconsistencia[], isLoading: boolean }` y renderiza:

**Sección 1 — Alertas/Problemas** (primero):
- Agrupa por `severidad`: ERROR (rojo), WARNING (ámbar), INFO (azul)
- Por cada issue: una fila compacta con ícono de severidad, `codigo` en `font-mono text-xs`, `descripcion`, y si tiene `campo_afectado` → badge gris
- Si no hay issues → muestra `"Sin issues detectados"` en verde

**Sección 2 — Categorías sin problemas** (después):
- Para cada categoría `[FIELD_VALIDATION, BUSINESS_RULE, FRAUD_ALERT, INTEGRATION_CHECK]` que no tenga issues → mostrar fila verde `✓ [Categoría] — sin problemas`
- Para cada categoría que sí tenga issues → no aparece en esta sección (ya aparece arriba)

**Nuevo type** en `src/types/incapacidad.ts`:
```ts
interface ValidationIssue {
  id: string
  categoria: 'FIELD_VALIDATION' | 'BUSINESS_RULE' | 'FRAUD_ALERT' | 'INTEGRATION_CHECK'
  severidad: 'ERROR' | 'WARNING' | 'INFO'
  codigo: string
  descripcion: string
  campo_afectado?: string | null
  valor_encontrado?: string | null
  valor_esperado?: string | null
  fecha_deteccion: string
}

interface ValidacionesResponse {
  issues: ValidationIssue[]
  has_errors: boolean
  has_fraud_alert: boolean
  total: number
}
```

**Nuevo método** en `incapacidadService.ts`:
```ts
async getValidaciones(id: string): Promise<ValidacionesResponse>
// GET /api/v1/incapacidades/{id}/validaciones
```

---

## Archivos a crear/modificar

| Archivo | Tipo |
|---------|------|
| `app/schemas/incapacidad.py` | Modificar — agregar `EmpleadoFallback`, `EmpresaFallback`, campos a `IncapacidadPendienteResponse` |
| `app/db/repositories/validation_inconsistencia_repository.py` | Modificar — agregar `get_by_incapacidad` |
| `app/schemas/validation_inconsistencia.py` | Modificar — agregar `ValidacionesResponse` |
| `app/api/v1/endpoints/incapacidades.py` | Modificar — fallback en pendientes + nuevo endpoint validaciones |
| `src/types/incapacidad.ts` | Modificar — agregar tipos fallback y validaciones |
| `src/services/incapacidadService.ts` | Modificar — agregar `getValidaciones` |
| `src/pages/incapacidades/PendientesPage.tsx` | Modificar — columna empleado/empresa con fallback |
| `src/pages/incapacidades/GestionarPage.tsx` | Modificar — fetch validaciones, strip en audit tab, renombrar tab |
| `src/components/incapacidades/IncapacidadContextStrip.tsx` | Crear |
| `src/components/incapacidades/ValidacionesPanel.tsx` | Crear |

---

## Qué NO cambia

- `AuditoriaFormulario` — sin cambios funcionales
- `HistorialTimeline` — sin cambios
- `DocumentosViewer` — sin cambios
- Schema de BD — sin migraciones
- `IncapacidadDetalle` — se desusa en este tab pero no se borra (puede usarse en otros contextos)
