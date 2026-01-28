import api from '@/lib/api';
import type { Empresa } from '@/types/empresa';

interface ListEmpresasParams {
  skip?: number;
  limit?: number;
  search?: string;
}

interface ListEmpresasResponse {
  items: Empresa[];
  total: number;
  skip: number;
  limit: number;
}

/**
 * Servicio para gestión de empresas
 */
class EmpresaService {
  private readonly baseUrl = '/empresas/';

  /**
   * Listar empresas con paginación y búsqueda opcional
   */
  async list(params: ListEmpresasParams): Promise<ListEmpresasResponse> {
    const { data } = await api.get<ListEmpresasResponse>(this.baseUrl, { params });
    return data;
  }

  /**
   * Obtener una empresa por ID
   */
  async getById(id: string): Promise<Empresa> {
    const { data } = await api.get<Empresa>(`${this.baseUrl}/${id}`);
    return data;
  }

  /**
   * Buscar empresas por NIT o razón social
   */
  async search(query: string): Promise<Empresa[]> {
    const { data } = await api.get<ListEmpresasResponse>(this.baseUrl, {
      params: { search: query, limit: 10 },
    });
    return data.items;
  }
}

export const empresaService = new EmpresaService();
export default empresaService;
