/**
 * LiquidacionPrevisionalPage — Pantalla de liquidación de un lote (Task
 * 5.6): dispara la re-liquidación de todas las incapacidades no duplicadas
 * del lote y muestra el resultado agregado por incapacidad.
 *
 * Endpoints consumidos (Task 4.3, `previsionalesService`):
 *   GET  /previsionales/lotes/{loteId}                    — obtenerLote
 *   GET  /previsionales/lotes/{loteId}/incapacidades       — listarIncapacidadesDelLote
 *   POST /previsionales/lotes/{loteId}/liquidar            — liquidarLote
 *
 * --- Gap real de backend: no hay desglose por segmento ---------------------
 * El texto original del plan describe esta pantalla con una
 * `PeriodosBreakdownTable` "segmento a segmento", mostrando `smlmv_aplicado`
 * y si se aplicó el piso, por período, contra el valor de la AFP. Se
 * verificó directamente que ese dato NO se expone: `PeriodoPrevisional`
 * (modelo SQLAlchemy con los campos `smlmv_aplicado`/`valor_segmento`/`ibc`
 * por período) no tiene ningún schema Pydantic de respuesta y solo se usa
 * INTERNAMENTE dentro de `_construir_filas_arpis` en
 * `app/api/v1/endpoints/previsionales/lotes.py` para armar el excel ARPIS.
 * No existe un `GET .../periodos` en ningún router. Por eso esta pantalla
 * NO intenta construir una tabla de desglose por segmento -- inventar esa
 * forma sería fabricar datos que el backend no entrega. En su lugar se
 * muestra el agregado por incapacidad que sí existe en
 * `IncapacidadPrevisionalResponse` (`valor_afp`, `valor_auditado`,
 * `diferencia_valor_afp`), con una nota honesta sobre la limitación en vez
 * de filas de relleno.
 *
 * --- Qué hace realmente "Liquidar lote" -------------------------------
 * El servicio recalcula `valor_auditado`/`diferencia_valor_afp` de cada
 * incapacidad NO duplicada del lote, usando los períodos ya persistidos
 * sobre el rango completo reportado por la AFP -- deliberadamente sin
 * recorte por día 181/ventana CRIE (decisión de negocio sin resolver
 * documentada en el propio servicio de backend). Las incapacidades con
 * `es_duplicado_interno=true` quedan fuera del recálculo por diseño, así
 * que sus columnas `valor_auditado`/`diferencia_valor_afp` pueden seguir en
 * `null` incluso después de liquidar -- el placeholder "Pendiente de
 * liquidar" es honesto igual (el valor no se calculó), aunque en ese caso
 * particular nunca se calculará vía este botón.
 */
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { Loader2, RefreshCw } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { DataTable } from '@/components/shared/DataTable';
import { previsionalesService } from '@/services/previsionales';
import type { IncapacidadPrevisional } from '@/types/previsional';
import { formatCurrency, formatDateTime } from '@/utils/formatters';
import { HIGHLIGHT_CLASSES } from './RadicacionLotePage';

function extractErrorInfo(error: unknown): { status?: number; detail?: string } {
  const response = (error as { response?: { status?: number; data?: { detail?: string } } })
    ?.response;
  return { status: response?.status, detail: response?.data?.detail };
}

/** Misma señal/color de "diferencia de valor" que `RadicacionLotePage`. */
function rowClassName(incapacidad: IncapacidadPrevisional): string {
  if (incapacidad.diferencia_valor_afp != null && incapacidad.diferencia_valor_afp !== 0) {
    return HIGHLIGHT_CLASSES.difValor;
  }
  return '';
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
    accessorKey: 'valor_afp',
    header: 'Valor AFP',
    cell: ({ row }) =>
      row.original.valor_afp != null ? formatCurrency(row.original.valor_afp) : '-',
  },
  {
    accessorKey: 'valor_auditado',
    header: 'Valor auditado',
    cell: ({ row }) =>
      row.original.valor_auditado != null ? (
        formatCurrency(row.original.valor_auditado)
      ) : (
        <span className="text-slate-400">Pendiente de liquidar</span>
      ),
  },
  {
    accessorKey: 'diferencia_valor_afp',
    header: 'Diferencia',
    cell: ({ row }) => {
      const dif = row.original.diferencia_valor_afp;
      if (dif == null) return <span className="text-slate-400">Pendiente de liquidar</span>;
      return (
        <span className={dif !== 0 ? 'font-semibold text-blue-700' : ''}>
          {formatCurrency(dif)}
        </span>
      );
    },
  },
];

