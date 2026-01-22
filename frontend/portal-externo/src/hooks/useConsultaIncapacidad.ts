/**
 * Hooks personalizados para consulta pública de incapacidades.
 * 
 * Proporciona React Query hooks con manejo de estado automático para:
 * - Consulta por número de radicación
 * - Consulta por documento de identidad
 * - Descarga de documentos con URL temporal
 * 
 * Todos los hooks manejan loading, error y success states automáticamente.
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import type { UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { consultaService } from '@/services/consultaService';
import type {
  ConsultaIncapacidadResponse,
  PresignedUrlResponse,
  TipoDocumento,
} from '@/types/consulta';

/**
 * Hook para consultar incapacidad por número de radicación.
 * 
 * Características:
 * - Consulta habilitada condicionalmente con `enabled`
 * - Datos en cache durante 5 minutos (staleTime)
 * - No reintenta en caso de error (404 es definitivo)
 * - Query key permite invalidación específica
 * 
 * @param numero - Número de radicación (ej: INC-ARL-20260117-0001)
 * @param enabled - Si la consulta debe ejecutarse (default: true)
 * @returns Query result con data, isLoading, error, etc.
 * 
 * @example
 * ```typescript
 * function BusquedaForm() {
 *   const [numero, setNumero] = useState('');
 *   const [buscar, setBuscar] = useState(false);
 *   
 *   const { data, isLoading, error } = useConsultarPorNumero(numero, buscar);
 *   
 *   const handleSubmit = (e) => {
 *     e.preventDefault();
 *     setBuscar(true); // Activa la consulta
 *   };
 *   
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <input value={numero} onChange={(e) => setNumero(e.target.value)} />
 *       <button type="submit">Buscar</button>
 *       {isLoading && <p>Buscando...</p>}
 *       {error && <p>Error: {error.message}</p>}
 *       {data && <DetalleIncapacidad data={data} />}
 *     </form>
 *   );
 * }
 * ```
 */
export const useConsultarPorNumero = (
  numero: string,
  enabled: boolean = true
): UseQueryResult<ConsultaIncapacidadResponse, Error> => {
  return useQuery({
    queryKey: ['incapacidad', 'consulta', 'numero', numero],
    queryFn: () => consultaService.consultarPorNumero(numero),
    enabled: enabled && !!numero, // Solo ejecuta si está habilitado Y hay número
    staleTime: 5 * 60 * 1000, // 5 minutos - los datos no cambian frecuentemente
    retry: false, // No reintentar - 404 es definitivo
    refetchOnWindowFocus: false, // No refrescar al volver a la pestaña
  });
};

/**
 * Hook para consultar incapacidad por documento de identidad.
 * 
 * Características:
 * - Consulta habilitada condicionalmente con `enabled`
 * - Datos en cache durante 5 minutos (staleTime)
 * - No reintenta en caso de error (404 es definitivo)
 * - Query key permite invalidación específica
 * 
 * @param documento - Número de documento de identidad
 * @param tipoDocumento - Tipo de documento (CC, CE, TI, PASAPORTE, PEP)
 * @param enabled - Si la consulta debe ejecutarse (default: true)
 * @returns Query result con data, isLoading, error, etc.
 * 
 * @example
 * ```typescript
 * function BusquedaPorDocumento() {
 *   const [documento, setDocumento] = useState('');
 *   const [tipoDocumento, setTipoDocumento] = useState<TipoDocumento>('CC');
 *   const [buscar, setBuscar] = useState(false);
 *   
 *   const { data, isLoading, error } = useConsultarPorDocumento(
 *     documento,
 *     tipoDocumento,
 *     buscar
 *   );
 *   
 *   const handleSubmit = (e) => {
 *     e.preventDefault();
 *     setBuscar(true);
 *   };
 *   
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <select value={tipoDocumento} onChange={(e) => setTipoDocumento(e.target.value as TipoDocumento)}>
 *         <option value="CC">Cédula de Ciudadanía</option>
 *         <option value="CE">Cédula de Extranjería</option>
 *       </select>
 *       <input value={documento} onChange={(e) => setDocumento(e.target.value)} />
 *       <button type="submit">Buscar</button>
 *       {isLoading && <p>Buscando...</p>}
 *       {error && <p>No se encontró incapacidad</p>}
 *       {data && <DetalleIncapacidad data={data} />}
 *     </form>
 *   );
 * }
 * ```
 */
export const useConsultarPorDocumento = (
  documento: string,
  tipoDocumento: TipoDocumento,
  enabled: boolean = true
): UseQueryResult<ConsultaIncapacidadResponse, Error> => {
  return useQuery({
    queryKey: ['incapacidad', 'consulta', 'documento', documento, tipoDocumento],
    queryFn: () => consultaService.consultarPorDocumento(documento, tipoDocumento),
    enabled: enabled && !!documento && !!tipoDocumento,
    staleTime: 5 * 60 * 1000, // 5 minutos
    retry: false, // No reintentar
    refetchOnWindowFocus: false,
  });
};

/**
 * Hook mutation para generar URL de descarga de documentos.
 * 
 * Mutation en lugar de query porque:
 * - La URL expira en 15 minutos (no cacheable)
 * - Cada descarga genera una URL nueva
 * - No queremos cache ni refetch automático
 * 
 * Características:
 * - Devuelve mutate function con loading/error states
 * - onSuccess/onError callbacks opcionales
 * - No almacena en cache (cada llamada es única)
 * 
 * @returns Mutation result con mutate, mutateAsync, isLoading, error, etc.
 * 
 * @example
 * ```typescript
 * function DocumentoCard({ documento, numero }) {
 *   const { mutate: descargar, isLoading, error } = useDescargarDocumento();
 *   
 *   const handleDescargar = () => {
 *     descargar(
 *       { numero, documentoId: documento.id },
 *       {
 *         onSuccess: (data) => {
 *           // Abrir URL en nueva pestaña
 *           window.open(data.url, '_blank');
 *           toast.success(`Descargando ${data.nombre_archivo}`);
 *         },
 *         onError: (error) => {
 *           toast.error('No se pudo generar la descarga');
 *         },
 *       }
 *     );
 *   };
 *   
 *   return (
 *     <button onClick={handleDescargar} disabled={isLoading}>
 *       {isLoading ? 'Generando...' : `Descargar ${documento.nombre_archivo}`}
 *     </button>
 *   );
 * }
 * ```
 * 
 * @example
 * ```typescript
 * // Uso con async/await
 * const { mutateAsync } = useDescargarDocumento();
 * 
 * const handleDescargarTodos = async () => {
 *   try {
 *     const urls = await Promise.all(
 *       documentos.map(doc => 
 *         mutateAsync({ numero: incapacidad.numero, documentoId: doc.id })
 *       )
 *     );
 *     urls.forEach(url => window.open(url.url, '_blank'));
 *   } catch (error) {
 *     toast.error('Error al descargar documentos');
 *   }
 * };
 * ```
 */
export const useDescargarDocumento = (): UseMutationResult<
  PresignedUrlResponse,
  Error,
  { numero: string; documentoId: string }
> => {
  return useMutation({
    mutationFn: ({ numero, documentoId }) =>
      consultaService.descargarDocumento(numero, documentoId),
    // No usar onSuccess/onError globales - dejar al componente decidir
  });
};
