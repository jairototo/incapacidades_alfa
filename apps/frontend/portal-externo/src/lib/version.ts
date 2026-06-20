/**
 * Versión de la aplicación, inyectada en build-time desde package.json
 * (vite.config.ts `define.__APP_VERSION__`). El guard evita un ReferenceError
 * en contextos donde el define no se aplique.
 */
export const APP_VERSION =
  typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '0.0.0';
