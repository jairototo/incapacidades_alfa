/**
 * Tests para el servicio de consulta pública de incapacidades.
 * 
 * Valida:
 * - Consulta por número de radicación
 * - Consulta por documento de identidad
 * - Generación de URL de descarga temporal
 * - Manejo de errores (404, 403, 400)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { consultaService } from '../consultaService';
import api from '@/services/api';
import type { ConsultaIncapacidadResponse, PresignedUrlResponse } from '@/types/consulta';

// Mock del módulo api
vi.mock('@/services/api');

describe('consultaService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('consultarPorNumero', () => {
    it('debe consultar incapacidad por número exitosamente', async () => {
      const mockNumero = 'INC-ARL-20260117-0001';
      const mockResponse: ConsultaIncapacidadResponse = {
        numero: mockNumero,
        tipo: 'ARL',
        estado: 'EN_AUDITORIA',
        fecha_inicio: '2026-01-10',
        fecha_fin: '2026-01-20',
        dias_totales: 10,
        diagnostico_cie10: 'S62.5',
        descripcion_diagnostico: 'Fractura de pulgar',
        observaciones_publicas: null,
        nombre_completo: 'Juan Pérez García',
        tipo_documento: 'CC',
        eps: null,
        created_at: '2026-01-17T10:00:00Z',
        updated_at: '2026-01-17T10:00:00Z',
        historial_estados: [
          {
            estado: 'RADICADA',
            fecha_cambio: '2026-01-17T10:00:00Z',
            observaciones: null,
          },
          {
            estado: 'EN_AUDITORIA',
            fecha_cambio: '2026-01-17T14:30:00Z',
            observaciones: 'Revisión iniciada',
          },
        ],
        documentos: [
          {
            id: '550e8400-e29b-41d4-a716-446655440001',
            nombre_archivo: 'incapacidad_medica.pdf',
            tipo_documento: 'INCAPACIDAD_MEDICA',
            tamanio_kb: 245,
            fecha_upload: '2026-01-17T10:05:00Z',
          },
        ],
      };

      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse });

      const result = await consultaService.consultarPorNumero(mockNumero);

      expect(api.get).toHaveBeenCalledWith('/incapacidades/consultar', {
        params: { numero: mockNumero },
      });
      expect(result).toEqual(mockResponse);
      expect(result.numero).toBe(mockNumero);
      expect(result.estado).toBe('EN_AUDITORIA');
      expect(result.historial_estados).toHaveLength(2);
      expect(result.documentos).toHaveLength(1);
    });

    it('debe manejar error 404 cuando la incapacidad no existe', async () => {
      const mockNumero = 'INC-ARL-20260117-9999';
      const mockError = {
        response: {
          status: 404,
          data: {
            error: {
              code: 'NOT_FOUND',
              message: `Incapacidad con número ${mockNumero} no encontrada`,
            },
          },
        },
      };

      vi.mocked(api.get).mockRejectedValueOnce(mockError);

      await expect(consultaService.consultarPorNumero(mockNumero)).rejects.toEqual(mockError);
      expect(api.get).toHaveBeenCalledWith('/incapacidades/consultar', {
        params: { numero: mockNumero },
      });
    });

    it('debe manejar error 400 para parámetros inválidos', async () => {
      const mockNumeroInvalido = 'INVALID-FORMAT';
      const mockError = {
        response: {
          status: 400,
          data: {
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Parámetros de consulta inválidos',
            },
          },
        },
      };

      vi.mocked(api.get).mockRejectedValueOnce(mockError);

      await expect(consultaService.consultarPorNumero(mockNumeroInvalido)).rejects.toEqual(mockError);
    });
  });

  describe('consultarPorDocumento', () => {
    it('debe consultar incapacidad por documento exitosamente', async () => {
      const mockDocumento = '1234567890';
      const mockTipoDocumento = 'CC';
      const mockResponse: ConsultaIncapacidadResponse = {
        numero: 'INC-SALUD-20260115-0042',
        tipo: 'SALUD',
        estado: 'APROBADA',
        fecha_inicio: '2026-01-08',
        fecha_fin: '2026-01-14',
        dias_totales: 6,
        diagnostico_cie10: 'J06.9',
        descripcion_diagnostico: 'Infección respiratoria aguda',
        observaciones_publicas: null,
        nombre_completo: 'María López Gómez',
        tipo_documento: mockTipoDocumento,
        eps: null,
        created_at: '2026-01-15T09:00:00Z',
        updated_at: '2026-01-15T09:00:00Z',
        historial_estados: [
          {
            estado: 'RADICADA',
            fecha_cambio: '2026-01-15T09:00:00Z',
            observaciones: null,
          },
          {
            estado: 'EN_AUDITORIA',
            fecha_cambio: '2026-01-15T11:00:00Z',
            observaciones: null,
          },
          {
            estado: 'APROBADA',
            fecha_cambio: '2026-01-16T15:45:00Z',
            observaciones: 'Documentación completa',
          },
        ],
        documentos: [
          {
            id: '550e8400-e29b-41d4-a716-446655440010',
            nombre_archivo: 'cedula_paciente.pdf',
            tipo_documento: 'CEDULA',
            tamanio_kb: 120,
            fecha_upload: '2026-01-15T09:10:00Z',
          },
          {
            id: '550e8400-e29b-41d4-a716-446655440011',
            nombre_archivo: 'incapacidad.pdf',
            tipo_documento: 'INCAPACIDAD_MEDICA',
            tamanio_kb: 310,
            fecha_upload: '2026-01-15T09:12:00Z',
          },
        ],
      };

      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse });

      const result = await consultaService.consultarPorDocumento(mockDocumento, mockTipoDocumento);

      expect(api.get).toHaveBeenCalledWith('/incapacidades/consultar', {
        params: {
          documento: mockDocumento,
          tipo_documento: mockTipoDocumento,
        },
      });
      expect(result).toEqual(mockResponse);
      expect(result.tipo_documento).toBe(mockTipoDocumento);
      expect(result.tipo).toBe('SALUD');
      expect(result.documentos).toHaveLength(2);
    });

    it('debe manejar error 404 cuando no existe incapacidad para el documento', async () => {
      const mockDocumento = '9999999999';
      const mockTipoDocumento = 'CC';
      const mockError = {
        response: {
          status: 404,
          data: {
            error: {
              code: 'NOT_FOUND',
              message: 'No se encontró incapacidad para el documento especificado',
            },
          },
        },
      };

      vi.mocked(api.get).mockRejectedValueOnce(mockError);

      await expect(
        consultaService.consultarPorDocumento(mockDocumento, mockTipoDocumento)
      ).rejects.toEqual(mockError);
    });
  });

  describe('descargarDocumento', () => {
    it('debe generar URL de descarga temporal exitosamente', async () => {
      const mockNumero = 'INC-ARL-20260117-0001';
      const mockDocumentoId = '550e8400-e29b-41d4-a716-446655440001';
      const mockResponse: PresignedUrlResponse = {
        url: 'https://storage.example.com/incapacidades/550e8400/incapacidad_medica.pdf?token=xyz123&expires=1738054200',
        expires_in: 900, // 15 minutos
        nombre_archivo: 'incapacidad_medica.pdf',
        tipo_documento: 'INCAPACIDAD_MEDICA',
      };

      vi.mocked(api.get).mockResolvedValueOnce({ data: mockResponse });

      const result = await consultaService.descargarDocumento(mockNumero, mockDocumentoId);

      expect(api.get).toHaveBeenCalledWith(
        `/incapacidades/${mockNumero}/documentos/${mockDocumentoId}/download`
      );
      expect(result).toEqual(mockResponse);
      expect(result.url).toContain('token=');
      expect(result.expires_in).toBe(900);
      expect(result.tipo_documento).toBe('INCAPACIDAD_MEDICA');
    });

    it('debe manejar error 404 cuando el documento no existe', async () => {
      const mockNumero = 'INC-ARL-20260117-0001';
      const mockDocumentoId = '550e8400-e29b-41d4-a716-000000000000';
      const mockError = {
        response: {
          status: 404,
          data: {
            error: {
              code: 'NOT_FOUND',
              message: `Documento ${mockDocumentoId} no encontrado`,
            },
          },
        },
      };

      vi.mocked(api.get).mockRejectedValueOnce(mockError);

      await expect(
        consultaService.descargarDocumento(mockNumero, mockDocumentoId)
      ).rejects.toEqual(mockError);
    });

    it('debe manejar error 403 cuando el documento no es público', async () => {
      const mockNumero = 'INC-ARL-20260117-0001';
      const mockDocumentoId = '550e8400-e29b-41d4-a716-446655440020';
      const mockError = {
        response: {
          status: 403,
          data: {
            error: {
              code: 'FORBIDDEN',
              message: 'El documento no es de acceso público',
            },
          },
        },
      };

      vi.mocked(api.get).mockRejectedValueOnce(mockError);

      await expect(
        consultaService.descargarDocumento(mockNumero, mockDocumentoId)
      ).rejects.toEqual(mockError);
    });

    it('debe manejar error 403 cuando el documento no pertenece a la incapacidad', async () => {
      const mockNumero = 'INC-ARL-20260117-0001';
      const mockDocumentoId = '550e8400-e29b-41d4-a716-446655440099';
      const mockError = {
        response: {
          status: 403,
          data: {
            error: {
              code: 'FORBIDDEN',
              message: 'El documento no pertenece a la incapacidad especificada',
            },
          },
        },
      };

      vi.mocked(api.get).mockRejectedValueOnce(mockError);

      await expect(
        consultaService.descargarDocumento(mockNumero, mockDocumentoId)
      ).rejects.toEqual(mockError);
    });

    it('debe generar múltiples URLs para diferentes documentos', async () => {
      const mockNumero = 'INC-SALUD-20260115-0042';
      const documentos = [
        {
          id: '550e8400-e29b-41d4-a716-446655440010',
          nombre: 'cedula.pdf',
          tipo: 'CEDULA',
        },
        {
          id: '550e8400-e29b-41d4-a716-446655440011',
          nombre: 'incapacidad.pdf',
          tipo: 'INCAPACIDAD_MEDICA',
        },
      ];

      const mockResponse1: PresignedUrlResponse = {
        url: 'https://storage.example.com/docs/cedula.pdf?token=abc',
        expires_in: 900,
        nombre_archivo: 'cedula.pdf',
        tipo_documento: 'CEDULA',
      };

      const mockResponse2: PresignedUrlResponse = {
        url: 'https://storage.example.com/docs/incapacidad.pdf?token=xyz',
        expires_in: 900,
        nombre_archivo: 'incapacidad.pdf',
        tipo_documento: 'INCAPACIDAD_MEDICA',
      };

      vi.mocked(api.get)
        .mockResolvedValueOnce({ data: mockResponse1 })
        .mockResolvedValueOnce({ data: mockResponse2 });

      const [result1, result2] = await Promise.all([
        consultaService.descargarDocumento(mockNumero, documentos[0].id),
        consultaService.descargarDocumento(mockNumero, documentos[1].id),
      ]);

      expect(result1.nombre_archivo).toBe('cedula.pdf');
      expect(result2.nombre_archivo).toBe('incapacidad.pdf');
      expect(api.get).toHaveBeenCalledTimes(2);
    });
  });
});
