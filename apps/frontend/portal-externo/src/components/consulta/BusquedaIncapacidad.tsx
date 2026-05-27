/**
 * Componente de búsqueda de incapacidades.
 * 
 * Permite consultar incapacidades por dos métodos:
 * - Número de radicación (ej: INC-ARL-20260117-0001)
 * - Documento de identidad (número + tipo)
 * 
 * Características:
 * - Toggle entre modos de búsqueda
 * - Validación en tiempo real con Zod
 * - Integración con React Query hooks
 * - UI responsive con shadcn/ui
 * - Manejo de estados loading/error/success
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/RadioGroup';
import { Select } from '@/components/ui/Select';
import { useConsultarPorNumero, useConsultarPorDocumento } from '@/hooks/useConsultaIncapacidad';
import {
  consultaPorNumeroSchema,
  consultaPorDocumentoSchema,
  TIPOS_DOCUMENTO,
  type ConsultaPorNumeroFormData,
  type ConsultaPorDocumentoFormData,
} from '@/schemas/consultaSchema';
import type { ConsultaIncapacidadResponse, TipoDocumento } from '@/types/consulta';
import { Search, FileText, IdCard, AlertCircle, Loader2 } from 'lucide-react';

export interface BusquedaIncapacidadProps {
  /**
   * Callback ejecutado cuando se encuentra una incapacidad.
   * @param incapacidad - Datos completos de la incapacidad encontrada
   */
  onResultado: (incapacidad: ConsultaIncapacidadResponse) => void;
}

type ModoBusqueda = 'numero' | 'documento';

/**
 * Componente principal de búsqueda de incapacidades.
 * 
 * @example
 * ```tsx
 * <BusquedaIncapacidad 
 *   onResultado={(incapacidad) => {
 *     console.log('Incapacidad encontrada:', incapacidad.numero);
 *     setIncapacidadSeleccionada(incapacidad);
 *   }}
 * />
 * ```
 */
