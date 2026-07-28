# Módulo Administrativo Empresas/Empleados — Diseño Frontend (sistema-interno)

**Fecha**: 2026-07-28
**Branch**: iniciando_desarrollo_para_produccion
**Alcance de este documento**: Frontend únicamente (Fases 5–8 de la matriz original: rutas/guards, UI de Empresas con panel de gráficas, UI de Empleados, carga masiva y navegación cruzada). Depende del contrato de API fijado en el spec y plan de backend:
- `docs/superpowers/specs/2026-07-27-rbac-empresas-empleados-backend-design.md`
- `docs/superpowers/plans/2026-07-27-rbac-empresas-empleados-backend.md`

## 0. Contexto y estado actual verificado

- App: `apps/frontend/sistema-interno` (React + TypeScript, Vite, Tailwind v3.4.19, shadcn/ui, `@tanstack/react-query`, `@tanstack/react-table`, `recharts@^3.7.0` ya instalado y en uso).
- Ruta `/empresas` ya existe como stub (`router/index.tsx:128-138`), `ProtectedRoute allowedRoles={[RolUsuario.ADMIN]}`, renderiza un placeholder `<div>`.
- No existe ninguna ruta `/empleados`, ni `empleadoService.ts`, ni `types/empleado.ts` — se construyen desde cero.
- `empresaService.ts` es de solo lectura (`list`, `getById`, `search`); necesita `create`/`update`/`regenerarPassword`/`getAnalitica`.
- Patrón CRUD de referencia: `src/pages/admin/AuditoresPage.tsx` + `src/services/auditorService.ts` — `useState` local para el formulario, `useMutation` de React Query por acción, error inline (`<p className="text-sm text-red-600">`, NO toast), `window.confirm()` para acciones destructivas, un único `Dialog` reusado para crear/editar (`editing` alterna título/campos).
- `DataTable.tsx` (`@tanstack/react-table`) solo tiene `getCoreRowModel()` — sin paginación/orden/filtro integrados. `AuditoresPage` usa una `Table` shadcn manual en vez de `DataTable` cuando necesita una columna de acciones condicionales; seguimos ese mismo patrón aquí.
- `authStore.ts`: `useHasRole(roles)` / `useCanPerform(action)` con un mapa `permissions: Record<string, string[]>` de strings punteados (`'incapacidad.read'`, etc.) que debe reflejar a mano el `PermissionChecker.PERMISSIONS` del backend (no hay contrato compartido entre frontend/backend hoy).
- `types/enums.ts`: `RolUsuario` **no tiene `LIQUIDADOR`** — el backend lo agregó en este mismo trabajo (branch `iniciando_desarrollo_para_produccion`, plan de backend Task 1); debe agregarse aquí también.
- Ejemplo de gráfica de referencia: `src/components/dashboard/charts/TendenciaMensualLineChart.tsx` — wrapper `Card`/`CardHeader`/`CardTitle`/`CardContent`, early return en estado vacío, `ResponsiveContainer width="100%" height={300}`, `CartesianGrid strokeDasharray="3 3" className="stroke-muted"`, `Tooltip` con variables CSS (`hsl(var(--background))`, `hsl(var(--border))`), colores de serie ya definidos, `Legend`.
- No existe patrón de panel colapsable con librería (`Collapsible`/`Accordion` de shadcn no están en uso); el único precedente es el expand/collapse manual de `src/components/layout/Sidebar.tsx` (estado local `expandedItems`, iconos `ChevronDown`/`ChevronRight`).
- No existe ningún precedente de carga de archivos (`type="file"`, `FormData`, `multipart/form-data`) en todo `sistema-interno` — se construye desde cero. `src/lib/api.ts` es una instancia axios con `Content-Type: application/json` por defecto; las peticiones de carga masiva deben sobreescribir ese header por petición.

## 1. Restricción transversal

**No se modifican estilos, tipografía, ni tokens de diseño existentes.** Todo componente nuevo reutiliza los componentes shadcn/ui, clases Tailwind y patrones visuales ya establecidos (los mismos `Card`, `Table`, `Dialog`, `Button`, colores de gráfica, tratamiento de estados de carga/vacío) que ya usan `AuditoresPage.tsx` y `components/dashboard/charts/*.tsx`. Ninguna tarea de este documento introduce una paleta, fuente o sistema de espaciado nuevo.

## 2. Estructura de rutas y archivos

### Rutas (`src/router/index.tsx`)
- Reemplazar el stub de `/empresas` (líneas 128-138) por la página real, siguiendo el mismo bloque anidado que ya usa `/usuarios` (líneas 152-162): `ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR]}` → `AppShell` → `{ index: true, element: <EmpresasPage /> }`.
- Agregar `/empleados` con el mismo patrón (no existe hoy).
- Ambas rutas gatean solo por **lectura** a nivel de ruta (las tres roles pueden entrar); la distinción de escritura ADMIN/AUDITOR se hace a nivel de botón con `useCanPerform`, no a nivel de ruta.

