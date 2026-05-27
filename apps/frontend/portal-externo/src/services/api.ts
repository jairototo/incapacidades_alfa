import axios from 'axios';
import type { Solicitante, SolicitanteCreate, SolicitanteUpdate, SearchSolicitanteParams } from '@/types/solicitante';
import type { CatalogoCIE10, SearchCIE10Params, CIE10Stats } from '@/types/catalogoCIE10';

/**
 * Instancia de Axios configurada para comunicarse con el backend
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8010/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Logging en desarrollo
api.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      });
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Logging y manejo de errores
api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.url}`, response.data);
    }
    return response;
  },
  (error) => {
    if (import.meta.env.DEV) {
      console.error('[API Error]', {
        url: error.config?.url,
        status: error.response?.status,
        data: error.response?.data,
      });
    }
    
    // Manejo de errores comunes
    if (error.response) {
      // El servidor respondió con un código de estado fuera del rango 2xx
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          error.message = data.error?.message || 'Solicitud inválida';
          break;
        case 404:
          error.message = data.error?.message || 'Recurso no encontrado';
          break;
        case 422:
          error.message = data.error?.message || 'Error de validación';
          break;
        case 429:
          error.message = 'Demasiadas solicitudes. Por favor, intente más tarde.';
          break;
        case 500:
          error.message = 'Error interno del servidor';
          break;
        default:
          error.message = data.error?.message || 'Ocurrió un error inesperado';
      }
    } else if (error.request) {
      // La solicitud fue hecha pero no se recibió respuesta
      error.message = 'No se pudo conectar con el servidor';
    }
    
    return Promise.reject(error);
  }
);

/**
 * API de Solicitantes
 */
export const solicitantesApi = {
  create: (data: SolicitanteCreate) => 
    api.post<Solicitante>('/solicitantes', data),
  
  search: (params: SearchSolicitanteParams) => 
    api.get<Solicitante[]>('/solicitantes/search', { params }),
  
  getById: (id: string) => 
    api.get<Solicitante>(`/solicitantes/${id}`),
  
  update: (id: string, data: SolicitanteUpdate) => 
    api.put<Solicitante>(`/solicitantes/${id}`, data),
  
  delete: (id: string) => 
    api.delete(`/solicitantes/${id}`),
};

/**
 * API de Catálogo CIE-10
 */
export const catalogoCIE10Api = {
  search: (params: SearchCIE10Params) => 
    api.get<CatalogoCIE10[]>('/catalogos/cie10', { params }),
  
  getByCodigo: (codigo: string) => 
    api.get<CatalogoCIE10>(`/catalogos/cie10/${codigo}`),
  
  list: (skip: number = 0, limit: number = 100) => 
    api.get<CatalogoCIE10[]>('/catalogos/cie10/all/list', { 
      params: { skip, limit } 
    }),
  
  stats: () => 
    api.get<CIE10Stats>('/catalogos/cie10/stats/count'),
};

export default api;
