import { describe, it, expect, vi, beforeEach } from 'vitest';
import api from '@/lib/api';
import { empresaService } from '../empresaService';

vi.mock('@/lib/api');

describe('empresaService', () => {
  beforeEach(() => vi.clearAllMocks());

  it('list() returns the flat array from the backend, not a wrapper object', async () => {
    const mockItems = [
      { id: '1', nit: '900123456', razon_social: 'Empresa Test', estado: 'ACTIVA', ciudad: 'Bogotá', created_at: '2026-01-01T00:00:00Z' },
    ];
    vi.mocked(api.get).mockResolvedValue({ data: mockItems });

    const result = await empresaService.list({ skip: 0, limit: 100 });

    expect(result).toEqual(mockItems);
    expect(api.get).toHaveBeenCalledWith('/empresas/', { params: { skip: 0, limit: 100 } });
  });

  it('create() posts to /empresas/ and returns the credentials-included response', async () => {
    const mockResponse = {
      id: '1', nit: '900999999', razon_social: 'Nueva SAS', estado: 'ACTIVA',
      email_contacto: 'nueva@empresa.com', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
      usuario_generado: { username: '900999999', password: 'Abc12345xyz9' },
    };
    vi.mocked(api.post).mockResolvedValue({ data: mockResponse });

    const result = await empresaService.create({
      nit: '900999999', razon_social: 'Nueva SAS', email_contacto: 'nueva@empresa.com',
    });

    expect(result.usuario_generado.password).toBe('Abc12345xyz9');
    expect(api.post).toHaveBeenCalledWith('/empresas/', {
      nit: '900999999', razon_social: 'Nueva SAS', email_contacto: 'nueva@empresa.com',
    });
  });

  it('regenerarPassword() posts to the regenerar-password endpoint', async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { message: 'ok', username: '900999999', password: 'NewTemp123x' },
    });

    const result = await empresaService.regenerarPassword('1');

    expect(result.password).toBe('NewTemp123x');
    expect(api.post).toHaveBeenCalledWith('/empresas/1/regenerar-password');
  });

  it('getAnalitica() fetches the combined analytics payload', async () => {
    const mockData = { top_empresas: [], tendencia_mensual: [] };
    vi.mocked(api.get).mockResolvedValue({ data: mockData });

    const result = await empresaService.getAnalitica();

    expect(result).toEqual(mockData);
    expect(api.get).toHaveBeenCalledWith('/empresas/analitica');
  });
});
