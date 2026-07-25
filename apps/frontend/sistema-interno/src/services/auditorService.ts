import api from '@/lib/api';

export interface AuditorOption {
  id: string;
  username: string;
  nombre_completo: string;
  sucursal: string | null;
  incapacidades_asignadas_activas: number;
}

class AuditorService {
  private readonly baseUrl = '/usuarios';

  async listActivos(): Promise<AuditorOption[]> {
    const { data } = await api.get<AuditorOption[]>(this.baseUrl, {
      params: { rol: 'AUDITOR', estado: 'ACTIVO', limit: 100 },
    });
    return data;
  }
}

export const auditorService = new AuditorService();
export default auditorService;
