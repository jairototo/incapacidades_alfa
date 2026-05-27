import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from './api';
import type { CreateIncapacidadDTO, IncapacidadResponse } from '@/types/api';

/**
 * Servicio para gestión de incapacidades
 */

/**
 * Crear una nueva incapacidad en el backend
 */
export async function createIncapacidad(data: CreateIncapacidadDTO): Promise<IncapacidadResponse> {
  const response = await api.post<IncapacidadResponse>('/incapacidades', data);
  return response.data;
}

/**
 * Hook para crear incapacidad con React Query
 */
export function useCreateIncapacidad() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createIncapacidad,
    onSuccess: (data) => {
      // Invalidar queries relacionadas si existen
      queryClient.invalidateQueries({ queryKey: ['incapacidades'] });
      
      if (import.meta.env.DEV) {
        console.log('[useCreateIncapacidad] Incapacidad creada exitosamente:', {
          id: data.id,
          numero: data.numero,
          estado: data.estado,
        });
      }
    },
    onError: (error: any) => {
      // Log de error en desarrollo
      if (import.meta.env.DEV) {
        console.error('[useCreateIncapacidad] Error al crear incapacidad:', {
          message: error.message,
          response: error.response?.data,
        });
      }
    },
  });
}

/**
 * Transformar datos del wizard al formato del backend
 */
export function transformWizardToDTO(wizardData: any): CreateIncapacidadDTO {
  const { tipo, datosPersonales, datosIncapacidad } = wizardData;

  // Extraer dias_totales desde datosIncapacidad
  const diasTotales = datosIncapacidad?.dias_totales || 0;

  if (tipo === 'ARL') {
    return {
      tipo: 'ARL',
      empleado_id: datosPersonales?.id,
      empresa_id: datosPersonales?.empresa_id,
      siniestro_id: datosIncapacidad?.siniestro_id || undefined,
      fecha_inicio: datosIncapacidad?.fecha_inicio 
        ? new Date(datosIncapacidad.fecha_inicio).toISOString().split('T')[0]
        : '',
      fecha_fin: datosIncapacidad?.fecha_fin 
        ? new Date(datosIncapacidad.fecha_fin).toISOString().split('T')[0]
        : '',
      dias_totales: diasTotales,
      diagnostico_cie10: datosIncapacidad?.diagnostico_cie10 || '',
      descripcion_diagnostico: datosIncapacidad?.descripcion_diagnostico || undefined,
      valor_dia: datosIncapacidad?.valor_dia || 0,
      ips: datosIncapacidad?.ips || undefined,
      tipo_enfermedad: datosIncapacidad?.tipo_enfermedad || undefined,
      observaciones: datosIncapacidad?.observaciones || undefined,
    };
  } else {
    // SALUD
    return {
      tipo: 'SALUD',
      afiliado_id: datosPersonales?.id,
      fecha_inicio: datosIncapacidad?.fecha_inicio 
        ? new Date(datosIncapacidad.fecha_inicio).toISOString().split('T')[0]
        : '',
      fecha_fin: datosIncapacidad?.fecha_fin 
        ? new Date(datosIncapacidad.fecha_fin).toISOString().split('T')[0]
        : '',
      dias_totales: diasTotales,
      diagnostico_cie10: datosIncapacidad?.diagnostico_cie10 || '',
      descripcion_diagnostico: datosIncapacidad?.descripcion_diagnostico || undefined,
      valor_dia: datosIncapacidad?.valor_dia || 0,
      eps: datosIncapacidad?.eps || undefined,
      subtipo: datosIncapacidad?.subtipo || undefined,
      observaciones: datosIncapacidad?.observaciones || undefined,
    };
  }
}
