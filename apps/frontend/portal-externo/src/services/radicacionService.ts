import api from '@/lib/api';

export interface RadicacionResponse {
  total_radicadas: number;
  items: { empleado_id: string; incapacidad_id?: string; numero?: string; success: boolean; error?: string }[];
}

export async function radicarIndividual(form: FormData): Promise<RadicacionResponse> {
  const { data } = await api.post<RadicacionResponse>('/incapacidades/radicar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
