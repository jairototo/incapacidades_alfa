import api from '@/lib/api';
import type {
  Empresa,
  EmpresaListItem,
  EmpresaCreatePayload,
  EmpresaCreateResponse,
  EmpresaUpdatePayload,
  RegenerarPasswordResponse,
  AnaliticaEmpresasResponse,
} from '@/types/empresa';

interface ListEmpresasParams {
  skip?: number;
  limit?: number;
  nit?: string;
  ciudad?: string;
  departamento?: string;
  search?: string;
}

/**
 * Servicio para gestión de empresas
 */
class EmpresaService {
  private readonly baseUrl = '/empresas/';

  async list(params: ListEmpresasParams): Promise<EmpresaListItem[]> {
    const { data } = await api.get<EmpresaListItem[]>(this.baseUrl, { params });
    return data;
  }

  async getById(id: string): Promise<Empresa> {
    const { data } = await api.get<Empresa>(`${this.baseUrl}${id}`);
    return data;
  }

  async create(payload: EmpresaCreatePayload): Promise<EmpresaCreateResponse> {
    const { data } = await api.post<EmpresaCreateResponse>(this.baseUrl, payload);
    return data;
  }

  async update(id: string, payload: EmpresaUpdatePayload): Promise<Empresa> {
    const { data } = await api.put<Empresa>(`${this.baseUrl}${id}`, payload);
    return data;
  }

  async regenerarPassword(id: string): Promise<RegenerarPasswordResponse> {
    const { data } = await api.post<RegenerarPasswordResponse>(`${this.baseUrl}${id}/regenerar-password`);
    return data;
  }

  async getAnalitica(): Promise<AnaliticaEmpresasResponse> {
    const { data } = await api.get<AnaliticaEmpresasResponse>(`${this.baseUrl}analitica`);
    return data;
  }
}

export const empresaService = new EmpresaService();
export default empresaService;
