/**
 * SiniestroManualPage — Registro manual de un siniestro previsional (fuera
 * del flujo de importación masiva). Destino de "Crear Siniestros" en
 * `RadicacionLotePage` (Task 5.3), que navega aquí como
 * `/previsionales/siniestros/nuevo?loteId=...` (ver docstring de esa
 * pantalla para el porqué: no existe un endpoint de creación en lote, el
 * mecanismo real es registrar siniestros uno a uno, aquí o en ARPIS).
 *
 * Endpoint consumido: POST /previsionales/siniestros (Task 4.4,
 * `previsionalesService.crearSiniestroManual`).
 *
 * --- Alcance de la vinculación a incapacidad (decisión de esta tarea) -----
 * El backend (ver docstring de `crear_siniestro` en
 * `endpoints/previsionales/siniestros.py`) autocompleta `identificacion`
 * desde `incapacidad_id` cuando se da el segundo y se omite el primero, y
 * rechaza con 400 si ambos se dan y no coinciden. Task 5.3 solo pasa
 * `loteId` en el query string (no `incapacidadId`) -- no hay una pantalla
 * previa que ya tenga una incapacidad puntual seleccionada. Por eso esta
 * pantalla, cuando llega con `loteId`, ofrece un selector que reutiliza
 * `previsionalesService.listarIncapacidadesDelLote` (ya usado por
 * `RadicacionLotePage`) para elegir una incapacidad de ESE lote como
 * referencia: al elegirla se fija `incapacidad_id` y se bloquea el campo
 * `identificacion` con el valor de esa incapacidad (evita que el usuario
 * escriba algo que no coincida y dispare el 400 de arriba). Si no se llega
 * con `loteId`, o el usuario prefiere no vincular, el formulario cae a modo
 * "manual": `identificacion` se escribe a mano y es requerida (mismo 400
 * que el backend documenta como "identificacion es requerida").
 *
 * No se construyó un buscador de incapacidades genérico entre lotes -- eso
 * sería una pantalla propia, desproporcionada para lo que el plan describe
 * como una captura manual liviana; el selector se limita a las
 * incapacidades del lote que ya trajo al usuario aquí.
 *
 * --- Campos que NO existen (gap de esquema documentado en el backend) -----
 * `ciudad`, `departamento`, `eps`, `arl` no son columnas reales de
 * `SiniestroPrevisional` (ver docstring del endpoint) -- no se agregan
 * inputs para ellos. Se deja una nota visible en el formulario en vez de
 * inventar campos que no tienen a dónde ir.
 */
import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { CheckCircle2, Link2, Loader2, Save } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { previsionalesService } from '@/services/previsionales';
import type { SiniestroManualRequest, SiniestroPrevisional } from '@/types/previsional';

const SIN_VINCULAR = '__sin_vincular__';

