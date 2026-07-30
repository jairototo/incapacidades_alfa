/**
 * RadicacionLotePage — Panel de radicación: pantalla principal a la que
 * llega un auditor justo después de cargar un lote (Task 5.2). Muestra el
 * detalle del lote, la tabla de sus incapacidades con resaltado visual de
 * señales de calidad de datos, controles de filtro, y las acciones de lote
 * (actualizar / crear siniestros / exportar ARPIS).
 *
 * Endpoints consumidos (Task 4.1, `previsionalesService`):
 *   GET  /previsionales/lotes/{loteId}                    — obtenerLote
 *   GET  /previsionales/lotes/{loteId}/incapacidades       — listarIncapacidadesDelLote
 *   GET  /previsionales/lotes/{loteId}/arpis.xlsx          — exportarArpis (ArpisExportButton)
 *   POST /previsionales/lotes/{loteId}/actualizar          — [GAP] devuelve 501 a propósito
 *
 * Paginación: esta tabla NO pagina -- renderiza todas las incapacidades del
 * lote de una vez. A diferencia de listados no acotados como
 * Empresas/Empleados (que usan `TablePagination` con skip/limit de
 * servidor), un lote previsional es por definición un solo excel cargado de
 * una vez, acotado en tamaño (~200 filas típicamente, ver
 * `CargaLotePage.test.tsx`/docs de Fase 5). Server-side pagination no
 * aportaría nada aquí y complicaría el cálculo de resaltado, que necesita
 * ver todas las filas para que el auditor pueda triage-ar el lote completo.
 *
 * "Crear Siniestros": el plan describe el mecanismo real como "el usuario
 * crea siniestros en ARPIS (externo) o los registra manualmente" (Task 4.4,
 * `POST /previsionales/siniestros`) -- no existe un endpoint que "cree
 * siniestros en lote" desde este botón. Se implementa como una navegación a
 * la pantalla de registro manual de Task 5.4 (`/previsionales/siniestros/nuevo`),
 * pasando `loteId` como query param por si esa pantalla quiere usarlo como
 * contexto (p.ej. para volver al lote al terminar). Esta es una decisión de
 * interpretación, no un mapeo 1:1 obvio -- ver reporte de Task 5.3.
 *
 * "Actualizar lote": el backend documenta este endpoint como un gap
 * conocido (Task 4.1) y devuelve 501 siempre (ver docstring de
 * `actualizar_lote` en `endpoints/previsionales/lotes.py`). El botón existe
 * para fijar el contrato de UI del plan, pero el 501 se trata como una
 * limitación esperada y documentada, no como un error del sistema -- se
 * muestra un mensaje neutro ("Esta función aún no está disponible") en vez
 * del texto de error genérico. `previsionalesService` deliberadamente NO
 * envuelve este endpoint (ver su docstring), así que se llama a `api.post`
 * directamente aquí.
 *
 * "Auditar" (columna Acciones, agregado en Task 5.5): sin este enlace la
 * pantalla de auditoría de Task 5.5
 * (`/previsionales/incapacidades/:incapacidadId/auditoria`) sería
 * inalcanzable desde la UI real -- esta era la única pantalla de la que un
 * auditor llega naturalmente a una incapacidad puntual. Navega pasando
 * `?loteId=` porque esa pantalla depende de él para poder cargar datos (no
 * existe un GET individual por incapacidad en el backend, ver docstring de
 * `AuditoriaPrevisionalPage.tsx`). Usa `row.original.lote_id` (ya viene en
 * `IncapacidadPrevisionalResponse`) en vez de cerrar sobre el `loteId` de
 * la URL de esta pantalla -- así la columna sigue siendo un `ColumnDef`
 * estático de nivel de módulo, sin necesitar convertirla en una fábrica
 * que dependa del componente.
 */
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { FilePlus2, Loader2, RefreshCw } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { DataTable } from '@/components/shared/DataTable';
import { ArpisExportButton } from '@/components/previsionales/ArpisExportButton';
import api from '@/lib/api';
import { previsionalesService } from '@/services/previsionales';
import type { FiltrosIncapacidadesLote, IncapacidadPrevisional } from '@/types/previsional';
import { formatCurrency, formatDate, formatDateTime } from '@/utils/formatters';

