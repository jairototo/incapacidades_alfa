/**
 * Utilidades de formato para fechas, monedas, etc.
 */

/**
 * Formatear fecha a formato local DD/MM/YYYY
 */
export function formatDate(dateString: string | Date): string {
  if (!dateString) return '-';
  
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
  
  return new Intl.DateTimeFormat('es-CO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date);
}

/**
 * Formatear fecha y hora a formato local DD/MM/YYYY HH:mm
 */
export function formatDateTime(dateString: string | Date): string {
  if (!dateString) return '-';
  
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
  
  return new Intl.DateTimeFormat('es-CO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

/**
 * Formatear moneda en pesos colombianos
 */
export function formatCurrency(value: number): string {
  if (value === null || value === undefined) return '-';
  
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Formatear número con separadores de miles
 */
export function formatNumber(value: number): string {
  if (value === null || value === undefined) return '-';
  
  return new Intl.NumberFormat('es-CO').format(value);
}

/**
 * Formatear bytes a tamaño legible (KB, MB, GB)
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Obtener nombre completo a partir de nombres y apellidos
 */
export function formatFullName(nombres: string, apellidos: string): string {
  return `${nombres} ${apellidos}`.trim();
}
