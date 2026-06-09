import api from '@/lib/api';
import type {
  PreIncapacidadListItem,
  PreIncapacidadDetalle,
  PreIncapacidadUpdate,
  DevolucionRequest,
  DevolucionResponse,
  PromocionResponse,
  BandejaFiltros,
} from '@/types/preIncapacidad';
import type { Incapacidad } from '@/types/incapacidad';

export const preIncapacidadService = {
  async listar(filtros: BandejaFiltros = {}): Promise<PreIncapacidadListItem[]> {
    const params = Object.fromEntries(
      Object.entries({
        estado: filtros.estado,
        search: filtros.search,
        skip: filtros.skip ?? 0,
        limit: filtros.limit ?? 50,
      }).filter(([_, v]) => v !== undefined && v !== null && v !== '')
    );
    const { data } = await api.get<PreIncapacidadListItem[]>('/pre-incapacidades/', { params });
    return data;
  },

  async getById(id: string): Promise<PreIncapacidadDetalle> {
    const { data } = await api.get<PreIncapacidadDetalle>(`/pre-incapacidades/${id}`);
    return data;
  },

  async actualizar(id: string, updates: PreIncapacidadUpdate): Promise<PreIncapacidadDetalle> {
    const { data } = await api.patch<PreIncapacidadDetalle>(`/pre-incapacidades/${id}`, updates);
    return data;
  },

  async devolver(id: string, body: DevolucionRequest): Promise<DevolucionResponse> {
    const { data } = await api.post<DevolucionResponse>(`/pre-incapacidades/${id}/devolver`, body);
    return data;
  },

  async promover(id: string): Promise<PromocionResponse> {
    const { data } = await api.post<PromocionResponse>(`/pre-incapacidades/${id}/promover`);
    return data;
  },

  async getIncapacidad(preIncapacidadId: string): Promise<Incapacidad> {
    const res = await api.get<Incapacidad>(`/pre-incapacidades/${preIncapacidadId}/incapacidad`);
    return res.data;
  },
};