const ESTADO_LABELS: Record<string, string> = {
  SIN_SINIESTRO: 'Sin siniestro',
  CON_SINIESTRO: 'Con siniestro',
  EN_AUDITORIA: 'En auditoría',
  AVALADO: 'Avalado',
  NO_AVALADO: 'No avalado',
  LIQUIDADO: 'Liquidado',
  PAGADO: 'Pagado',
};

/**
 * Clases tailwind de fondo de fila por señal, reutilizadas también en la
 * leyenda. Se exporta (Task 5.6) para que `LiquidacionPrevisionalPage`
 * reutilice exactamente el mismo azul de "diferencia de valor" en vez de
 * duplicar el valor del literal -- misma señal visual, misma fuente de
 * verdad, en las dos pantallas donde aplica.
 */
export const HIGHLIGHT_CLASSES = {
  error: 'bg-red-50',
  repetida: 'bg-purple-50',
  sinSiniestro: 'bg-amber-50',
  difValor: 'bg-blue-50',
} as const;

/**
 * Clase de resaltado de una fila. Cuando una incapacidad dispara más de una
 * señal a la vez se muestra solo la de mayor prioridad, en este orden:
 *
 *   1. Error de carga (rojo)      -- el dato de la fila puede ser
 *      inconsistente o incompleto; es la señal más urgente porque puede
 *      invalidar cualquier otra columna calculada de esa misma fila.
 *   2. Repetida (violeta)         -- la fila es un duplicado interno; el
 *      auditor necesita resolver cuál copia es la válida antes de mirar
 *      cualquier otra cosa.
 *   3. Sin siniestro (ámbar)      -- falta `numero_siniestro`; relevante,
 *      pero esperable en muchas filas al inicio del flujo (antes de
 *      "Crear Siniestros"), por eso va después de error/repetida.
 *   4. Diferencia de valor (azul) -- el valor auditado no coincide con el
 *      valor reportado por la AFP; importante, pero no bloquea el resto del
 *      flujo de auditoría de la misma forma que las tres señales previas.
 */
function rowClassName(incapacidad: IncapacidadPrevisional): string {
  if (incapacidad.errores_carga !== null) return HIGHLIGHT_CLASSES.error;
  if (incapacidad.es_duplicado_interno) return HIGHLIGHT_CLASSES.repetida;
  if (incapacidad.numero_siniestro === null) return HIGHLIGHT_CLASSES.sinSiniestro;
  if (incapacidad.diferencia_valor_afp != null && incapacidad.diferencia_valor_afp !== 0) {
    return HIGHLIGHT_CLASSES.difValor;
  }
  return '';
}

function extractErrorInfo(error: unknown): { status?: number; detail?: string } {
  const response = (error as { response?: { status?: number; data?: { detail?: string } } })
    ?.response;
  return { status: response?.status, detail: response?.data?.detail };
}

