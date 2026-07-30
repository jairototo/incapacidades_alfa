/**
 * AuditoriaPrevisionalPage — Pantalla más grande y compleja del módulo
 * Previsionales (Task 5.5): el flujo de auditoría de UNA incapacidad,
 * registro a registro. Un auditor la usa para: revisar las 19 señales
 * AB-AT ya evaluadas (Task 3.3/4.2), editar el único campo ALFA que le
 * pertenece (`dia_181_alfa`), avalar/no avalar, y separar una fila mal
 * reportada en dos (Duplicar).
 *
 * Endpoints consumidos (`previsionalesService`, Task 4.2):
 *   GET   /previsionales/incapacidades/{id}/senales   — obtenerSenales
 *   PATCH /previsionales/incapacidades/{id}           — patchIncapacidad
 *   POST  /previsionales/incapacidades/{id}/aval       — registrarAval
 *   POST  /previsionales/incapacidades/{id}/duplicar   — duplicarIncapacidad
 *
 * --- Decisión de arquitectura: NO existe un GET individual --------------
 * El plan de Task 5.5 pedía verificar si hay un `GET
 * /previsionales/incapacidades/{id}` antes de decidir cómo se carga la
 * incapacidad. Se revisaron los dos únicos routers que registran rutas
 * bajo `/previsionales/incapacidades` en el backend:
 *
 *   - `app/api/v1/endpoints/previsionales/auditoria.py`: solo expone
 *     `GET .../senales`, `PATCH /{id}`, `POST .../aval`,
 *     `POST .../duplicar`. Ninguna de esas 4 rutas devuelve la fila
 *     completa por sí sola (PATCH/aval/duplicar sí devuelven
 *     `IncapacidadPrevisionalResponse`, pero solo como resultado de una
 *     escritura, no como consulta).
 *   - `app/api/v1/endpoints/previsionales/lotes.py`: el único GET que
 *     devuelve `IncapacidadPrevisionalResponse` es
 *     `GET /previsionales/lotes/{lote_id}/incapacidades` (lista completa
 *     de UN lote, sin filtro por incapacidad_id individual).
 *
 * Conclusión verificada (no adivinada): NO existe un endpoint de consulta
 * de una incapacidad individual. La opción (a) del brief ("agregar un
 * método mínimo si el endpoint existe") queda descartada por inexistente
 * -- inventar un endpoint no es parte de esta tarea de frontend. Se toma
 * la opción (b): `?loteId=` es OBLIGATORIO para que esta pantalla pueda
 * cargar cualquier dato. Se listan las incapacidades del lote
 * (`listarIncapacidadesDelLote`, ya usado por `RadicacionLotePage`) y se
 * busca la fila por id en el cliente -- lo que de paso da gratis los datos
 * para la navegación registro a registro (punto 2 del brief). Sin
 * `loteId` la pantalla no intenta adivinar ni deja un panel en blanco:
 * muestra un mensaje explícito explicando por qué no puede cargar nada.
 *
 * --- Navegación registro a registro --------------------------------------
 * Se excluyen las filas `es_duplicado_interno=true` de la lista de
 * navegación (Anterior/Siguiente): son artefactos administrativos creados
 * por "Duplicar" en esta misma pantalla, no filas reales reportadas por la
 * AFP -- un auditor recorriendo el lote registro a registro no debería
 * aterrizar en ellas por accidente. Si la incapacidad actual SÍ es un
 * duplicado interno (se llega por navegación directa, p.ej. justo después
 * de crearlo), igual se muestra su detalle completo -- solo no participa
 * de Anterior/Siguiente porque no forma parte de esa secuencia.
 */
import { useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ChevronLeft, ChevronRight, Copy, Loader2, Save } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { AvalActions } from '@/components/previsionales/AvalActions';
import { SenalesPrevisionalesPanel } from '@/components/previsionales/SenalesPrevisionalesPanel';
import { previsionalesService } from '@/services/previsionales';
import type { IncapacidadPrevisional } from '@/types/previsional';
import { formatDate } from '@/utils/formatters';

/** Clave base de la lista de incapacidades del lote usada por esta pantalla.
 * Deliberadamente distinta de `previsionales-lote-incapacidades` (usada por
 * `RadicacionLotePage`, que incluye filtros en la clave) y de
 * `previsionales-lote-incapacidades-picker` (usada por
 * `SiniestroManualPage`) -- misma convención de esas dos pantallas: cada
 * consumidor de "lista de incapacidades del lote" tiene su propia clave
 * para no pisarse entre sí.
 */
const LOTE_INCAPACIDADES_KEY = 'previsionales-lote-incapacidades-auditoria';

