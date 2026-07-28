import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '@/lib/api';
import { empleadoService } from '../empleadoService';

vi.mock('@/lib/api');

describe('empleadoService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('list() returns the flat array, forwards filters as params', async () => {
    const mockItems = [
      { id: '1', numero_documento: '123', tipo_documento: 'CC', nombres: 'Ana', apellidos: 'Gómez', cargo: 'Analista', estado: 'ACTIVO', created_at: '2026-01-01T00:00:00Z' },
    ];
    vi.mocked(api.get).mockResolvedValue({ data: mockItems });

    const result = await empleadoService.list({ empresa_id: 'e1', skip: 0, limit: 100 });

    expect(result).toEqual(mockItems);
    expect(api.get).toHaveBeenCalledWith('/empleados/', { params: { empresa_id: 'e1', skip: 0, limit: 100 } });
  });

  it('create() posts to /empleados/', async () => {
    const payload = {
      empresa_id: 'e1', numero_documento: '999', tipo_documento: 'CC',
      nombres: 'Luis', apellidos: 'Pérez', fecha_ingreso: '2024-01-01',
    };
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'x', ...payload, estado: 'ACTIVO', created_at: '2026-01-01T00:00:00Z' } });

    await empleadoService.create(payload);

    expect(api.post).toHaveBeenCalledWith('/empleados/', payload);
  });

  it('getPlantilla() requests a blob', async () => {
    const mockBlob = new Blob(['xlsx-bytes']);
    vi.mocked(api.get).mockResolvedValue({ data: mockBlob });

    const result = await empleadoService.getPlantilla();

    expect(result).toBe(mockBlob);
    expect(api.get).toHaveBeenCalledWith('/empleados/plantilla', { responseType: 'blob' });
  });

  it('validarCargaMasiva() posts multipart form data with the file', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { total_filas: 2, validas: 1, con_error: 1, errores: [{ fila: 2, columna: 'numero_documento', mensaje: 'Campo obligatorio' }] },
    });
    const file = new File(['content'], 'empleados.xlsx');

    const result = await empleadoService.validarCargaMasiva(file);

    expect(result.validas).toBe(1);
    const callArgs = vi.mocked(api.post).mock.calls[0];
    expect(callArgs[0]).toBe('/empleados/carga-masiva/validar');
    expect(callArgs[1]).toBeInstanceOf(FormData);
    expect(callArgs[2]?.headers).toEqual({ 'Content-Type': 'multipart/form-data' });
  });

  it('confirmarCargaMasiva() posts multipart form data with the file', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { total_filas: 2, insertadas: 1, con_error: 1, errores: [] },
    });
    const file = new File(['content'], 'empleados.xlsx');

    const result = await empleadoService.confirmarCargaMasiva(file);

    expect(result.insertadas).toBe(1);
    const callArgs = vi.mocked(api.post).mock.calls[0];
    expect(callArgs[0]).toBe('/empleados/carga-masiva/confirmar');
    expect(callArgs[1]).toBeInstanceOf(FormData);
  });
});