const columns: ColumnDef<IncapacidadPrevisional>[] = [
  {
    id: 'identificacion',
    header: 'Identificación',
    cell: ({ row }) => (
      <div>
        <div className="font-medium">{row.original.identificacion ?? '-'}</div>
        {row.original.tipo_identificacion && (
          <div className="text-xs text-slate-500">{row.original.tipo_identificacion}</div>
        )}
      </div>
    ),
  },
  {
    accessorKey: 'radicado',
    header: 'Radicado',
    cell: ({ row }) => row.original.radicado ?? '-',
  },
  {
    accessorKey: 'tipo_ingreso',
    header: 'Tipo de ingreso',
    cell: ({ row }) => row.original.tipo_ingreso ?? '-',
  },
  {
    accessorKey: 'fecha_inicial',
    header: 'Fecha inicial',
    cell: ({ row }) => (row.original.fecha_inicial ? formatDate(row.original.fecha_inicial) : '-'),
  },
  {
    accessorKey: 'fecha_final',
    header: 'Fecha final',
    cell: ({ row }) => (row.original.fecha_final ? formatDate(row.original.fecha_final) : '-'),
  },
  {
    accessorKey: 'valor_afp',
    header: 'Valor AFP',
    cell: ({ row }) =>
      row.original.valor_afp != null ? formatCurrency(row.original.valor_afp) : '-',
  },
  {
    accessorKey: 'valor_auditado',
    header: 'Valor auditado',
    cell: ({ row }) =>
      row.original.valor_auditado != null ? formatCurrency(row.original.valor_auditado) : '-',
  },
  {
    accessorKey: 'diferencia_valor_afp',
    header: 'Diferencia',
    cell: ({ row }) => {
      const dif = row.original.diferencia_valor_afp;
      if (dif == null) return '-';
      return (
        <span className={dif !== 0 ? 'font-semibold text-blue-700' : ''}>
          {formatCurrency(dif)}
        </span>
      );
    },
  },
  {
    accessorKey: 'estado',
    header: 'Estado',
    cell: ({ row }) => (
      <Badge variant="outline" className="whitespace-nowrap">
        {ESTADO_LABELS[row.original.estado] ?? row.original.estado}
      </Badge>
    ),
  },
  {
    id: 'senales',
    header: 'Señales',
    cell: ({ row }) => {
      const inc = row.original;
      return (
        <div className="flex flex-wrap gap-1">
          {inc.errores_carga !== null && (
            <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Error</Badge>
          )}
          {inc.es_duplicado_interno && (
            <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100">Repetida</Badge>
          )}
          {inc.numero_siniestro === null && (
            <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">Sin siniestro</Badge>
          )}
          {inc.diferencia_valor_afp != null && inc.diferencia_valor_afp !== 0 && (
            <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">Dif. valor</Badge>
          )}
        </div>
      );
    },
  },
  {
    id: 'acciones',
    header: 'Acciones',
    cell: ({ row }) => (
      <Link
        to={`/previsionales/incapacidades/${row.original.id}/auditoria?loteId=${row.original.lote_id}`}
        className="text-sm font-medium text-blue-700 hover:underline"
      >
        Auditar
      </Link>
    ),
  },
];