### Archivos nuevos
| Archivo | Responsabilidad |
|---|---|
| `src/types/empleado.ts` | Tipo `Empleado`, espejo de `types/empresa.ts` |
| `src/services/empleadoService.ts` | CRUD + `getPlantilla` + `validarCargaMasiva` + `confirmarCargaMasiva` |
| `src/pages/admin/EmpresasPage.tsx` | Listado + filtros + panel de analítica + modales |
| `src/pages/admin/EmpleadosPage.tsx` | Listado + filtros + modales + botón carga masiva |
| `src/components/empresas/AnaliticaPanel.tsx` | Panel colapsable, orquesta las 2 gráficas |
| `src/components/empresas/TopEmpresasChart.tsx` | Gráfica 1: barras horizontales |
| `src/components/empresas/TendenciaRadicacionesChart.tsx` | Gráfica 2: línea/área mensual |
| `src/components/empleados/CargaMasivaWizard.tsx` | Dialog de 3 pasos |
| `src/components/shared/TablePagination.tsx` | Paginación anterior/siguiente reutilizable |

### Archivos modificados
| Archivo | Cambio |
|---|---|
| `src/services/empresaService.ts` | Agregar `create`, `update`, `regenerarPassword`, `getAnalitica` |
| `src/types/enums.ts` | Agregar `LIQUIDADOR` a `RolUsuario` |
| `src/store/authStore.ts` | Agregar entradas de `LIQUIDADOR` y ampliar `AUDITOR` en el mapa `permissions` |
| `src/router/index.tsx` | Reemplazar stub `/empresas`, agregar `/empleados` |

## 3. Mapa de permisos frontend (debe reflejar el backend)

| Rol | Entradas nuevas/cambiadas en `authStore.ts`'s `permissions` |
|---|---|
| ADMIN | Sin cambio (`['*']` ya cubre todo) |
| AUDITOR | Se agregan a su arreglo existente: `'empresa.read', 'empleado.read', 'empleado.create', 'empleado.update', 'empleado.delete'` |
| LIQUIDADOR | Nueva entrada: `['empresa.read', 'empleado.read']` |
| READONLY | Sin cambios — por decisión tomada durante la implementación de backend, READONLY perdió el acceso a Empresas/Empleados a nivel de backend; el frontend nunca le otorga estos permisos |

Las acciones de escritura sobre Empresas (`'empresa.create'`, `'empresa.update'`, `'empresa.delete'`, usadas por los botones "Crear empresa"/"Editar"/"Regenerar contraseña") no se agregan a ninguna entrada del mapa salvo la de ADMIN — cubiertas trivialmente por su comodín `'*'`. Se documentan aquí solo para que el nombre exacto del string quede fijo antes de implementar (`useCanPerform('empresa.update')` gatea tanto "Editar" como "Regenerar contraseña", ya que el backend gatea ambos con el mismo `EMPRESA_UPDATE`).

## 4. Página Empresas (`EmpresasPage.tsx`)

**Layout** (`<div className="space-y-4 p-6">`, igual que `AuditoresPage`):
1. `AnaliticaPanel` colapsable arriba de todo (ver §6).
2. Barra de filtros: NIT/razón social (texto), ciudad (texto), departamento (texto) — todos opcionales, combinables, enviados a `empresaService.list({ nit, ciudad, departamento, skip, limit })`. Visible para los tres roles con acceso de lectura.
3. Tabla (shadcn `Table` manual, no `DataTable`, por la columna de acciones condicionales): NIT, razón social, ciudad, departamento, estado, acciones.
4. `TablePagination` al pie.
5. Botón "Crear empresa" — solo si `useCanPerform('empresa.create')` es verdadero (ADMIN). AUDITOR/LIQUIDADOR nunca lo ven (no aplica deshabilitar-con-tooltip, ya que no tienen ninguna vía de acción sobre este recurso).
6. Acciones por fila: "Editar" (ADMIN), "Ver empleados" (los tres roles — navega a `/empleados?empresa_id=<id>`), "Regenerar contraseña" (ADMIN).

**Modal crear/editar** (un solo `Dialog`, estado `editing` alterna modo): campos = todos los del modelo `Empresa` + `email_contacto` (obligatorio en creación, reflejando que el backend ahora lo requiere). Al crear exitosamente, **no cerrar directo al listado** — primero se muestra el modal bloqueante de contraseña (ver abajo); al cerrar ese modal se refresca el listado (`queryClient.invalidateQueries`).

**Modal de revelado de contraseña** (`Dialog` separado, sin `onOpenChange` de auto-cierre — solo se cierra con un botón "Cerrar" habilitado tras marcar un checkbox de confirmación "Copié la contraseña"): muestra `username` + `password` (monoespaciado, seleccionable) con botón de copiar al portapapeles y el aviso "esta contraseña no se mostrará de nuevo". Este mismo componente se reutiliza para "Regenerar contraseña".

## 5. Página Empleados (`EmpleadosPage.tsx`)

