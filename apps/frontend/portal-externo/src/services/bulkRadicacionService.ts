import api from '@/lib/api';

export interface ValidacionError {
  codigo: string;
  descripcion: string;
  campo_afectado?: string | null;
  severidad: string; // "ERROR" | "WARNING"
}

export interface ValidacionFila {
  fila: number;
  empleado_id: string | null;
  datos: Record<string, unknown>;
  errores: ValidacionError[];
  valida: boolean; // true when the row has NO ERROR-severity issues (warnings are advisory)
}

export interface ValidacionResponse {
  filas: ValidacionFila[];
  total: number;
  validas: number;
}

export interface ZipAsignacion {
  archivo: string;
  numero_documento?: string;
  tipo?: string;
  match: boolean;
  motivo?: string | null;
}

export interface RadicacionMasivaResponse {
  total_radicadas: number;
  items: { empleado_id: string; incapacidad_id?: string; numero?: string; success: boolean; error?: string }[];
  documentos_ignorados: { filename: string; motivo: string }[];
}

export async function descargarPlantilla(empleadoIds: string[]): Promise<Blob> {
  const { data } = await api.post('/incapacidades/radicar-masiva/plantilla',
    { empleado_ids: empleadoIds }, { responseType: 'blob' });
  return data as Blob;
}

export async function validarExcel(file: File): Promise<ValidacionResponse> {
  const fd = new FormData();
  fd.append('archivo', file);
  const { data } = await api.post<ValidacionResponse>('/incapacidades/radicar-masiva/validar', fd,
    { headers: { 'Content-Type': 'multipart/form-data' } });
  return data;
}

export async function mapearZip(file: File, documentos: string[]): Promise<{ asignaciones: ZipAsignacion[] }> {
  const fd = new FormData();
  fd.append('archivo', file);
  fd.append('documentos_esperados', documentos.join(','));
  const { data } = await api.post<{ asignaciones: ZipAsignacion[] }>('/incapacidades/radicar-masiva/zip', fd,
    { headers: { 'Content-Type': 'multipart/form-data' } });
  return data;
}

export async function radicarMasiva(
  filas: Record<string, unknown>[],
  documentos: { name: string; file: File }[],
): Promise<RadicacionMasivaResponse> {
  const fd = new FormData();
  fd.append('filas', JSON.stringify(filas));
  documentos.forEach((d) => fd.append('documentos', d.file, d.name));
  const { data } = await api.post<RadicacionMasivaResponse>('/incapacidades/radicar-masiva', fd,
    { headers: { 'Content-Type': 'multipart/form-data' } });
  return data;
}