export function RadicacionLotePage() {
  const { loteId } = useParams<{ loteId: string }>();
  const navigate = useNavigate();

  const [filtros, setFiltros] = useState<FiltrosIncapacidadesLote>({});

  const {
    data: lote,
    isLoading: isLoadingLote,
    isError: isErrorLote,
  } = useQuery({
    queryKey: ['previsionales-lote', loteId],
    queryFn: () => previsionalesService.obtenerLote(loteId!),
    enabled: !!loteId,
  });

  const {
    data: incapacidades = [],
    isLoading: isLoadingIncapacidades,
  } = useQuery({
    queryKey: ['previsionales-lote-incapacidades', loteId, filtros],
    queryFn: () => previsionalesService.listarIncapacidadesDelLote(loteId!, filtros),
    enabled: !!loteId,
  });

  // POST /previsionales/lotes/{id}/actualizar -- deliberadamente NO envuelto
  // en previsionalesService (ver docstring del servicio): el propio backend
  // advierte que este endpoint es un gap sin lógica real todavía.
  const actualizarMutation = useMutation({
    mutationFn: () => api.post(`/previsionales/lotes/${loteId}/actualizar`),
  });

  const toggleFiltro = (key: keyof FiltrosIncapacidadesLote) => (checked: boolean) => {
    setFiltros((prev) => ({ ...prev, [key]: checked ? true : undefined }));
  };

  const handleCrearSiniestros = () => {
    navigate(`/previsionales/siniestros/nuevo?loteId=${loteId}`);
  };

  const actualizarError = actualizarMutation.isError
    ? extractErrorInfo(actualizarMutation.error)
    : null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">
            {isLoadingLote ? 'Cargando lote...' : lote?.nombre_archivo ?? 'Lote'}
          </h1>
          {loteId && <p className="text-sm text-slate-500">ID del lote: {loteId}</p>}
        </div>

        <div className="flex flex-wrap items-start gap-2">
          <Button variant="outline" onClick={handleCrearSiniestros}>
            <FilePlus2 className="mr-2 h-4 w-4" />
            Crear Siniestros
          </Button>
          <Button
            variant="outline"
            onClick={() => actualizarMutation.mutate()}
            disabled={actualizarMutation.isPending}
          >
            {actualizarMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            Actualizar lote
          </Button>
          {loteId && <ArpisExportButton loteId={loteId} nombreArchivo={lote?.nombre_archivo} />}
        </div>
      </div>

      {actualizarError && actualizarError.status === 501 && (
        <Alert>
          <AlertTitle>Esta función aún no está disponible</AlertTitle>
          <AlertDescription>
            El re-cruce de siniestros sobre un lote ya cargado todavía no tiene una
            implementación en el backend (gap conocido y documentado). Para actualizar los
            siniestros de este lote, usa "Crear Siniestros" o vuelve a cargar el excel más
            reciente desde ARPIS.
          </AlertDescription>
        </Alert>
      )}
      {actualizarError && actualizarError.status !== 501 && (
        <Alert variant="destructive">
          <AlertTitle>No se pudo actualizar el lote</AlertTitle>
          <AlertDescription>
            {actualizarError.detail ?? 'Ocurrió un error inesperado al actualizar el lote.'}
          </AlertDescription>
        </Alert>
      )}

      {isErrorLote && (
        <Alert variant="destructive">
          <AlertTitle>No se pudo cargar el lote</AlertTitle>
          <AlertDescription>Verifica el enlace o intenta nuevamente.</AlertDescription>
        </Alert>
      )}

      {lote && (
        <Card className="p-4">
          <dl className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm md:grid-cols-4">
            <div>
              <dt className="text-slate-500">Estado</dt>
              <dd className="font-medium">{lote.estado}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Fecha de cargue</dt>
              <dd className="font-medium">{formatDateTime(lote.fecha_cargue)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Total de filas</dt>
              <dd className="font-medium">{lote.total_filas}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Total de incapacidades</dt>
              <dd className="font-medium">{lote.total_incapacidades}</dd>
            </div>
          </dl>
        </Card>
      )}

      {/* Leyenda de colores -- misma prioridad documentada en rowClassName arriba. */}
      <Card className="p-3">
        <p className="mb-2 text-xs font-medium text-slate-500">
          Leyenda de resaltado (de mayor a menor prioridad cuando aplica más de una señal)
        </p>
        <div className="flex flex-wrap gap-4 text-xs text-slate-700">
          <span className="flex items-center gap-1.5">
            <span className={`h-3 w-3 rounded border border-red-300 ${HIGHLIGHT_CLASSES.error}`} />
            Error de carga
          </span>
          <span className="flex items-center gap-1.5">
            <span
              className={`h-3 w-3 rounded border border-purple-300 ${HIGHLIGHT_CLASSES.repetida}`}
            />
            Repetida
          </span>
          <span className="flex items-center gap-1.5">
            <span
              className={`h-3 w-3 rounded border border-amber-300 ${HIGHLIGHT_CLASSES.sinSiniestro}`}
            />
            Sin siniestro
          </span>
          <span className="flex items-center gap-1.5">
            <span
              className={`h-3 w-3 rounded border border-blue-300 ${HIGHLIGHT_CLASSES.difValor}`}
            />
            Diferencia de valor
          </span>
        </div>
      </Card>

      {/* Filtros */}
      <Card className="p-3">
        <p className="mb-2 text-xs font-medium text-slate-500">Filtrar por señal</p>
        <div className="flex flex-wrap gap-4 text-sm">
          <label className="flex items-center gap-2">
            <Checkbox
              checked={!!filtros.sin_siniestro}
              onCheckedChange={(checked) => toggleFiltro('sin_siniestro')(checked === true)}
            />
            Sin siniestro
          </label>
          <label className="flex items-center gap-2">
            <Checkbox
              checked={!!filtros.repetidas}
              onCheckedChange={(checked) => toggleFiltro('repetidas')(checked === true)}
            />
            Repetidas
          </label>
          <label className="flex items-center gap-2">
            <Checkbox
              checked={!!filtros.errores}
              onCheckedChange={(checked) => toggleFiltro('errores')(checked === true)}
            />
            Con errores
          </label>
          <label className="flex items-center gap-2">
            <Checkbox
              checked={!!filtros.dif_valor}
              onCheckedChange={(checked) => toggleFiltro('dif_valor')(checked === true)}
            />
            Diferencia de valor
          </label>
        </div>
      </Card>

      <div className="text-sm text-slate-500">
        {isLoadingIncapacidades ? 'Cargando incapacidades...' : `${incapacidades.length} incapacidades`}
      </div>

      <DataTable
        columns={columns}
        data={incapacidades}
        isLoading={isLoadingIncapacidades}
        rowClassName={rowClassName}
        emptyMessage="No hay incapacidades para los filtros seleccionados"
      />
    </div>
  );
}
