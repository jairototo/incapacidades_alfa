import api from '@/lib/api';

export interface AuditorOption {
  id: string;
  username: string;
  email: string;
  nombre_completo: string;
  sucursal: string | null;
  incapacidades_asignadas_activas: number;
  estado: string;
}

export interface CreateAuditorData {
  username: string;
  email: string;
  nombre_completo: string;
  password: string;
  sucursal: string | null;
}

export interface UpdateAuditorData {
  nombre_completo?: string;
  email?: string;
  sucursal?: string | null;
}

class AuditorService {
  private readonly baseUrl = '/usuarios';

  async listActivos(): Promise<AuditorOption[]> {
    const { data } = await api.get<AuditorOption[]>(this.baseUrl, {
      params: { rol: 'AUDITOR', estado: 'ACTIVO', limit: 100 },
    });
    return data;
  }

  async create(payload: CreateAuditorData): Promise<AuditorOption> {
    const { data } = await api.post<AuditorOption>(`${this.baseUrl}/`, {
      ...payload,
      rol: 'AUDITOR',
    });
    return data;
  }

  async update(id: string, payload: UpdateAuditorData): Promise<AuditorOption> {
    const { data } = await api.put<AuditorOption>(`${this.baseUrl}/${id}`, payload);
    return data;
  }

  async deactivate(id: string): Promise<AuditorOption> {
    const { data } = await api.post<AuditorOption>(`${this.baseUrl}/${id}/desactivar`);
    return data;
  }

  async reporte(): Promise<AuditorOption[]> {
    const { data } = await api.get<AuditorOption[]>(`${this.baseUrl}/reporte-auditores`);
    return data;
  }
}

export const auditorService = new AuditorService();
export default auditorService;
