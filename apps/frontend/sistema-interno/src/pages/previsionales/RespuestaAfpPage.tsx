/**
 * RespuestaAfpPage — Pantalla final del flujo Previsionales (Task 5.7):
 * genera y descarga el excel de respuesta a la AFP de un lote.
 *
 * Endpoints consumidos (Task 4.3, `previsionalesService`):
 *   GET /previsionales/lotes/{loteId}                    — obtenerLote
 *   GET /previsionales/lotes/{loteId}/incapacidades       — listarIncapacidadesDelLote
 *   GET /previsionales/lotes/{loteId}/respuesta.xlsx      — descargarRespuesta (blob)
 *
 * --- Qué genera realmente este botón ---------------------------------------
 * El backend NO reconstruye un excel desde cero: reabre los bytes del excel
 * ORIGINALMENTE archivado al cargar el lote y le agrega exactamente dos
 * columnas (AVAL, OBSERVACION), emparejando filas por clave de contenido (no
 * por posición) y excluyendo las filas `es_duplicado_interno=true`. Por eso
 * puede fallar con 404 si el lote no existe o no tiene un archivo original
 * archivado (un estado real posible en lotes anteriores a esta funcionalidad,
 * o si el archivo no se persistió por algún motivo), y con 400 si ese archivo
 * archivado no es un excel válido.
 *
 * --- Resumen de disposición (judgment call) ---------------------------------
 * Se incluye un resumen "X de Y incapacidades tienen aval registrado" antes
 * del botón de descarga: es información puramente orientativa (no bloquea la
 * descarga) que ayuda al auditor a notar si está generando la respuesta antes
 * de tiempo -- si nadie ha avalado nada todavía, la respuesta tendría las
 * columnas AVAL/OBSERVACION en blanco para todas las filas, lo cual sería
 * válido pero probablemente prematuro. El conteo se calcula sobre las mismas
 * filas que el backend realmente exporta (excluyendo `es_duplicado_interno`),
 * para que el número que ve el auditor coincida con lo que el excel va a
 * contener.
 *
 * --- Filename ----------------------------------------------------------
 * Seguimos el mismo estilo que `ArpisExportButton.tsx`: prefijo descriptivo +
 * el `nombre_archivo` del lote (sin la extensión original), con `loteId` como
 * respaldo si el lote todavía no cargó.
 *
 * --- Enlaces de salida ---------------------------------------------------
 * Al ser la última pantalla del flujo, se agregan dos enlaces de "qué sigue":
 * volver al panel de radicación del lote (Task 5.3) y empezar un lote nuevo
 * (Task 5.2, `/previsionales/carga`). Es una pantalla deliberadamente
 * delgada -- un botón y un resumen -- así que estos enlaces son la única
 * salida útil una vez descargada la respuesta.
 */
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Download, Loader2 } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { previsionalesService } from '@/services/previsionales';
import { formatDateTime } from '@/utils/formatters';

function extractErrorInfo(error: unknown): { status?: number; detail?: string } {
  const response = (error as { response?: { status?: number; data?: { detail?: string } } })
    ?.response;
  return { status: response?.status, detail: response?.data?.detail };
}

export function RespuestaAfpPage() {
  const { loteId } = useParams<{ loteId: string }>();

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
    queryKey: ['previsionales-lote-incapacidades-respuesta', loteId],
    queryFn: () => previsionalesService.listarIncapacidadesDelLote(loteId!),
    enabled: !!loteId,
  });

  // El excel de respuesta excluye es_duplicado_interno=true (Task 3.4/4.3) --
  // el resumen cuenta solo sobre las filas que el backend realmente exporta.
  const incapacidadesRespuesta = incapacidades.filter((inc) => !inc.es_duplicado_interno);
  const totalRespuesta = incapacidadesRespuesta.length;
  const conAval = incapacidadesRespuesta.filter((inc) => inc.aval != null).length;

  const descargarMutation = useMutation({
    mutationFn: () => previsionalesService.descargarRespuesta(loteId!),
    onSuccess: (blob) => {
      const base = (lote?.nombre_archivo ?? loteId ?? 'lote').replace(/\.xlsx$/i, '');
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `respuesta_afp_${base}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    },
  });

  const descargarError = descargarMutation.isError
    ? extractErrorInfo(descargarMutation.error)
    : null;
  const esNoEncontrado = descargarError?.status === 404;
  const esArchivoInvalido = descargarError?.status === 400;
  const esOtroError = !!descargarError && !esNoEncontrado && !esArchivoInvalido;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">
            {isLoadingLote
              ? 'Cargando lote...'
              : `Respuesta AFP — ${lote?.nombre_archivo ?? 'Lote'}`}
          </h1>
          {loteId && <p className="text-sm text-slate-500">ID del lote: {loteId}</p>}
        </div>

        <Button
          onClick={() => descargarMutation.mutate()}
          disabled={descargarMutation.isPending || !loteId}
        >
          {descargarMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          Descargar respuesta
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

      <Card className="p-4">
        <p className="text-sm text-slate-700">
          {isLoadingIncapacidades
            ? 'Cargando estado de aval...'
            : `${conAval} de ${totalRespuesta} incapacidades tienen aval registrado.`}
        </p>
        {!isLoadingIncapacidades && totalRespuesta > 0 && conAval < totalRespuesta && (
          <p className="mt-1 text-xs text-amber-700">
            Generar la respuesta ahora dejará las columnas AVAL/OBSERVACION en blanco para las
            incapacidades sin aval todavía.
          </p>
        )}
      </Card>

      {descargarMutation.isSuccess && !descargarMutation.isPending && (
        <Alert data-testid="descarga-exitosa">
          <AlertTitle>Respuesta generada</AlertTitle>
          <AlertDescription>La descarga del excel de respuesta se inició.</AlertDescription>
        </Alert>
      )}

      {esNoEncontrado && (
        <Alert variant="destructive">
          <AlertTitle>Lote o archivo original no encontrado</AlertTitle>
          <AlertDescription>
            {descargarError?.detail ??
              'No se encontró el lote o no tiene un archivo original archivado. Verifica que el lote exista y que el excel se haya cargado correctamente.'}
          </AlertDescription>
        </Alert>
      )}

      {esArchivoInvalido && (
        <Alert variant="destructive">
          <AlertTitle>El archivo original archivado no es válido</AlertTitle>
          <AlertDescription>
            {descargarError?.detail ??
              'El excel original archivado para este lote está corrupto o no es un excel válido. Contacta al equipo técnico.'}
          </AlertDescription>
        </Alert>
      )}

      {esOtroError && (
        <Alert variant="destructive">
          <AlertTitle>No se pudo generar la respuesta</AlertTitle>
          <AlertDescription>
            {descargarError?.detail ?? 'Ocurrió un error inesperado al generar la respuesta.'}
          </AlertDescription>
        </Alert>
      )}

      <div className="flex flex-wrap gap-4 border-t border-slate-200 pt-4 text-sm">
        {loteId && (
          <Link
            to={`/previsionales/lotes/${loteId}`}
            className="font-medium text-blue-700 hover:underline"
          >
            Volver al lote
          </Link>
        )}
        <Link to="/previsionales/carga" className="font-medium text-blue-700 hover:underline">
          Cargar un nuevo lote
        </Link>
      </div>
    </div>
  );
}
