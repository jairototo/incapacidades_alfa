import { useCallback } from 'react';

export type ToastVariant = 'default' | 'destructive';

export interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
}

let toastCounter = 0;

const toastListeners: Array<(toast: Toast) => void> = [];

export function useToast() {
  const toast = useCallback(
    ({ title, description, variant = 'default' }: Omit<Toast, 'id'>) => {
      const id = `toast-${++toastCounter}`;
      const newToast: Toast = { id, title, description, variant };

      // Notificar a todos los listeners
      toastListeners.forEach((listener) => listener(newToast));

      // Auto-dismiss después de 5 segundos
      setTimeout(() => {
        toastListeners.forEach((listener) =>
          listener({ ...newToast, id: `dismiss-${id}` })
        );
      }, 5000);

      return newToast;
    },
    []
  );

  return { toast };
}

/**
 * Hook para escuchar toasts globalmente (usado por ToastProvider)
 */
export function useToastListener(callback: (toast: Toast) => void) {
  toastListeners.push(callback);
  return () => {
    const index = toastListeners.indexOf(callback);
    if (index > -1) {
      toastListeners.splice(index, 1);
    }
  };
}
