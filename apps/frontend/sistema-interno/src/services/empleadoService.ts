import api from '@/lib/api';
import type {
  EmpleadoListItem,
  Empleado,
  EmpleadoCreatePayload,
  EmpleadoUpdatePayload,
  ValidacionMasivaResponse,
  ConfirmacionMasivaResponse,
} from '@/types/empleado';

interface ListEmpleadosParams {
  empresa_id?: string;
  estado?: string;
  documento?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

class EmpleadoService {
  private readonly baseUrl = '/empleados/';

  async list(params: ListEmpleadosParams): Promise<EmpleadoListItem[]> {
    const { data } = await api.get<EmpleadoListItem[]>(this.baseUrl, { params });
    return data;
  }

  async getById(id: string): Promise<Empleado> {
    const { data } = await api.get<Empleado>(`${this.baseUrl}${id}`);
    return data;
  }

  async create(payload: EmpleadoCreatePayload): Promise<Empleado> {
    const { data } = await api.post<Empleado>(this.baseUrl, payload);
    return data;
  }

  async update(id: string, payload: EmpleadoUpdatePayload): Promise<Empleado> {
    const { data } = await api.put<Empleado>(`${this.baseUrl}${id}`, payload);
    return data;
  }

  async deactivate(id: string): Promise<Empleado> {
    const { data } = await api.post<Empleado>(`${this.baseUrl}${id}/deactivate`);
    return data;
  }

  async getPlantilla(): Promise<Blob> {
    const { data } = await api.get<Blob>(`${this.baseUrl}plantilla`, { responseType: 'blob' });
    return data;
  }

  async validarCargaMasiva(file: File): Promise<ValidacionMasivaResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<ValidacionMasivaResponse>(
      `${this.baseUrl}carga-masiva/validar`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  }

  async confirmarCargaMasiva(file: File): Promise<ConfirmacionMasivaResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<ConfirmacionMasivaResponse>(
      `${this.baseUrl}carga-masiva/confirmar`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  }
}

export const empleadoService = new EmpleadoService();
export default empleadoService;