Mismo shell que `EmpresasPage`: filtros (búsqueda por nombres/apellidos/documento, selector de empresa con opción "Todas las empresas", prellenado desde `?empresa_id=` si se llega vía el enlace "Ver empleados"), tabla, paginación. Botones "Crear empleado" y "Cargar masivo" gateados por `useCanPerform('empleado.create')` (ADMIN/AUDITOR; LIQUIDADOR nunca los ve).

**Modal crear/editar**: mismo patrón de `Dialog` único. Campos = modelo `Empleado` **menos** `cuenta_bancaria`/`banco`/`tipo_cuenta` (excluidos también aquí, igual que en backend).

## 6. Panel de analítica (`AnaliticaPanel.tsx`)

- Colapsable con estado local + `localStorage` (clave `analitica-empresas-collapsed`), patrón manual (como `Sidebar.tsx`), sin nueva dependencia de `Collapsible`.
- Encabezado: título "Analítica de empresas" + subtítulo "Top 10 y tendencia de los últimos 12 meses" + botón chevron.
- Cuerpo (expandido): grid de 2 columnas en escritorio (`grid-cols-1 lg:grid-cols-2`), apilado en pantallas angostas — responsividad solo por CSS.
- Un único `useQuery(['empresas-analitica'], () => empresaService.getAnalitica())` alimenta ambas gráficas (una sola petición, igual que el payload combinado del backend).
- Estados: `isLoading` → skeleton (reutilizar el tratamiento de carga que ya usan las gráficas de `dashboard/charts`, no inventar uno nuevo); vacío (`top_empresas.length === 0`) → "No hay datos para mostrar"; error → mensaje inline + botón "Reintentar" (`refetch()`).

**`TopEmpresasChart.tsx`**: `BarChart` horizontal (recharts `layout="vertical"`), una sola tonalidad secuencial (reutilizar el color primario ya usado en `dashboard/charts`, no una paleta nueva), `YAxis` con `tickFormatter` que trunca razón social larga con elipsis, `Tooltip` con razón social completa + NIT + conteo formateado `toLocaleString('es-CO')`, mismo wrapper `Card`/`ResponsiveContainer`.

**`TendenciaRadicacionesChart.tsx`**: `LineChart` (o `AreaChart`), eje X = `periodo` formateado `MMM YYYY` en español, eje Y = `total`, una sola serie, mismo estilo de Card/tooltip/leyenda ya establecido.

## 7. Carga masiva de empleados (`CargaMasivaWizard.tsx`)

`Dialog` de 3 pasos secuenciales, sin saltos permitidos, con botón "Volver" para retroceder:

1. **Subir**: enlace "Descargar plantilla" (`empleadoService.getPlantilla()` → descarga de blob) + `<input type="file" accept=".xlsx">` (sin precedente en el proyecto, se construye desde cero) + botón "Validar" que llama `empleadoService.validarCargaMasiva(file)` (`FormData`, sobreescribiendo `Content-Type` por petición).
2. **Resultados**: tabla de errores `{fila, columna, mensaje}` (si hay) + resumen (`total_filas`, `validas`, `con_error`); botón "Confirmar carga" habilitado solo si `validas > 0`, llama `empleadoService.confirmarCargaMasiva(file)` reenviando el mismo archivo en estado (sin token de validación, igual que el backend).
3. **Confirmación**: resumen `insertadas`/`con_error` + tabla de errores de inserción si los hay; botón "Cerrar" cierra el wizard e invalida la query del listado de Empleados.

## 8. Navegación cruzada Empresas ↔ Empleados

Botón "Ver empleados" en una fila de Empresa: `navigate('/empleados?empresa_id=' + empresa.id)`. `EmpleadosPage` lee `useSearchParams()` al montar y prellena el filtro/selector de empresa si el parámetro está presente.

## 9. Pruebas

Vitest, siguiendo las convenciones ya existentes en `sistema-interno` (a confirmar el detalle exacto de estructura de archivos de test al momento de escribir el plan de implementación). Cobertura mínima 70%, por convención del proyecto.

- `EmpresasPage`/`EmpleadosPage`: render con cada rol, verificar presencia/ausencia de botones de crear/editar/regenerar.
- Modal de contraseña: verificar que no se puede cerrar sin marcar el checkbox de confirmación.
- `CargaMasivaWizard`: mockear las tres llamadas de servicio, verificar transición entre pasos y renderizado de la tabla de errores.
- Mapa de permisos: verificar que `useCanPerform` devuelve el booleano correcto para las nuevas acciones por rol (incluye el caso LIQUIDADOR y el caso READONLY sin acceso).
- Navegación cruzada: verificar que `EmpleadosPage` prellena el filtro de empresa cuando llega con `?empresa_id=`.

## 10. Fuera de alcance de este documento

- Cualquier cambio al backend — el contrato de API ya está fijo (ver spec/plan de backend referenciados en el encabezado).
- Cambios a `portal-externo` (aplicación separada, con su propia versión de Tailwind/Zod — no se toca).
- Aplicar la migración de backfill de Usuario (Task 7 del plan de backend) — sigue pendiente de confirmación manual, independiente del frontend.
