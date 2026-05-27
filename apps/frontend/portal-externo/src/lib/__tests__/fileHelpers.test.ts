import { describe, it, expect } from 'vitest';
import {
  validateFileType,
  validateFileSize,
  formatFileSize,
  getFileExtension,
  isImageFile,
  isPdfFile,
  validateFile,
  MAX_FILE_SIZE,
  ALLOWED_MIME_TYPES,
} from '@/lib/fileHelpers';

describe('fileHelpers', () => {
  describe('validateFileType', () => {
    it('debe aceptar archivos PDF', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      expect(validateFileType(file)).toBe(true);
    });

    it('debe aceptar archivos JPEG', () => {
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
      expect(validateFileType(file)).toBe(true);
    });

    it('debe aceptar archivos PNG', () => {
      const file = new File(['content'], 'test.png', { type: 'image/png' });
      expect(validateFileType(file)).toBe(true);
    });

    it('debe rechazar archivos no permitidos', () => {
      const file = new File(['content'], 'test.doc', { type: 'application/msword' });
      expect(validateFileType(file)).toBe(false);
    });

    it('debe rechazar archivos con tipo desconocido', () => {
      const file = new File(['content'], 'test.xyz', { type: 'application/xyz' });
      expect(validateFileType(file)).toBe(false);
    });
  });

  describe('validateFileSize', () => {
    it('debe aceptar archivos menores al límite', () => {
      const file = new File(['a'.repeat(100)], 'test.pdf', { type: 'application/pdf' });
      expect(validateFileSize(file, 1024)).toBe(true);
    });

    it('debe aceptar archivos iguales al límite', () => {
      const content = 'a'.repeat(1024);
      const file = new File([content], 'test.pdf', { type: 'application/pdf' });
      expect(validateFileSize(file, 1024)).toBe(true);
    });

    it('debe rechazar archivos mayores al límite', () => {
      const content = 'a'.repeat(MAX_FILE_SIZE + 1);
      const file = new File([content], 'test.pdf', { type: 'application/pdf' });
      expect(validateFileSize(file)).toBe(false);
    });

    it('debe usar MAX_FILE_SIZE por defecto', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      expect(validateFileSize(file)).toBe(true);
    });
  });

  describe('formatFileSize', () => {
    it('debe formatear 0 bytes', () => {
      expect(formatFileSize(0)).toBe('0 Bytes');
    });

    it('debe formatear bytes', () => {
      expect(formatFileSize(500)).toBe('500 Bytes');
    });

    it('debe formatear kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(1536)).toBe('1.5 KB');
    });

    it('debe formatear megabytes', () => {
      expect(formatFileSize(1048576)).toBe('1 MB');
      expect(formatFileSize(5242880)).toBe('5 MB');
    });

    it('debe formatear gigabytes', () => {
      expect(formatFileSize(1073741824)).toBe('1 GB');
    });
  });

  describe('getFileExtension', () => {
    it('debe extraer extensión de archivo simple', () => {
      expect(getFileExtension('documento.pdf')).toBe('pdf');
    });

    it('debe extraer extensión de archivo con múltiples puntos', () => {
      expect(getFileExtension('archivo.backup.tar.gz')).toBe('gz');
    });

    it('debe retornar cadena vacía si no hay extensión', () => {
      expect(getFileExtension('archivo')).toBe('');
    });

    it('debe convertir a minúsculas', () => {
      expect(getFileExtension('DOCUMENTO.PDF')).toBe('pdf');
    });
  });

  describe('isImageFile', () => {
    it('debe identificar archivos de imagen JPEG', () => {
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
      expect(isImageFile(file)).toBe(true);
    });

    it('debe identificar archivos de imagen PNG', () => {
      const file = new File(['content'], 'test.png', { type: 'image/png' });
      expect(isImageFile(file)).toBe(true);
    });

    it('debe rechazar archivos no imagen', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      expect(isImageFile(file)).toBe(false);
    });
  });

  describe('isPdfFile', () => {
    it('debe identificar archivos PDF', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      expect(isPdfFile(file)).toBe(true);
    });

    it('debe rechazar archivos no PDF', () => {
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
      expect(isPdfFile(file)).toBe(false);
    });
  });

  describe('validateFile', () => {
    it('debe validar archivo correcto', () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      const result = validateFile(file);
      
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('debe rechazar tipo de archivo incorrecto', () => {
      const file = new File(['content'], 'test.doc', { type: 'application/msword' });
      const result = validateFile(file);
      
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Tipo de archivo no permitido');
    });

    it('debe rechazar archivo que excede tamaño máximo', () => {
      const content = 'a'.repeat(MAX_FILE_SIZE + 1);
      const file = new File([content], 'test.pdf', { type: 'application/pdf' });
      const result = validateFile(file);
      
      expect(result.valid).toBe(false);
      expect(result.error).toContain('excede el tamaño máximo');
    });

    it('debe usar límite personalizado', () => {
      const file = new File(['a'.repeat(2000)], 'test.pdf', { type: 'application/pdf' });
      const result = validateFile(file, 1000);
      
      expect(result.valid).toBe(false);
      expect(result.error).toContain('excede el tamaño máximo');
    });
  });

  describe('constantes', () => {
    it('debe exportar ALLOWED_MIME_TYPES correctamente', () => {
      expect(ALLOWED_MIME_TYPES).toContain('application/pdf');
      expect(ALLOWED_MIME_TYPES).toContain('image/jpeg');
      expect(ALLOWED_MIME_TYPES).toContain('image/png');
    });

    it('debe tener MAX_FILE_SIZE de 10MB', () => {
      expect(MAX_FILE_SIZE).toBe(10 * 1024 * 1024);
    });
  });
});
