import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { createIncapacidad, useCreateIncapacidad, transformWizardToDTO } from '../incapacidadService';
import api from '../api';
import type { CreateIncapacidadDTO, IncapacidadResponse } from '@/types/api';

// Mock del módulo api
vi.mock('../api');

describe('incapacidadService', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: any) =>
    createElement(QueryClientProvider, { client: queryClient }, children);

  describe('createIncapacidad', () => {
    it('debe crear incapacidad exitosamente', async () => {
      const mockDTO: CreateIncapacidadDTO = {
        tipo: 'ARL',
        empleado_id: '123e4567-e89b-12d3-a456-426614174000',
        empresa_id: '123e4567-e89b-12d3-a456-426614174001',
        fecha_inicio: '2026-01-10',
        fecha_fin: '2026-01-15',
        dias_totales: 5,
        diagnostico_cie10: 'A00.1',
        valor_dia: 50000,
      };

      const mockResponse: IncapacidadResponse = {
        id: '123e4567-e89b-12d3-a456-426614174002',
        numero: 'INC-ARL-2026-001234',
        tipo: 'ARL',
        estado: 'RADICADA',
        fecha_inicio: '2026-01-10',
        fecha_fin: '2026-01-15',
        dias_totales: 5,
        diagnostico_cie10: 'A00.1',
        descripcion_diagnostico: null,
        valor_dia: 50000,
        valor_total: 250000,
        observaciones: null,
        created_at: '2026-01-16T10:00:00Z',
        updated_at: '2026-01-16T10:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse });

      const result = await createIncapacidad(mockDTO);

      expect(api.post).toHaveBeenCalledWith('/incapacidades', mockDTO);
      expect(result).toEqual(mockResponse);
      expect(result.numero).toBe('INC-ARL-2026-001234');
      expect(result.estado).toBe('RADICADA');
    });

    it('debe manejar errores de red', async () => {
      const mockDTO: CreateIncapacidadDTO = {
        tipo: 'SALUD',
        afiliado_id: '123e4567-e89b-12d3-a456-426614174003',
        fecha_inicio: '2026-01-10',
        fecha_fin: '2026-01-15',
        dias_totales: 5,
        diagnostico_cie10: 'B00.2',
        valor_dia: 40000,
      };

      const mockError = {
        response: {
          status: 500,
          data: {
            error: {
              code: 'INTERNAL_ERROR',
              message: 'Error interno del servidor',
            },
          },
        },
      };

      vi.mocked(api.post).mockRejectedValueOnce(mockError);

      await expect(createIncapacidad(mockDTO)).rejects.toEqual(mockError);
    });

    it('debe manejar errores de validación (400)', async () => {
      const mockDTO: CreateIncapacidadDTO = {
        tipo: 'ARL',
        empleado_id: 'invalid-uuid',
        empresa_id: '123e4567-e89b-12d3-a456-426614174001',
        fecha_inicio: '2026-01-10',
        fecha_fin: '2026-01-15',
        dias_totales: 5,
        diagnostico_cie10: 'A00.1',
        valor_dia: 50000,
      };

      const mockError = {
        response: {
          status: 400,
          data: {
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Datos inválidos',
              details: [
                {
                  field: 'empleado_id',
                  message: 'UUID inválido',
                },
              ],
            },
          },
        },
      };

      vi.mocked(api.post).mockRejectedValueOnce(mockError);

      await expect(createIncapacidad(mockDTO)).rejects.toEqual(mockError);
    });
  });

  describe('useCreateIncapacidad', () => {
    it('debe crear incapacidad exitosamente con mutation', async () => {
      const mockResponse: IncapacidadResponse = {
        id: '123e4567-e89b-12d3-a456-426614174002',
        numero: 'INC-ARL-2026-001234',
        tipo: 'ARL',
        estado: 'RADICADA',
        fecha_inicio: '2026-01-10',
        fecha_fin: '2026-01-15',
        dias_totales: 5,
        diagnostico_cie10: 'A00.1',
        descripcion_diagnostico: null,
        valor_dia: 50000,
        valor_total: 250000,
        observaciones: null,
        created_at: '2026-01-16T10:00:00Z',
        updated_at: '2026-01-16T10:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse });

      const { result } = renderHook(() => useCreateIncapacidad(), { wrapper });

      const mockDTO: CreateIncapacidadDTO = {
        tipo: 'ARL',
        empleado_id: '123e4567-e89b-12d3-a456-426614174000',
        empresa_id: '123e4567-e89b-12d3-a456-426614174001',
        fecha_inicio: '2026-01-10',
        fecha_fin: '2026-01-15',
        dias_totales: 5,
        diagnostico_cie10: 'A00.1',
        valor_dia: 50000,
      };

      result.current.mutate(mockDTO);

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockResponse);
    });

    it('debe manejar errores en mutation', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            error: {
              message: 'Datos inválidos',
            },
          },
        },
      };

      vi.mocked(api.post).mockRejectedValueOnce(mockError);

      const { result } = renderHook(() => useCreateIncapacidad(), { wrapper });

      const mockDTO: CreateIncapacidadDTO = {
        tipo: 'ARL',
        empleado_id: '123e4567-e89b-12d3-a456-426614174000',
        empresa_id: '123e4567-e89b-12d3-a456-426614174001',
        fecha_inicio: '2026-01-10',
        fecha_fin: '2026-01-15',
        dias_totales: 5,
        diagnostico_cie10: 'A00.1',
        valor_dia: 50000,
      };

      result.current.mutate(mockDTO);

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toEqual(mockError);
    });
  });

  describe('transformWizardToDTO', () => {
    it('debe transformar datos ARL correctamente', () => {
      const wizardData = {
        tipo: 'ARL',
        datosPersonales: {
          id: '123e4567-e89b-12d3-a456-426614174000',
          empresa_id: '123e4567-e89b-12d3-a456-426614174001',
        },
        datosIncapacidad: {
          fecha_inicio: new Date('2026-01-10'),
          fecha_fin: new Date('2026-01-15'),
          dias_totales: 5,
          diagnostico_cie10: 'A00.1',
          descripcion_diagnostico: 'Diagnóstico de prueba',
          valor_dia: 50000,
          ips: 'IPS Test',
          tipo_enfermedad: 'ACCIDENTE_TRABAJO',
          observaciones: 'Observación de prueba',
        },
      };

      const result = transformWizardToDTO(wizardData);

      expect(result).toEqual({
        tipo: 'ARL',
        empleado_id: '123e4567-e89b-12d3-a456-426614174000',
        empresa_id: '123e4567-e89b-12d3-a456-426614174001',
        fecha_inicio: '2026-01-10',
        fecha_fin: '2026-01-15',
        dias_totales: 5,
        diagnostico_cie10: 'A00.1',
        descripcion_diagnostico: 'Diagnóstico de prueba',
        valor_dia: 50000,
        ips: 'IPS Test',
        tipo_enfermedad: 'ACCIDENTE_TRABAJO',
        observaciones: 'Observación de prueba',
        siniestro_id: undefined,
      });
    });

    it('debe transformar datos SALUD correctamente', () => {
      const wizardData = {
        tipo: 'SALUD',
        datosPersonales: {
          id: '123e4567-e89b-12d3-a456-426614174003',
        },
        datosIncapacidad: {
          fecha_inicio: new Date('2026-01-12'),
          fecha_fin: new Date('2026-01-20'),
          dias_totales: 8,
          diagnostico_cie10: 'B00.2',
          descripcion_diagnostico: 'Enfermedad general',
          valor_dia: 40000,
          eps: 'EPS Test',
          subtipo: 'ENFERMEDAD_GENERAL',
        },
      };

      const result = transformWizardToDTO(wizardData);

      expect(result).toEqual({
        tipo: 'SALUD',
        afiliado_id: '123e4567-e89b-12d3-a456-426614174003',
        fecha_inicio: '2026-01-12',
        fecha_fin: '2026-01-20',
        dias_totales: 8,
        diagnostico_cie10: 'B00.2',
        descripcion_diagnostico: 'Enfermedad general',
        valor_dia: 40000,
        eps: 'EPS Test',
        subtipo: 'ENFERMEDAD_GENERAL',
        observaciones: undefined,
      });
    });

    it('debe manejar campos opcionales vacíos', () => {
      const wizardData = {
        tipo: 'ARL',
        datosPersonales: {
          id: '123e4567-e89b-12d3-a456-426614174000',
          empresa_id: '123e4567-e89b-12d3-a456-426614174001',
        },
        datosIncapacidad: {
          fecha_inicio: new Date('2026-01-10'),
          fecha_fin: new Date('2026-01-15'),
          dias_totales: 5,
          diagnostico_cie10: 'A00.1',
          valor_dia: 50000,
        },
      };

      const result = transformWizardToDTO(wizardData);

      expect(result.descripcion_diagnostico).toBeUndefined();
      expect(result.ips).toBeUndefined();
      expect(result.observaciones).toBeUndefined();
    });

    it('debe formatear fechas correctamente (ISO date)', () => {
      const wizardData = {
        tipo: 'ARL',
        datosPersonales: {
          id: '123e4567-e89b-12d3-a456-426614174000',
          empresa_id: '123e4567-e89b-12d3-a456-426614174001',
        },
        datosIncapacidad: {
          fecha_inicio: new Date('2026-01-10T15:30:00Z'),
          fecha_fin: new Date('2026-01-15T15:30:00Z'),
          dias_totales: 5,
          diagnostico_cie10: 'A00.1',
          valor_dia: 50000,
        },
      };

      const result = transformWizardToDTO(wizardData);

      expect(result.fecha_inicio).toBe('2026-01-10');
      expect(result.fecha_fin).toBe('2026-01-15');
    });
  });
});