function extractErrorInfo(error: unknown): { status?: number; detail?: string } {
  const response = (error as { response?: { status?: number; data?: { detail?: string } } })
    ?.response;
  return { status: response?.status, detail: response?.data?.detail };
}

// Zod v3 (sistema-interno). Ambas fechas obligatorias por el brief; se
// agrega además que fecha_final >= fecha_inicial -- validación obvia de
// consistencia de datos, no un requisito documentado del backend, pero
// evitar un rango invertido en el cliente es más útil que dejar que el
// servidor lo rechace (o peor, lo acepte silenciosamente si no lo valida).
const duplicarSchema = z
  .object({
    fecha_inicial: z.string().min(1, 'La fecha inicial es obligatoria'),
    fecha_final: z.string().min(1, 'La fecha final es obligatoria'),
  })
  .refine((v) => !v.fecha_inicial || !v.fecha_final || v.fecha_final >= v.fecha_inicial, {
    message: 'La fecha final debe ser igual o posterior a la fecha inicial',
    path: ['fecha_final'],
  });
type DuplicarForm = z.infer<typeof duplicarSchema>;

export function AuditoriaPrevisionalPage() {
  const { incapacidadId } = useParams<{ incapacidadId: string }>();
  const [searchParams] = useSearchParams();
  const loteId = searchParams.get('loteId') ?? undefined;
  const navigate = useNavigate();

  const listaKey = useMemo(() => [LOTE_INCAPACIDADES_KEY, loteId] as const, [loteId]);

  const {
    data: incapacidadesLote = [],
    isLoading: isLoadingLista,
    isError: isErrorLista,
  } = useQuery({
    queryKey: listaKey,
    queryFn: () => previsionalesService.listarIncapacidadesDelLote(loteId!),
    enabled: !!loteId,
  });

  const incapacidad = useMemo(
    () => incapacidadesLote.find((inc) => inc.id === incapacidadId),
    [incapacidadesLote, incapacidadId]
  );

  const navList = useMemo(
    () => incapacidadesLote.filter((inc) => !inc.es_duplicado_interno),
    [incapacidadesLote]
  );
  const navIndex = navList.findIndex((inc) => inc.id === incapacidadId);
  const prevInc = navIndex > 0 ? navList[navIndex - 1] : undefined;
  const nextInc = navIndex !== -1 && navIndex < navList.length - 1 ? navList[navIndex + 1] : undefined;

  const goTo = (id: string) => navigate(`/previsionales/incapacidades/${id}/auditoria?loteId=${loteId}`);

  // Sin loteId no hay ningún endpoint que devuelva esta incapacidad (ver
  // docstring del módulo) -- mensaje explícito en vez de un panel en
  // blanco o un intento fallido de fetch.
  if (!loteId) {
    return (
      <div className="space-y-4">
        <h1 className="text-xl font-bold text-slate-900">Auditoría de Incapacidad</h1>
        <Alert variant="destructive">
          <AlertTitle>Falta el contexto del lote</AlertTitle>
          <AlertDescription>
            Esta pantalla necesita el parámetro <code>?loteId=</code> para poder cargar la
            incapacidad: el backend no expone una consulta individual por incapacidad, solo el
            listado de incapacidades de un lote. Vuelve al panel de radicación del lote y usa el
            enlace "Auditar" de la fila correspondiente.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (isLoadingLista) {
    return <div className="py-8 text-center text-sm text-slate-500">Cargando incapacidad...</div>;
  }

  if (isErrorLista) {
    return (
      <Alert variant="destructive">
        <AlertTitle>No se pudo cargar el lote</AlertTitle>
        <AlertDescription>Verifica el enlace o intenta nuevamente.</AlertDescription>
      </Alert>
    );
  }

  if (!incapacidad) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Incapacidad no encontrada</AlertTitle>
        <AlertDescription>
          No se encontró la incapacidad {incapacidadId} en el lote {loteId}.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">
            Auditoría — {incapacidad.identificacion ?? incapacidad.id}
          </h1>
          <p className="text-sm text-slate-500">
            Radicado: {incapacidad.radicado ?? '-'} · Lote: {loteId}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {navIndex !== -1 && (
            <span className="text-xs text-slate-500" data-testid="nav-posicion">
              Registro {navIndex + 1} de {navList.length}
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            disabled={!prevInc}
            onClick={() => prevInc && goTo(prevInc.id)}
            data-testid="btn-anterior"
          >
            <ChevronLeft className="mr-1 h-4 w-4" />
            Anterior
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={!nextInc}
            onClick={() => nextInc && goTo(nextInc.id)}
            data-testid="btn-siguiente"
          >
            Siguiente
            <ChevronRight className="ml-1 h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* `key={incapacidad.id}` remonta este subárbol al navegar entre
          registros: todo su estado local (dia_181_alfa en edición, diálogo
          de duplicar, resultado de la última mutation) se reinicia solo,
          sin necesidad de useEffects manuales de "reset on id change". */}
      <IncapacidadAuditoriaDetalle
        key={incapacidad.id}
        incapacidad={incapacidad}
        listaKey={listaKey}
        onIrA={goTo}
      />
    </div>
  );
}

interface IncapacidadAuditoriaDetalleProps {
  incapacidad: IncapacidadPrevisional;
  listaKey: readonly [string, string | undefined];
  onIrA: (incapacidadId: string) => void;
}

function IncapacidadAuditoriaDetalle({
  incapacidad,
  listaKey,
  onIrA,
}: IncapacidadAuditoriaDetalleProps) {
  const queryClient = useQueryClient();
  const [diaAlfa, setDiaAlfa] = useState(incapacidad.dia_181_alfa ?? '');
  const [duplicarOpen, setDuplicarOpen] = useState(false);
  const [duplicado, setDuplicado] = useState<IncapacidadPrevisional | null>(null);

  const { data: senales = [], isLoading: isLoadingSenales } = useQuery({
    queryKey: ['previsionales-senales', incapacidad.id],
    queryFn: () => previsionalesService.obtenerSenales(incapacidad.id),
  });

  const updateCachedIncapacidad = (updated: IncapacidadPrevisional) => {
    queryClient.setQueryData<IncapacidadPrevisional[]>(listaKey, (old) =>
      old ? old.map((i) => (i.id === updated.id ? updated : i)) : old
    );
  };

  const patchMutation = useMutation({
    mutationFn: () =>
      previsionalesService.patchIncapacidad(incapacidad.id, { dia_181_alfa: diaAlfa || null }),
    onSuccess: updateCachedIncapacidad,
  });

  const avalMutation = useMutation({
    mutationFn: (body: { aval: 'SI' | 'NO'; motivo?: string }) =>
      previsionalesService.registrarAval(incapacidad.id, body),
    onSuccess: updateCachedIncapacidad,
  });

  const duplicarMutation = useMutation({
    mutationFn: (body: { fecha_inicial: string; fecha_final: string }) =>
      previsionalesService.duplicarIncapacidad(incapacidad.id, body),
    onSuccess: (nueva) => {
      queryClient.setQueryData<IncapacidadPrevisional[]>(listaKey, (old) =>
        old ? [...old, nueva] : old
      );
      setDuplicado(nueva);
      setDuplicarOpen(false);
    },
  });

  const {
    register: registerDuplicar,
    handleSubmit: handleSubmitDuplicar,
    reset: resetDuplicar,
    formState: { errors: duplicarErrors },
  } = useForm<DuplicarForm>({
    resolver: zodResolver(duplicarSchema),
    defaultValues: { fecha_inicial: '', fecha_final: '' },
  });

  const abrirDuplicar = () => {
    setDuplicado(null);
    resetDuplicar();
    setDuplicarOpen(true);
  };

  const onSubmitDuplicar = (values: DuplicarForm) => {
    duplicarMutation.mutate(values);
  };

  const patchError = patchMutation.isError ? extractErrorInfo(patchMutation.error) : null;
  const avalError = avalMutation.isError ? extractErrorInfo(avalMutation.error) : null;
  const duplicarError = duplicarMutation.isError ? extractErrorInfo(duplicarMutation.error) : null;

  return (
    <>
      {/* Datos generales de la fila */}
      <Card className="p-4">
        <dl className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm md:grid-cols-4">
          <div>
            <dt className="text-slate-500">Fecha inicial</dt>
            <dd className="font-medium">
              {incapacidad.fecha_inicial ? formatDate(incapacidad.fecha_inicial) : '-'}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Fecha final</dt>
            <dd className="font-medium">
              {incapacidad.fecha_final ? formatDate(incapacidad.fecha_final) : '-'}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Día 181 (AFP)</dt>
            <dd className="font-medium">
              {incapacidad.dia_181_afp ? formatDate(incapacidad.dia_181_afp) : '-'}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Estado</dt>
            <dd className="font-medium">{incapacidad.estado}</dd>
          </div>
        </dl>
      </Card>

      {/* Campo ALFA editable -- único campo real (gap de esquema documentado
          en el backend, ver `IncapacidadPrevisionalPatchRequest`): no se
          agregan inputs para `fecha_crie_alfa`/`observacion_alfa` porque no
          existen como columnas editables. */}
      <Card className="p-4 space-y-3">
        <h2 className="text-sm font-semibold text-slate-800">Día 181 auditado (Alfa)</h2>
        <form
          className="flex flex-wrap items-end gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            patchMutation.mutate();
          }}
        >
          <div className="space-y-1.5">
            <Label htmlFor="dia-181-alfa">dia_181_alfa</Label>
            <Input
              id="dia-181-alfa"
              type="date"
              value={diaAlfa}
              onChange={(e) => setDiaAlfa(e.target.value)}
              disabled={patchMutation.isPending}
            />
          </div>
          <Button type="submit" size="sm" disabled={patchMutation.isPending}>
            {patchMutation.isPending ? (
              <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-1.5 h-4 w-4" />
            )}
            Guardar
          </Button>
          {patchMutation.isSuccess && !patchMutation.isPending && (
            <span className="text-xs text-green-700" data-testid="alfa-guardado">
              Guardado.
            </span>
          )}
        </form>
        {patchError && (
          <Alert variant="destructive">
            <AlertTitle>No se pudo guardar</AlertTitle>
            <AlertDescription>{patchError.detail ?? 'Ocurrió un error inesperado.'}</AlertDescription>
          </Alert>
        )}
        <p className="text-xs text-slate-400">
          Único campo ALFA editable por el auditor — `fecha_crie_alfa` y `observacion_alfa` no
          existen como columnas propias en el backend (gap de esquema documentado).
        </p>
      </Card>

      {/* Señales AB-AT */}
      <Card className="p-4">
        <SenalesPrevisionalesPanel senales={senales} isLoading={isLoadingSenales} />
      </Card>

      {/* Aval */}
      <Card className="p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-slate-800">Aval de auditoría</h2>
          <AvalActions
            aval={incapacidad.aval}
            motivoNoAval={incapacidad.motivo_no_aval}
            isSubmitting={avalMutation.isPending}
            onAvalar={() => avalMutation.mutate({ aval: 'SI' })}
            onNoAvalar={(motivo) => avalMutation.mutate({ aval: 'NO', motivo })}
          />
        </div>
        {avalError && (
          <Alert variant="destructive">
            <AlertTitle>No se pudo registrar el aval</AlertTitle>
            <AlertDescription>{avalError.detail ?? 'Ocurrió un error inesperado.'}</AlertDescription>
          </Alert>
        )}
      </Card>

      {/* Duplicar: separar una fila mal reportada en 2+ incapacidades */}
      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800">Separar fila mal reportada</h2>
          <Button variant="outline" size="sm" onClick={abrirDuplicar} data-testid="btn-duplicar">
            <Copy className="mr-1.5 h-4 w-4" />
            Duplicar
          </Button>
        </div>
        <p className="text-xs text-slate-500">
          Crea un nuevo registro (`es_duplicado_interno=true`) a partir de esta fila, con un
          rango de fechas propio, cuando la AFP reportó dos incapacidades reales en una sola fila
          del excel.
        </p>
        {duplicado && (
          <Alert data-testid="duplicar-confirmacion">
            <AlertTitle>Se creó un registro duplicado</AlertTitle>
            <AlertDescription className="flex flex-wrap items-center gap-2">
              <span>Nuevo registro creado correctamente.</span>
              <Button variant="link" className="h-auto p-0" onClick={() => onIrA(duplicado.id)}>
                Ir al duplicado
              </Button>
            </AlertDescription>
          </Alert>
        )}
      </Card>

      <Dialog open={duplicarOpen} onOpenChange={setDuplicarOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Duplicar incapacidad</DialogTitle>
            <DialogDescription>
              Define el rango de fechas del nuevo registro separado de esta fila.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitDuplicar(onSubmitDuplicar)} className="space-y-3" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="dup-fecha-inicial">Fecha inicial</Label>
              <Input
                id="dup-fecha-inicial"
                type="date"
                disabled={duplicarMutation.isPending}
                {...registerDuplicar('fecha_inicial')}
              />
              {duplicarErrors.fecha_inicial && (
                <p className="text-xs text-destructive">{duplicarErrors.fecha_inicial.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="dup-fecha-final">Fecha final</Label>
              <Input
                id="dup-fecha-final"
                type="date"
                disabled={duplicarMutation.isPending}
                {...registerDuplicar('fecha_final')}
              />
              {duplicarErrors.fecha_final && (
                <p className="text-xs text-destructive">{duplicarErrors.fecha_final.message}</p>
              )}
            </div>
            {duplicarError && (
              <Alert variant="destructive">
                <AlertTitle>No se pudo duplicar</AlertTitle>
                <AlertDescription>
                  {duplicarError.detail ?? 'Ocurrió un error inesperado.'}
                </AlertDescription>
              </Alert>
            )}
            <DialogFooter>
              <Button type="submit" disabled={duplicarMutation.isPending}>
                {duplicarMutation.isPending ? 'Duplicando...' : 'Duplicar'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
