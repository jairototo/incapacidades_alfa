/**
 * Servicio para consulta pública de incapacidades.
 * 
 * Proporciona métodos para:
 * - Consultar incapacidad por número de radicación
 * - Consultar incapacidad por documento de identidad
 * - Generar URL de descarga temporal para documentos públicos
 * 
 * Todos los endpoints son públicos (sin autenticación).
 */

import api from '@/services/api';
import type {
  ConsultaIncapacidadResponse,
  PresignedUrlResponse,
  TipoDocumento,
} from '@/types/consulta';

export const consultaService = {
  /**
   * Consultar incapacidad por número de radicación.
   * 
   * Endpoint público sin autenticación que permite buscar una incapacidad
   * usando su número de radicación único.
   * 
   * @param numero - Número de radicación (ej: INC-ARL-20260117-0001)
   * @returns Promise con los datos completos de la incapacidad
   * @throws {AxiosError} 
   *   - 400 si el parámetro es inválido
   *   - 404 si la incapacidad no existe
   * 
   * @example
   * ```typescript
   * const incapacidad = await consultaService.consultarPorNumero('INC-ARL-20260117-0001');
   * console.log(incapacidad.estado); // "EN_AUDITORIA"
   * ```
   */
  consultarPorNumero: async (
    numero: string
  ): Promise<ConsultaIncapacidadResponse> => {
    const { data } = await api.get<ConsultaIncapacidadResponse>(
      '/incapacidades/consultar',
      {
        params: { numero },
      }
    );
    return data;
  },

  /**
   * Consultar incapacidad por documento de identidad.
   * 
   * Endpoint público sin autenticación que permite buscar una incapacidad
   * usando el documento de identidad del empleado o afiliado.
   * 
   * @param documento - Número de documento de identidad
   * @param tipoDocumento - Tipo de documento (CC, CE, TI, PASAPORTE, PEP)
   * @returns Promise con los datos completos de la incapacidad
   * @throws {AxiosError}
   *   - 400 si los parámetros son inválidos
   *   - 404 si no se encuentra incapacidad para ese documento
   * 
   * @example
   * ```typescript
   * const incapacidad = await consultaService.consultarPorDocumento(
   *   '1234567890',
   *   'CC'
   * );
   * console.log(incapacidad.nombre_completo); // "Juan Pérez García"
   * ```
   */
  consultarPorDocumento: async (
    documento: string,
    tipoDocumento: TipoDocumento
  ): Promise<ConsultaIncapacidadResponse> => {
    const { data } = await api.get<ConsultaIncapacidadResponse>(
      '/incapacidades/consultar',
      {
        params: {
          documento,
          tipo_documento: tipoDocumento,
        },
      }
    );
    return data;
  },

  /**
   * Generar URL de descarga temporal para un documento público.
   * 
   * Endpoint público que genera una URL pre-firmada válida por 15 minutos
   * para descargar un documento asociado a una incapacidad.
   * 
   * Solo funciona con tipos de documentos públicos:
   * - INCAPACIDAD_MEDICA
   * - CEDULA
   * - HISTORIA_CLINICA
   * 
   * @param numero - Número de radicación de la incapacidad
   * @param documentoId - ID único del documento (UUID)
   * @returns Promise con URL pre-firmada y metadata del documento
   * @throws {AxiosError}
   *   - 404 si la incapacidad o el documento no existen
   *   - 403 si el documento no es público o no pertenece a la incapacidad
   * 
   * @example
   * ```typescript
   * const presignedUrl = await consultaService.descargarDocumento(
   *   'INC-ARL-20260117-0001',
   *   '550e8400-e29b-41d4-a716-446655440000'
   * );
   * 
   * // Abrir en nueva pestaña
   * window.open(presignedUrl.url, '_blank');
   * 
   * console.log(presignedUrl.expires_in); // 900 (15 minutos)
   * ```
   */
  descargarDocumento: async (
    numero: string,
    documentoId: string
  ): Promise<PresignedUrlResponse> => {
    const { data } = await api.get<PresignedUrlResponse>(
      `/incapacidades/${numero}/documentos/${documentoId}/download`
    );
    return data;
  },
};
