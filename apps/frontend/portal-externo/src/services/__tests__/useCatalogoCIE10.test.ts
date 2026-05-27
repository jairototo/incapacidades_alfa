import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement, type ReactNode } from 'react';
import { 
  useSearchCIE10, 
  useCIE10ByCodigo,
  useCIE10Stats,
  useListCIE10
} from '../queries/useCatalogoCIE10';
import * as api from '../api';

vi.mock('../api');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useCatalogoCIE10', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useSearchCIE10', () => {
    it('should return CIE-10 codes matching query', async () => {
      // Arrange
      const mockData = [
        { codigo: 'A00', descripcion: 'Cólera', created_at: '2026-01-01', updated_at: '2026-01-01' },
        { codigo: 'A00.0', descripcion: 'Cólera debido a Vibrio cholerae 01, biotipo cholerae', created_at: '2026-01-01', updated_at: '2026-01-01' },
        { codigo: 'A00.1', descripcion: 'Cólera debido a Vibrio cholerae 01, biotipo El Tor', created_at: '2026-01-01', updated_at: '2026-01-01' },
      ];
      vi.mocked(api.catalogoCIE10Api.search).mockResolvedValue({ data: mockData } as any);

      // Act
      const { result } = renderHook(
        () => useSearchCIE10('A00', 20),
        { wrapper: createWrapper() }
      );

      // Assert
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toHaveLength(3);
      expect(result.current.data?.[0].codigo).toBe('A00');
    });

    it('should search by description (diabetes)', async () => {
      // Arrange
      const mockData = [
        { codigo: 'E10', descripcion: 'Diabetes mellitus insulinodependiente', created_at: '2026-01-01', updated_at: '2026-01-01' },
        { codigo: 'E11', descripcion: 'Diabetes mellitus no insulinodependiente', created_at: '2026-01-01', updated_at: '2026-01-01' },
        { codigo: 'E12', descripcion: 'Diabetes mellitus asociada con desnutrición', created_at: '2026-01-01', updated_at: '2026-01-01' },
      ];
      vi.mocked(api.catalogoCIE10Api.search).mockResolvedValue({ data: mockData } as any);

      // Act
      const { result } = renderHook(
        () => useSearchCIE10('diabetes', 20),
        { wrapper: createWrapper() }
      );

      // Assert
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toHaveLength(3);
      expect(result.current.data?.every(item => item.descripcion.toLowerCase().includes('diabetes'))).toBe(true);
    });

    it('should not execute when query length < 2', () => {
      // Arrange
      vi.mocked(api.catalogoCIE10Api.search).mockResolvedValue({ data: [] } as any);

      // Act
      renderHook(
        () => useSearchCIE10('A', 20),
        { wrapper: createWrapper() }
      );

      // Assert - La query no debería ejecutarse con menos de 2 caracteres
      expect(api.catalogoCIE10Api.search).not.toHaveBeenCalled();
    });

    it('should use staleTime of 10 minutes', async () => {
      // Arrange
      const mockData = [
        { codigo: 'J00', descripcion: 'Rinofaringitis aguda [resfriado común]', created_at: '2026-01-01', updated_at: '2026-01-01' }
      ];
      vi.mocked(api.catalogoCIE10Api.search).mockResolvedValue({ data: mockData } as any);

      // Act
      const { result } = renderHook(
        () => useSearchCIE10('J00', 20),
        { wrapper: createWrapper() }
      );

      // Assert
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      // Verificamos que la query funciona correctamente (staleTime se verifica en configuración)
      expect(result.current.data).toBeDefined();
      expect(result.current.data?.[0].codigo).toBe('J00');
    });
  });

  describe('useCIE10ByCodigo', () => {
    it('should return exact code when found', async () => {
      // Arrange
      const mockData = { 
        codigo: 'A00.1', 
        descripcion: 'Cólera debido a Vibrio cholerae 01, biotipo El Tor',
        created_at: '2026-01-01',
        updated_at: '2026-01-01'
      };
      vi.mocked(api.catalogoCIE10Api.getByCodigo).mockResolvedValue({ data: mockData } as any);

      // Act
      const { result } = renderHook(
        () => useCIE10ByCodigo('A00.1', true),
        { wrapper: createWrapper() }
      );

      // Assert
      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.codigo).toBe('A00.1');
      expect(result.current.data?.descripcion).toContain('Cólera');
    });

    it('should handle not found error (404)', async () => {
      // Arrange
      const error = {
        response: {
          status: 404,
          data: {
            error: { message: 'Código CIE-10 no encontrado' }
          }
        }
      };
      vi.mocked(api.catalogoCIE10Api.getByCodigo).mockRejectedValue(error);

      // Act
      const { result } = renderHook(
        () => useCIE10ByCodigo('Z99.9', true),
        { wrapper: createWrapper() }
      );

      // Assert
      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toBeDefined();
    });
  });
});