export function LiquidacionPrevisionalPage() {
  const { loteId } = useParams<{ loteId: string }>();
  const queryClient = useQueryClient();

  // Clave propia de esta pantalla (misma convención que las otras pantallas
  // de Previsionales: cada consumidor de "lista de incapacidades del lote"
  // tiene su propia clave, ver `AuditoriaPrevisionalPage`/`SiniestroManualPage`).
  const incapacidadesKey = ['previsionales-lote-incapacidades-liquidacion', loteId] as const;

  const {
    data: lote,
    isLoading: isLoadingLote,
    isError: isErrorLote,
  } = useQuery({
    queryKey: ['previsionales-lote', loteId],
    queryFn: () => previsionalesService.obtenerLote(loteId!),
    enabled: !!loteId,
  });

  const { data: incapacidades = [], isLoading: isLoadingIncapacidades } = useQuery({
    queryKey: incapacidadesKey,
    queryFn: () => previsionalesService.listarIncapacidadesDelLote(loteId!),
    enabled: !!loteId,
  });

  const liquidarMutation = useMutation({
    mutationFn: () => previsionalesService.liquidarLote(loteId!),
    onSuccess: () => {
      // El endpoint solo devuelve el conteo -- hay que refrescar la lista
      // para ver los `valor_auditado`/`diferencia_valor_afp` recalculados.
      queryClient.invalidateQueries({ queryKey: incapacidadesKey });
    },
  });

  const liquidarError = liquidarMutation.isError
    ? extractErrorInfo(liquidarMutation.error)
    : null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">
            {isLoadingLote ? 'Cargando lote...' : `Liquidación — ${lote?.nombre_archivo ?? 'Lote'}`}
          </h1>
          {loteId && <p className="text-sm text-slate-500">ID del lote: {loteId}</p>}
        </div>

        <Button
          onClick={() => liquidarMutation.mutate()}
          disabled={liquidarMutation.isPending || !loteId}
        >
          {liquidarMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="mr-2 h-4 w-4" />
          )}
          Liquidar lote
        </Button>
      </div>

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

      {liquidarMutation.isSuccess && !liquidarMutation.isPending && (
        <Alert data-testid="liquidar-resultado">
          <AlertTitle>Liquidación completada</AlertTitle>
          <AlertDescription>
            Se liquidaron {liquidarMutation.data?.liquidadas ?? 0} incapacidades.
          </AlertDescription>
        </Alert>
      )}

      {liquidarError && (
        <Alert variant="destructive">
          <AlertTitle>No se pudo liquidar el lote</AlertTitle>
          <AlertDescription>
            {liquidarError.detail ?? 'Ocurrió un error inesperado al liquidar el lote.'}
          </AlertDescription>
        </Alert>
      )}

      <Alert>
        <AlertTitle>Desglose por segmento no disponible</AlertTitle>
        <AlertDescription>
          El desglose segmento a segmento (SMLMV aplicado, si se aplicó el piso) todavía no se
          expone en ningún endpoint del backend -- aquí se muestra el valor agregado por
          incapacidad. El desglose por segmento estará disponible cuando el backend lo exponga.
        </AlertDescription>
      </Alert>

      <div className="text-sm text-slate-500">
        {isLoadingIncapacidades
          ? 'Cargando incapacidades...'
          : `${incapacidades.length} incapacidades`}
      </div>

      <DataTable
        columns={columns}
        data={incapacidades}
        isLoading={isLoadingIncapacidades}
        rowClassName={rowClassName}
        emptyMessage="No hay incapacidades en este lote"
      />
    </div>
  );
}
