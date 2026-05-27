/**
 * Utilidades para formateo de valores.
 * 
 * Funciones helper para formatear fechas, monedas y otros valores
 * de forma consistente en toda la aplicación.
 */

/**
 * Formatea una fecha ISO a formato local colombiano.
 * 
 * @param fechaISO - Fecha en formato ISO (ej: "2026-01-17T10:00:00Z")
 * @param opciones - Opciones de formateo (opcional)
 * @returns Fecha formateada (ej: "17 de enero de 2026")
 * 
 * @example
 * ```typescript
 * formatearFecha("2026-01-17T10:00:00Z")
 * // "17 de enero de 2026"
 * 
 * formatearFecha("2026-01-17", { dateStyle: 'short' })
 * // "17/01/2026"
 * ```
 */
export const formatearFecha = (
  fechaISO: string,
  opciones?: Intl.DateTimeFormatOptions
): string => {
  const opcionesPorDefecto: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  };

  return new Date(fechaISO).toLocaleDateString('es-CO', opciones || opcionesPorDefecto);
};

/**
 * Formatea una fecha ISO a formato de fecha y hora local.
 * 
 * @param fechaISO - Fecha en formato ISO
 * @returns Fecha y hora formateada (ej: "17 de enero de 2026, 10:00:00 a. m.")
 * 
 * @example
 * ```typescript
 * formatearFechaHora("2026-01-17T10:00:00Z")
 * // "17 de enero de 2026, 10:00:00 a. m."
 * ```
 */
export const formatearFechaHora = (fechaISO: string): string => {
  return new Date(fechaISO).toLocaleString('es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Formatea una fecha ISO a formato corto.
 * 
 * @param fechaISO - Fecha en formato ISO
 * @returns Fecha formateada (ej: "17/01/2026")
 * 
 * @example
 * ```typescript
 * formatearFechaCorta("2026-01-17T10:00:00Z")
 * // "17/01/2026"
 * ```
 */
export const formatearFechaCorta = (fechaISO: string): string => {
  return new Date(fechaISO).toLocaleDateString('es-CO', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
};

/**
 * Formatea un número como moneda colombiana (COP).
 * 
 * @param valor - Valor numérico
 * @param opciones - Opciones de formateo (opcional)
 * @returns Valor formateado (ej: "$50.000")
 * 
 * @example
 * ```typescript
 * formatearMoneda(50000)
 * // "$50.000"
 * 
 * formatearMoneda(1234567.89)
 * // "$1.234.568"
 * ```
 */
export const formatearMoneda = (
  valor: number,
  opciones?: Intl.NumberFormatOptions
): string => {
  const opcionesPorDefecto: Intl.NumberFormatOptions = {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  };

  return new Intl.NumberFormat('es-CO', opciones || opcionesPorDefecto).format(valor);
};

/**
 * Formatea un número entero con separadores de miles.
 * 
 * @param valor - Valor numérico
 * @returns Valor formateado (ej: "1.234.567")
 * 
 * @example
 * ```typescript
 * formatearNumero(1234567)
 * // "1.234.567"
 * ```
 */
export const formatearNumero = (valor: number): string => {
  return new Intl.NumberFormat('es-CO').format(valor);
};

/**
 * Formatea un tamaño de archivo en KB a una representación legible.
 * 
 * @param kb - Tamaño en kilobytes
 * @returns Tamaño formateado (ej: "1.5 MB", "250 KB")
 * 
 * @example
 * ```typescript
 * formatearTamanioArchivo(250)
 * // "250 KB"
 * 
 * formatearTamanioArchivo(1536)
 * // "1.5 MB"
 * 
 * formatearTamanioArchivo(2097152)
 * // "2 GB"
 * ```
 */
export const formatearTamanioArchivo = (kb: number): string => {
  if (kb < 1024) {
    return `${kb} KB`;
  } else if (kb < 1024 * 1024) {
    return `${(kb / 1024).toFixed(1)} MB`;
  } else {
    return `${(kb / (1024 * 1024)).toFixed(1)} GB`;
  }
};

/**
 * Formatea un texto para capitalizar la primera letra de cada palabra.
 * 
 * @param texto - Texto a formatear
 * @returns Texto capitalizado (ej: "Juan Pérez García")
 * 
 * @example
 * ```typescript
 * capitalizarTexto("juan pérez garcía")
 * // "Juan Pérez García"
 * 
 * capitalizarTexto("EN_AUDITORIA")
 * // "En Auditoria"
 * ```
 */
export const capitalizarTexto = (texto: string): string => {
  return texto
    .toLowerCase()
    .replace(/_/g, ' ')
    .split(' ')
    .map((palabra) => palabra.charAt(0).toUpperCase() + palabra.slice(1))
    .join(' ');
};

/**
 * Formatea un estado de incapacidad para mostrar.
 * 
 * @param estado - Estado de la incapacidad
 * @returns Estado formateado (ej: "En Auditoría")
 * 
 * @example
 * ```typescript
 * formatearEstado("EN_AUDITORIA")
 * // "En Auditoría"
 * 
 * formatearEstado("APROBADA")
 * // "Aprobada"
 * ```
 */
export const formatearEstado = (estado: string): string => {
  const mapaEstados: Record<string, string> = {
    RADICADA: 'Radicada',
    EN_AUDITORIA: 'En Auditoría',
    OBSERVADA: 'Observada',
    APROBADA: 'Aprobada',
    RECHAZADA: 'Rechazada',
    EN_PAGO: 'En Pago',
    PAGADA: 'Pagada',
    CANCELADA: 'Cancelada',
  };

  return mapaEstados[estado] || capitalizarTexto(estado);
};