export function BusquedaIncapacidad({ onResultado }: BusquedaIncapacidadProps) {
  const [modo, setModo] = useState<ModoBusqueda>('numero');

  // Formulario para búsqueda por número
  const formNumero = useForm<ConsultaPorNumeroFormData>({
    resolver: zodResolver(consultaPorNumeroSchema),
    defaultValues: { numero: '' },
  });

  // Formulario para búsqueda por documento
  const formDocumento = useForm<ConsultaPorDocumentoFormData>({
    resolver: zodResolver(consultaPorDocumentoSchema),
    defaultValues: {
      documento: '',
      tipo_documento: 'CC' as TipoDocumento,
    },
  });

  // Estado para controlar cuándo ejecutar las queries
  const [ejecutarBusquedaNumero, setEjecutarBusquedaNumero] = useState(false);
  const [ejecutarBusquedaDocumento, setEjecutarBusquedaDocumento] = useState(false);

  // Hooks de React Query
  const {
    data: resultadoNumero,
    isLoading: loadingNumero,
    error: errorNumero,
    refetch: refetchNumero,
  } = useConsultarPorNumero(
    formNumero.watch('numero'),
    ejecutarBusquedaNumero
  );

  const {
    data: resultadoDocumento,
    isLoading: loadingDocumento,
    error: errorDocumento,
    refetch: refetchDocumento,
  } = useConsultarPorDocumento(
    formDocumento.watch('documento'),
    formDocumento.watch('tipo_documento'),
    ejecutarBusquedaDocumento
  );

  // Efecto para manejar resultados exitosos
  useEffect(() => {
    if (resultadoNumero) {
      onResultado(resultadoNumero);
      formNumero.reset();
      setEjecutarBusquedaNumero(false);
    }
  }, [resultadoNumero, onResultado, formNumero]);

  useEffect(() => {
    if (resultadoDocumento) {
      onResultado(resultadoDocumento);
      formDocumento.reset({ documento: '', tipo_documento: 'CC' });
      setEjecutarBusquedaDocumento(false);
    }
  }, [resultadoDocumento, onResultado, formDocumento]);

  // Handlers
  const handleBuscarPorNumero = formNumero.handleSubmit(() => {
    setEjecutarBusquedaNumero(true);
    refetchNumero();
  });

  const handleBuscarPorDocumento = formDocumento.handleSubmit(() => {
    setEjecutarBusquedaDocumento(true);
    refetchDocumento();
  });

  const handleCambiarModo = (nuevoModo: string) => {
    setModo(nuevoModo as ModoBusqueda);
    // Resetear formularios y errores al cambiar de modo
    formNumero.reset();
    formDocumento.reset({ documento: '', tipo_documento: 'CC' });
    setEjecutarBusquedaNumero(false);
    setEjecutarBusquedaDocumento(false);
  };

  const isLoading = loadingNumero || loadingDocumento;
  const error = modo === 'numero' ? errorNumero : errorDocumento;

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-6 w-6" />
          Consultar Incapacidad
        </CardTitle>
        <CardDescription>
          Busca tu incapacidad por número de radicación o documento de identidad
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Toggle de modo de búsqueda */}
        <div className="space-y-3">
          <Label>Buscar por:</Label>
          <RadioGroup
            value={modo}
            onValueChange={handleCambiarModo}
            className="grid grid-cols-2 gap-4"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="numero" id="modo-numero" />
              <Label
                htmlFor="modo-numero"
                className="flex items-center gap-2 cursor-pointer font-normal"
              >
                <FileText className="h-4 w-4" />
                Número de radicación
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <RadioGroupItem value="documento" id="modo-documento" />
              <Label
                htmlFor="modo-documento"
                className="flex items-center gap-2 cursor-pointer font-normal"
              >
                <IdCard className="h-4 w-4" />
                Documento de identidad
              </Label>
            </div>
          </RadioGroup>
        </div>

        {/* Formulario de búsqueda por número */}
        {modo === 'numero' && (
          <form onSubmit={handleBuscarPorNumero} className="space-y-4">
            <div>
              <Input
                label="Número de radicación"
                placeholder="Ej: INC-ARL-20260117-0001"
                error={formNumero.formState.errors.numero?.message}
                helperText="Formato: INC-[TIPO]-[FECHA]-[CONSECUTIVO]"
                {...formNumero.register('numero')}
                disabled={isLoading}
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || !formNumero.formState.isValid}
            >
              {loadingNumero && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {loadingNumero ? 'Buscando...' : 'Buscar'}
            </Button>
          </form>
        )}

        {/* Formulario de búsqueda por documento */}
        {modo === 'documento' && (
          <form onSubmit={handleBuscarPorDocumento} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-1">
                <Label htmlFor="tipo-documento" required>
                  Tipo de documento
                </Label>
                <Select
                  id="tipo-documento"
                  {...formDocumento.register('tipo_documento')}
                  disabled={isLoading}
                  className="mt-1"
                >
                  {TIPOS_DOCUMENTO.map((tipo) => (
                    <option key={tipo} value={tipo}>
                      {tipo === 'CC' && 'Cédula de Ciudadanía'}
                      {tipo === 'CE' && 'Cédula de Extranjería'}
                      {tipo === 'TI' && 'Tarjeta de Identidad'}
                      {tipo === 'PASAPORTE' && 'Pasaporte'}
                      {tipo === 'PEP' && 'PEP'}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="md:col-span-2">
                <Input
                  label="Número de documento"
                  placeholder="Ej: 1234567890"
                  error={formDocumento.formState.errors.documento?.message}
                  {...formDocumento.register('documento')}
                  disabled={isLoading}
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading || !formDocumento.formState.isValid}
            >
              {loadingDocumento && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {loadingDocumento ? 'Buscando...' : 'Buscar'}
            </Button>
          </form>
        )}

        {/* Mensaje de error */}
        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg transition-all">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-red-900">
                No se encontró la incapacidad
              </h4>
              <p className="text-sm text-red-700 mt-1">
                {(error as { response?: { status?: number } })?.response?.status === 404
                  ? 'No existe una incapacidad con los datos proporcionados. Verifica la información e intenta nuevamente.'
                  : 'Ocurrió un error al realizar la búsqueda. Por favor, intenta nuevamente.'}
              </p>
            </div>
          </div>
        )}

        {/* Información adicional */}
        <div className="text-sm text-gray-500 bg-gray-50 p-4 rounded-lg">
          <p className="font-medium text-gray-700 mb-2">💡 Consejos de búsqueda:</p>
          <ul className="space-y-1 list-disc list-inside">
            <li>El número de radicación está en el documento de confirmación</li>
            <li>Para búsqueda por documento, usa el mismo registrado al radicar</li>
            <li>Los resultados muestran el estado actual de tu incapacidad</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