// ---------------------------------------------------------------------------
// Zod schema (Zod v3 — sistema-interno)
// ---------------------------------------------------------------------------
// `identificacion` se declara opcional aquí a propósito -- su obligatoriedad
// depende de si hay una incapacidad vinculada (ver `onSubmit`), no es una
// regla estática que zod pueda expresar sola sin duplicar el estado del
// selector dentro del schema.
const formSchema = z.object({
  identificacion: z.string().max(50, 'Máximo 50 caracteres').optional(),
  numero_siniestro: z
    .string()
    .min(1, 'El número de siniestro es obligatorio')
    .max(50, 'Máximo 50 caracteres'),
  origen: z.string().max(100, 'Máximo 100 caracteres').optional(),
  estado: z.string().max(50, 'Máximo 50 caracteres').optional(),
  fecha_aviso: z.string().optional(),
  fecha_siniestro: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

/**
 * Extrae `{ status, detail }` de un error axios. Mismo patrón que
 * `extractErrorInfo` en `RadicacionLotePage.tsx`.
 */
function extractErrorInfo(error: unknown): { status?: number; detail?: string } {
  const response = (error as { response?: { status?: number; data?: { detail?: string } } })
    ?.response;
  return { status: response?.status, detail: response?.data?.detail };
}

export function SiniestroManualPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const loteId = searchParams.get('loteId') ?? undefined;

  const [incapacidadIdSeleccionada, setIncapacidadIdSeleccionada] = useState<string>('');
  const [creado, setCreado] = useState<SiniestroPrevisional | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    setError,
    clearErrors,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      identificacion: '',
      numero_siniestro: '',
      origen: '',
      estado: '',
      fecha_aviso: '',
      fecha_siniestro: '',
    },
  });

  // Incapacidades del lote de origen, para el selector de vinculación.
  // Solo se pide si llegamos con `loteId` (ver docstring del módulo).
  const { data: incapacidadesLote = [], isLoading: isLoadingIncapacidades } = useQuery({
    queryKey: ['previsionales-lote-incapacidades-picker', loteId],
    queryFn: () => previsionalesService.listarIncapacidadesDelLote(loteId!),
    enabled: !!loteId,
  });

  const incapacidadSeleccionada = useMemo(
    () => incapacidadesLote.find((inc) => inc.id === incapacidadIdSeleccionada),
    [incapacidadesLote, incapacidadIdSeleccionada]
  );

  const mutation = useMutation({
    mutationFn: (body: SiniestroManualRequest) => previsionalesService.crearSiniestroManual(body),
    onSuccess: (result) => setCreado(result),
  });

  const handleSeleccionIncapacidad = (value: string) => {
    if (value === SIN_VINCULAR) {
      setIncapacidadIdSeleccionada('');
      setValue('identificacion', '');
      clearErrors('identificacion');
      return;
    }
    setIncapacidadIdSeleccionada(value);
    const inc = incapacidadesLote.find((i) => i.id === value);
    setValue('identificacion', inc?.identificacion ?? '');
    clearErrors('identificacion');
  };

  const onSubmit = (values: FormValues) => {
    // Espejo del 400 del backend ("identificacion es requerida"): si no hay
    // incapacidad vinculada, identificacion es obligatoria. Cuando SÍ hay
    // vínculo, el campo ya viene bloqueado con el valor de la incapacidad,
    // así que nunca puede llegar vacío por ese camino.
    if (!incapacidadIdSeleccionada && !values.identificacion?.trim()) {
      setError('identificacion', {
        type: 'manual',
        message: 'La identificación es obligatoria si no vinculas una incapacidad del lote.',
      });
      return;
    }

    mutation.mutate({
      identificacion: values.identificacion?.trim() || undefined,
      numero_siniestro: values.numero_siniestro.trim(),
      origen: values.origen?.trim() || undefined,
      estado: values.estado?.trim() || undefined,
      fecha_aviso: values.fecha_aviso || undefined,
      fecha_siniestro: values.fecha_siniestro || undefined,
      incapacidad_id: incapacidadIdSeleccionada || undefined,
    });
  };

  const handleRegistrarOtro = () => {
    setCreado(null);
    mutation.reset();
    setIncapacidadIdSeleccionada('');
    reset();
  };

  const errorInfo = mutation.isError ? extractErrorInfo(mutation.error) : null;
  const esConflicto = errorInfo?.status === 409;
  const esValidacion = errorInfo?.status === 400;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Registrar Siniestro</h1>
        <p className="mt-1 text-sm text-slate-500">
          Registro manual de un siniestro previsional, fuera de la importación masiva de ARPIS.
        </p>
        {loteId && <p className="text-xs text-slate-500">Lote de origen: {loteId}</p>}
      </div>

      {!creado && (
        <Card className="max-w-xl space-y-4 p-4">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            {/* Vinculación a incapacidad del lote */}
            {loteId && (
              <div className="space-y-1.5 rounded-md border border-slate-200 bg-slate-50 p-3">
                <Label htmlFor="siniestro-incapacidad" className="flex items-center gap-1.5">
                  <Link2 className="h-3.5 w-3.5" />
                  Vincular a una incapacidad del lote (opcional)
                </Label>
                <Select
                  value={incapacidadIdSeleccionada || SIN_VINCULAR}
                  onValueChange={handleSeleccionIncapacidad}
                  disabled={mutation.isPending || isLoadingIncapacidades}
                >
                  <SelectTrigger id="siniestro-incapacidad">
                    <SelectValue placeholder="Sin vincular (registro manual)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={SIN_VINCULAR}>Sin vincular (registro manual)</SelectItem>
                    {incapacidadesLote.map((inc) => (
                      <SelectItem key={inc.id} value={inc.id}>
                        {inc.identificacion ?? 'Sin identificación'} — {inc.radicado ?? 'sin radicado'}{' '}
                        ({inc.estado})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {isLoadingIncapacidades && (
                  <p className="text-xs text-slate-500">Cargando incapacidades del lote...</p>
                )}
                {incapacidadSeleccionada && (
                  <p className="text-xs text-slate-500">
                    La identificación se tomó de esta incapacidad y no se puede editar.
                  </p>
                )}
              </div>
            )}

            {/* Identificación */}
            <div className="space-y-1.5">
              <Label htmlFor="siniestro-identificacion">
                Identificación {!incapacidadIdSeleccionada && <span className="text-destructive">*</span>}
              </Label>
              <Input
                id="siniestro-identificacion"
                type="text"
                disabled={mutation.isPending || !!incapacidadIdSeleccionada}
                readOnly={!!incapacidadIdSeleccionada}
                {...register('identificacion')}
              />
              {errors.identificacion && (
                <p className="text-xs text-destructive">{errors.identificacion.message}</p>
              )}
            </div>

            {/* Número de siniestro */}
            <div className="space-y-1.5">
              <Label htmlFor="siniestro-numero">
                Número de siniestro <span className="text-destructive">*</span>
              </Label>
              <Input
                id="siniestro-numero"
                type="text"
                disabled={mutation.isPending}
                {...register('numero_siniestro')}
              />
              {errors.numero_siniestro && (
                <p className="text-xs text-destructive">{errors.numero_siniestro.message}</p>
              )}
            </div>

            {/* Origen */}
            <div className="space-y-1.5">
              <Label htmlFor="siniestro-origen">Origen</Label>
              <Input
                id="siniestro-origen"
                type="text"
                disabled={mutation.isPending}
                {...register('origen')}
              />
              {errors.origen && <p className="text-xs text-destructive">{errors.origen.message}</p>}
            </div>

            {/* Estado */}
            <div className="space-y-1.5">
              <Label htmlFor="siniestro-estado">Estado</Label>
              <Input
                id="siniestro-estado"
                type="text"
                disabled={mutation.isPending}
                {...register('estado')}
              />
              {errors.estado && <p className="text-xs text-destructive">{errors.estado.message}</p>}
            </div>

            {/* Fechas */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="siniestro-fecha-aviso">Fecha de aviso</Label>
                <Input
                  id="siniestro-fecha-aviso"
                  type="date"
                  disabled={mutation.isPending}
                  {...register('fecha_aviso')}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="siniestro-fecha-siniestro">Fecha del siniestro</Label>
                <Input
                  id="siniestro-fecha-siniestro"
                  type="date"
                  disabled={mutation.isPending}
                  {...register('fecha_siniestro')}
                />
              </div>
            </div>

            <p className="text-xs text-slate-400">
              Ciudad, departamento, EPS y ARL todavía no son campos soportados por el sistema
              (gap de esquema conocido) -- no se capturan aquí.
            </p>

            {esConflicto && (
              <Alert variant="destructive">
                <AlertTitle>Ya existe un siniestro con ese número</AlertTitle>
                <AlertDescription>
                  {errorInfo?.detail ??
                    'Ya existe un siniestro con ese número de siniestro. Verifica el número o busca el registro existente.'}
                </AlertDescription>
              </Alert>
            )}
            {esValidacion && (
              <Alert variant="destructive">
                <AlertTitle>Datos inválidos</AlertTitle>
                <AlertDescription>
                  {errorInfo?.detail ?? 'Revisa los datos del formulario e intenta de nuevo.'}
                </AlertDescription>
              </Alert>
            )}
            {mutation.isError && !esConflicto && !esValidacion && (
              <Alert variant="destructive">
                <AlertTitle>No se pudo registrar el siniestro</AlertTitle>
                <AlertDescription>
                  {errorInfo?.detail ?? 'Ocurrió un error inesperado al registrar el siniestro.'}
                </AlertDescription>
              </Alert>
            )}

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Registrando...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Registrar siniestro
                  </>
                )}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {creado && (
        <Card className="max-w-xl space-y-4 p-4">
          <div className="flex items-center gap-2 text-green-700">
            <CheckCircle2 className="h-5 w-5" />
            <h2 className="text-base font-semibold">Siniestro registrado correctamente</h2>
          </div>

          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
            <div>
              <span className="text-slate-500">Identificación</span>
              <p className="font-medium">{creado.identificacion}</p>
            </div>
            <div>
              <span className="text-slate-500">Número de siniestro</span>
              <p className="font-medium">{creado.numero_siniestro}</p>
            </div>
            {creado.origen && (
              <div>
                <span className="text-slate-500">Origen</span>
                <p className="font-medium">{creado.origen}</p>
              </div>
            )}
            {creado.estado && (
              <div>
                <span className="text-slate-500">Estado</span>
                <p className="font-medium">{creado.estado}</p>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={handleRegistrarOtro}>
              Registrar otro
            </Button>
            {loteId && (
              <Button onClick={() => navigate(`/previsionales/lotes/${loteId}`)}>
                Volver al lote
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
