/**
 * CargaLotePage — Punto de entrada del flujo Previsionales: cargar un lote
 * (excel de la AFP) para que el backend lo decifre (si aplica), valide
 * encabezados, parsee cada fila, segmente, liquide y persista, todo en una
 * sola llamada síncrona (`POST /previsionales/lotes`, ver
 * `previsionalesService.cargarLote`).
 *
 * A diferencia de `CargaMasivaWizard` (empleados), aquí NO existe un
 * endpoint de "validar" separado -- el backend hace todo el trabajo en la
 * misma petición y devuelve el `LotePrevisional` final con sus conteos. Por
 * eso esta pantalla es un formulario de un solo paso, no un wizard.
 *
 * El archivo se maneja como estado local (no registrado en react-hook-form)
 * siguiendo el mismo patrón que `CargaMasivaWizard.tsx` -- evita la
 * complejidad de validar un `FileList` con zod para un campo que de todas
 * formas se valida "a mano" (obligatorio, único). Contraseña y nombre de
 * archivo sí van por react-hook-form + zod, que es donde aporta valor
 * (formato, longitud).
 *
 * La contraseña de la AFP es un valor de formulario de un solo uso: nunca
 * se registra en consola, nunca va en la URL, y nunca entra en un query key
 * de TanStack Query (la carga es un `useMutation`, no un `useQuery`, así
 * que no hay query key que la exponga).
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle2, Loader2, Upload } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { previsionalesService } from '@/services/previsionales';
import type { LotePrevisional } from '@/types/previsional';

// ---------------------------------------------------------------------------
// Zod schema (Zod v3 — sistema-interno)
// ---------------------------------------------------------------------------
// El archivo NO va aquí (ver nota arriba) -- solo los campos de texto.
const formSchema = z.object({
  password: z.string().optional(),
  nombre_archivo: z.string().max(255, 'Máximo 255 caracteres').optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface CargarLoteVariables extends FormValues {
  file: File;
}

/**
 * Extrae un mensaje de error legible de una respuesta axios.
 * Mismo patrón que `extractErrorMessage` en `EmpresasPage.tsx` /
 * el manejo de error en `CreacionSiniestroPage.tsx`: el backend expone
 * `BadRequestException` como `error.response.data.detail`.
 */
function extractErrorMessage(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data
    ?.detail;
  const message = (error as { message?: string })?.message;
  return detail ?? message ?? fallback;
}

export function CargaLotePage() {
  const navigate = useNavigate();

  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [lote, setLote] = useState<LotePrevisional | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: { password: '', nombre_archivo: '' },
  });

  const mutation = useMutation({
    mutationFn: ({ file, password, nombre_archivo }: CargarLoteVariables) =>
      previsionalesService.cargarLote(file, password || undefined, nombre_archivo || undefined),
    onSuccess: (result) => {
      setLote(result);
    },
  });

  const onSubmit = (values: FormValues) => {
    if (!file) {
      setFileError('El archivo es obligatorio.');
      return;
    }
    setFileError(null);
    mutation.mutate({ ...values, file });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] ?? null);
    setFileError(null);
  };

  const handleCargarOtro = () => {
    setLote(null);
    setFile(null);
    setFileError(null);
    mutation.reset();
    reset();
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Upload className="h-5 w-5 text-blue-600" />
          Carga de Lote Previsional
        </h1>
        <p className="text-slate-500 mt-1 text-sm">
          Sube el excel de la AFP para decifrar, validar, liquidar y registrar el lote.
        </p>
      </div>

      {!lote && (
        <Card className="p-4 max-w-xl">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            {/* Archivo */}
            <div className="space-y-1.5">
              <Label htmlFor="lote-archivo">
                Archivo (.xlsx) <span className="text-destructive">*</span>
              </Label>
              <Input
                id="lote-archivo"
                type="file"
                accept=".xlsx"
                onChange={handleFileChange}
                disabled={mutation.isPending}
              />
              {file && <p className="text-xs text-slate-500">Seleccionado: {file.name}</p>}
              {fileError && <p className="text-xs text-destructive">{fileError}</p>}
            </div>

            {/* Contraseña (opcional, archivo cifrado) */}
            <div className="space-y-1.5">
              <Label htmlFor="lote-password">Contraseña del archivo (si está cifrado)</Label>
              <Input
                id="lote-password"
                type="password"
                autoComplete="off"
                disabled={mutation.isPending}
                {...register('password')}
              />
              {errors.password && (
                <p className="text-xs text-destructive">{errors.password.message}</p>
              )}
            </div>

            {/* Nombre de archivo (opcional, override) */}
            <div className="space-y-1.5">
              <Label htmlFor="lote-nombre-archivo">Nombre de archivo (opcional)</Label>
              <Input
                id="lote-nombre-archivo"
                type="text"
                placeholder="Por defecto se usa el nombre del archivo subido"
                disabled={mutation.isPending}
                {...register('nombre_archivo')}
              />
              {errors.nombre_archivo && (
                <p className="text-xs text-destructive">{errors.nombre_archivo.message}</p>
              )}
            </div>

            {mutation.isError && (
              <Alert variant="destructive">
                <AlertTitle>No se pudo cargar el lote</AlertTitle>
                <AlertDescription>
                  {extractErrorMessage(mutation.error, 'Ocurrió un error inesperado al cargar el lote.')}
                </AlertDescription>
              </Alert>
            )}

            <div className="flex justify-end pt-2">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Cargando lote...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Cargar lote
                  </>
                )}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {lote && (
        <Card className="p-4 max-w-xl space-y-4">
          <div className="flex items-center gap-2 text-green-700">
            <CheckCircle2 className="h-5 w-5" />
            <h2 className="text-base font-semibold">Lote cargado correctamente</h2>
          </div>

          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
            <div>
              <span className="text-slate-500">Archivo</span>
              <p className="font-medium">{lote.nombre_archivo}</p>
            </div>
            <div>
              <span className="text-slate-500">Estado</span>
              <p className="font-medium">{lote.estado}</p>
            </div>
            <div>
              <span className="text-slate-500">Total de filas</span>
              <p className="font-medium">{lote.total_filas}</p>
            </div>
            <div>
              <span className="text-slate-500">Total de incapacidades</span>
              <p className="font-medium">{lote.total_incapacidades}</p>
            </div>
            {lote.observaciones && (
              <div className="col-span-2">
                <span className="text-slate-500">Observaciones</span>
                <p>{lote.observaciones}</p>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={handleCargarOtro}>
              Cargar otro lote
            </Button>
            <Button onClick={() => navigate(`/previsionales/lotes/${lote.id}`)}>
              Ver detalle del lote
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
