/**
 * Utilidades para validación y manipulación de archivos
 */

export const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'image/jpeg',
  'image/jpg',
  'image/png',
] as const;

export const ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png'] as const;

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

export type AllowedMimeType = typeof ALLOWED_MIME_TYPES[number];
export type AllowedExtension = typeof ALLOWED_EXTENSIONS[number];

/**
 * Valida si el tipo MIME del archivo es permitido
 */
export function validateFileType(file: File): boolean {
  return ALLOWED_MIME_TYPES.includes(file.type as AllowedMimeType);
}

/**
 * Valida si el tamaño del archivo no excede el límite
 */
export function validateFileSize(file: File, maxSize: number = MAX_FILE_SIZE): boolean {
  return file.size <= maxSize;
}

/**
 * Formatea el tamaño de un archivo en bytes a una cadena legible
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Obtiene la extensión de un archivo
 */
export function getFileExtension(filename: string): string {
  const parts = filename.split('.');
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
}

/**
 * Determina si un archivo es una imagen
 */
export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/');
}

/**
 * Determina si un archivo es un PDF
 */
export function isPdfFile(file: File): boolean {
  return file.type === 'application/pdf';
}

/**
 * Genera un ID único para un archivo
 */
export function generateFileId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Valida múltiples aspectos de un archivo
 */
export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

export function validateFile(file: File, maxSize: number = MAX_FILE_SIZE): FileValidationResult {
  if (!validateFileType(file)) {
    return {
      valid: false,
      error: `Tipo de archivo no permitido. Solo se aceptan: ${ALLOWED_EXTENSIONS.join(', ').toUpperCase()}`,
    };
  }
  
  if (!validateFileSize(file, maxSize)) {
    return {
      valid: false,
      error: `El archivo excede el tamaño máximo de ${formatFileSize(maxSize)}`,
    };
  }
  
  return { valid: true };
}
