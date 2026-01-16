import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { uploadDocumento, useUploadDocumento, uploadMultipleDocumentos } from '../documentoService';
import api from '../api';
import type { DocumentoResponse } from '@/types/api';

// Mock del módulo api
vi.mock('../api');

describe('documentoService', () => {
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

  describe('uploadDocumento', () => {
    it('debe subir documento exitosamente', async () => {
      const mockFile = new File(['content'], 'incapacidad.pdf', {
        type: 'application/pdf',
      });

      const mockResponse: DocumentoResponse = {
        id: '123e4567-e89b-12d3-a456-426614174010',
        tipo_documento: 'INCAPACIDAD_MEDICA',
        nombre_archivo: 'incapacidad.pdf',
        mime_type: 'application/pdf',
        tamanio_bytes: 1024,
        created_at: '2026-01-16T10:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse });

      const result = await uploadDocumento({
        incapacidadId: '123e4567-e89b-12d3-a456-426614174000',
        archivo: mockFile,
        tipoDocumento: 'INCAPACIDAD_MEDICA',
      });

      expect(api.post).toHaveBeenCalledWith(
        '/incapacidades/123e4567-e89b-12d3-a456-426614174000/documentos',
        expect.any(FormData),
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      expect(result).toEqual(mockResponse);
      expect(result.nombre_archivo).toBe('incapacidad.pdf');
      expect(result.tipo_documento).toBe('INCAPACIDAD_MEDICA');
    });

    it('debe crear FormData correctamente', async () => {
      const mockFile = new File(['content'], 'documento.pdf', {
        type: 'application/pdf',
      });

      const mockResponse: DocumentoResponse = {
        id: '123e4567-e89b-12d3-a456-426614174010',
        tipo_documento: 'HISTORIA_CLINICA',
        nombre_archivo: 'documento.pdf',
        mime_type: 'application/pdf',
        tamanio_bytes: 1024,
        created_at: '2026-01-16T10:00:00Z',
      };

      let capturedFormData: FormData | undefined;

      vi.mocked(api.post).mockImplementation(async (_url, data, _config) => {
        capturedFormData = data as FormData;
        return { data: mockResponse };
      });

      await uploadDocumento({
        incapacidadId: '123e4567-e89b-12d3-a456-426614174000',
        archivo: mockFile,
        tipoDocumento: 'HISTORIA_CLINICA',
      });

      expect(capturedFormData).toBeInstanceOf(FormData);
      expect(capturedFormData?.get('archivo')).toEqual(mockFile);
      expect(capturedFormData?.get('tipo_documento')).toBe('HISTORIA_CLINICA');
    });

    it('debe manejar errores de upload', async () => {
      const mockFile = new File(['content'], 'documento.pdf', {
        type: 'application/pdf',
      });

      const mockError = {
        response: {
          status: 400,
          data: {
            error: {
              code: 'INVALID_FILE',
              message: 'Archivo no válido',
            },
          },
        },
      };

      vi.mocked(api.post).mockRejectedValueOnce(mockError);

      await expect(
        uploadDocumento({
          incapacidadId: '123e4567-e89b-12d3-a456-426614174000',
          archivo: mockFile,
          tipoDocumento: 'INCAPACIDAD_MEDICA',
        })
      ).rejects.toEqual(mockError);
    });

    it('debe manejar diferentes tipos de documento', async () => {
      const mockFile = new File(['content'], 'soporte.pdf', {
        type: 'application/pdf',
      });

      const mockResponse: DocumentoResponse = {
        id: '123e4567-e89b-12d3-a456-426614174010',
        tipo_documento: 'SOPORTE_ARL',
        nombre_archivo: 'soporte.pdf',
        mime_type: 'application/pdf',
        tamanio_bytes: 2048,
        created_at: '2026-01-16T10:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse });

      const result = await uploadDocumento({
        incapacidadId: '123e4567-e89b-12d3-a456-426614174000',
        archivo: mockFile,
        tipoDocumento: 'SOPORTE_ARL',
      });

      expect(result.tipo_documento).toBe('SOPORTE_ARL');
    });
  });

  describe('useUploadDocumento', () => {
    it('debe subir documento exitosamente con mutation', async () => {
      const mockFile = new File(['content'], 'incapacidad.pdf', {
        type: 'application/pdf',
      });

      const mockResponse: DocumentoResponse = {
        id: '123e4567-e89b-12d3-a456-426614174010',
        tipo_documento: 'INCAPACIDAD_MEDICA',
        nombre_archivo: 'incapacidad.pdf',
        mime_type: 'application/pdf',
        tamanio_bytes: 1024,
        created_at: '2026-01-16T10:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValueOnce({ data: mockResponse });

      const { result } = renderHook(() => useUploadDocumento(), { wrapper });

      result.current.mutate({
        incapacidadId: '123e4567-e89b-12d3-a456-426614174000',
        archivo: mockFile,
        tipoDocumento: 'INCAPACIDAD_MEDICA',
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toEqual(mockResponse);
    });

    it('debe manejar errores en mutation', async () => {
      const mockFile = new File(['content'], 'documento.pdf', {
        type: 'application/pdf',
      });

      const mockError = {
        response: {
          status: 413,
          data: {
            error: {
              message: 'Archivo demasiado grande',
            },
          },
        },
      };

      vi.mocked(api.post).mockRejectedValueOnce(mockError);

      const { result } = renderHook(() => useUploadDocumento(), { wrapper });

      result.current.mutate({
        incapacidadId: '123e4567-e89b-12d3-a456-426614174000',
        archivo: mockFile,
        tipoDocumento: 'INCAPACIDAD_MEDICA',
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toEqual(mockError);
    });
  });

  describe('uploadMultipleDocumentos', () => {
    it('debe subir múltiples documentos exitosamente', async () => {
      const archivos = [
        {
          file: new File(['content1'], 'incapacidad.pdf', {
            type: 'application/pdf',
          }),
          tipo: 'INCAPACIDAD_MEDICA' as const,
        },
        {
          file: new File(['content2'], 'historia.pdf', {
            type: 'application/pdf',
          }),
          tipo: 'HISTORIA_CLINICA' as const,
        },
      ];

      const mockResponses: DocumentoResponse[] = [
        {
          id: '123e4567-e89b-12d3-a456-426614174010',
          tipo_documento: 'INCAPACIDAD_MEDICA',
          nombre_archivo: 'incapacidad.pdf',
          mime_type: 'application/pdf',
          tamanio_bytes: 1024,
          created_at: '2026-01-16T10:00:00Z',
        },
        {
          id: '123e4567-e89b-12d3-a456-426614174011',
          tipo_documento: 'HISTORIA_CLINICA',
          nombre_archivo: 'historia.pdf',
          mime_type: 'application/pdf',
          tamanio_bytes: 2048,
          created_at: '2026-01-16T10:00:00Z',
        },
      ];

      vi.mocked(api.post)
        .mockResolvedValueOnce({ data: mockResponses[0] })
        .mockResolvedValueOnce({ data: mockResponses[1] });

      const results = await uploadMultipleDocumentos(
        '123e4567-e89b-12d3-a456-426614174000',
        archivos
      );

      expect(results).toHaveLength(2);
      expect(results[0].success).toBe(true);
      expect(results[0].data).toEqual(mockResponses[0]);
      expect(results[1].success).toBe(true);
      expect(results[1].data).toEqual(mockResponses[1]);
    });

    it('debe manejar errores parciales', async () => {
      const archivos = [
        {
          file: new File(['content1'], 'incapacidad.pdf', {
            type: 'application/pdf',
          }),
          tipo: 'INCAPACIDAD_MEDICA' as const,
        },
        {
          file: new File(['content2'], 'historia.pdf', {
            type: 'application/pdf',
          }),
          tipo: 'HISTORIA_CLINICA' as const,
        },
      ];

      const mockResponse: DocumentoResponse = {
        id: '123e4567-e89b-12d3-a456-426614174010',
        tipo_documento: 'INCAPACIDAD_MEDICA',
        nombre_archivo: 'incapacidad.pdf',
        mime_type: 'application/pdf',
        tamanio_bytes: 1024,
        created_at: '2026-01-16T10:00:00Z',
      };

      const mockError = {
        response: {
          status: 400,
          data: {
            error: {
              message: 'Archivo no válido',
            },
          },
        },
      };

      vi.mocked(api.post)
        .mockResolvedValueOnce({ data: mockResponse })
        .mockRejectedValueOnce(mockError);

      const results = await uploadMultipleDocumentos(
        '123e4567-e89b-12d3-a456-426614174000',
        archivos
      );

      expect(results).toHaveLength(2);
      expect(results[0].success).toBe(true);
      expect(results[0].data).toEqual(mockResponse);
      expect(results[1].success).toBe(false);
      expect(results[1].error).toBe('Archivo no válido');
    });

    it('debe subir documentos de forma secuencial', async () => {
      const archivos = [
        {
          file: new File(['content1'], 'doc1.pdf', { type: 'application/pdf' }),
          tipo: 'INCAPACIDAD_MEDICA' as const,
        },
        {
          file: new File(['content2'], 'doc2.pdf', { type: 'application/pdf' }),
          tipo: 'HISTORIA_CLINICA' as const,
        },
      ];

      const callOrder: number[] = [];

      vi.mocked(api.post).mockImplementation(async () => {
        callOrder.push(Date.now());
        await new Promise((resolve) => setTimeout(resolve, 10));
        return {
          data: {
            id: '123e4567-e89b-12d3-a456-426614174010',
            tipo_documento: 'INCAPACIDAD_MEDICA',
            nombre_archivo: 'doc.pdf',
            mime_type: 'application/pdf',
            tamanio_bytes: 1024,
            created_at: '2026-01-16T10:00:00Z',
          },
        };
      });

      await uploadMultipleDocumentos(
        '123e4567-e89b-12d3-a456-426614174000',
        archivos
      );

      // Verificar que las llamadas fueron secuenciales (segunda llamada después de la primera)
      expect(callOrder).toHaveLength(2);
      expect(callOrder[1]).toBeGreaterThanOrEqual(callOrder[0]);
    });

    it('debe retornar array vacío si no hay archivos', async () => {
      const results = await uploadMultipleDocumentos(
        '123e4567-e89b-12d3-a456-426614174000',
        []
      );

      expect(results).toEqual([]);
      expect(api.post).not.toHaveBeenCalled();
    });
  });
});
