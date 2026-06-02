import { useState } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

import { useDemoReset } from '@/application/hooks/usePortalUsers';
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  PageHeader,
  PageLayout,
} from '@/presentation/components/ui';

export function AdminPage() {
  const resetMut = useDemoReset();
  const [confirmText, setConfirmText] = useState('');

  function handleReset() {
    if (confirmText !== 'RESET') return;
    resetMut.mutate();
  }

  return (
    <PageLayout width="default">
      <PageHeader
        title="Operaciones administrativas"
        description="Acciones reservadas para administradores del portal."
      />

      <Card>
        <CardHeader
          title="Reset de demo"
          actions={<Badge variant="error">Destructivo</Badge>}
        />
        <CardBody>
          <p className="mb-4 inline-flex items-start gap-2 rounded-md bg-yellow-50 p-3 text-sm text-yellow-900">
            <AlertTriangle size={16} strokeWidth={1.75} aria-hidden className="mt-0.5" />
            <span>
              Esta acción <strong>borra todos los datos operativos</strong> de demostración
              (afiliaciones, novedades, FURAT, FUREP, ausencias, aportes, bitácora). No afecta
              empresas, trabajadores ni usuarios.
            </span>
          </p>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">
              Escribe <span className="font-mono">RESET</span> para confirmar
            </label>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              className="mt-1 block w-48 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-mono shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <Button
            variant="primary"
            disabled={confirmText !== 'RESET'}
            loading={resetMut.isPending}
            onClick={handleReset}
            leftIcon={<RotateCcw size={14} strokeWidth={1.75} aria-hidden />}
          >
            Ejecutar reset
          </Button>

          {resetMut.isSuccess && resetMut.data ? (
            <div className="mt-4 rounded-md border border-green-200 bg-green-50 p-3 text-sm">
              <p className="font-medium text-green-900">
                Reset ejecutado a las {new Date(resetMut.data.occurred_at).toLocaleString('es-CO')}
              </p>
              <ul className="mt-2 list-inside list-disc text-green-800">
                {resetMut.data.truncated_tables.map((t) => (
                  <li key={t} className="font-mono text-xs">
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {resetMut.isError ? (
            <p className="mt-4 text-sm text-red-600">No se pudo ejecutar el reset.</p>
          ) : null}
        </CardBody>
      </Card>
    </PageLayout>
  );
}
