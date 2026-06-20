/**
 * Página de consulta de incapacidades para empresa (autenticada).
 *
 * Muestra la lista de incapacidades radicadas para la empresa del token
 * (filtrada en backend por `mi-empresa`), con filtros y un drawer de
 * detalle que reutiliza los componentes públicos DetalleIncapacidad +
 * TimelineEstados.
 */

import { useState, useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { FiltrosConsultaEmpresa } from '@/components/consulta/FiltrosConsultaEmpresa';
import { TablaIncapacidades } from '@/components/consulta/TablaIncapacidades';
import { DetalleIncapacidad } from '@/components/consulta/DetalleIncapacidad';
import { TimelineEstados } from '@/components/consulta/TimelineEstados';
import {
  useIncapacidadesDeMiEmpresa,
  type FiltrosConsulta,
  type IncapacidadListItem,
} from '@/services/consultaEmpresaService';
import { useConsultarPorNumero } from '@/hooks/useConsultaIncapacidad';
import type { ConsultaIncapacidadResponse } from '@/types/consulta';

// ─────────────────────────────────────────────────────────────────────────────
// Drawer
// ─────────────────────────────────────────────────────────────────────────────

interface DetalleDrawerProps {
  item: IncapacidadListItem;
  onClose: () => void;
}

function DetalleDrawer({ item, onClose }: DetalleDrawerProps) {
  const { data, isLoading, isError } = useConsultarPorNumero(item.numero);

  const closeBtnRef = useRef<HTMLButtonElement>(null);
  useEffect(() => { closeBtnRef.current?.focus(); }, []);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    /* Wrapper: positions backdrop + panel together */
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop — aria-hidden so screen readers skip it */}
      <div
        className="absolute inset-0 bg-black/40"
        aria-hidden="true"
        onClick={onClose}
      />
      {/* Panel */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={`Detalle incapacidad ${item.numero}`}
        className="relative w-full max-w-2xl bg-white shadow-2xl overflow-y-auto flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold text-foreground">
            Detalle — {item.numero}
          </h2>
          <button
            ref={closeBtnRef}
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Cerrar"
          >
            <X className="h-5 w-5" />
            <span className="sr-only">Cerrar</span>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 space-y-6">
          {isLoading && (
            <p className="text-sm text-muted-foreground py-12">
              Cargando…
            </p>
          )}

          {!isLoading && data && (
            <>
              <DetalleIncapacidad
                incapacidad={data as ConsultaIncapacidadResponse}
              />
              <TimelineEstados
                historial={(data as ConsultaIncapacidadResponse).historial_estados}
              />
            </>
          )}

          {isError && (
            <p className="text-sm text-destructive py-12">
              No se pudo cargar el detalle de la incapacidad.
            </p>
          )}
        </div>
      </aside>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export function ConsultaEmpresa() {
  const [filtros, setFiltros] = useState<FiltrosConsulta>({});
  const [selected, setSelected] = useState<IncapacidadListItem | null>(null);

  const { data: items = [], isLoading, isError } = useIncapacidadesDeMiEmpresa(filtros);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-white border-b border-border">
        <div className="container mx-auto px-4 py-6 max-w-7xl">
          <h1 className="text-2xl md:text-3xl font-bold text-foreground">
            Consulta de Incapacidades
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Visualiza y filtra las incapacidades radicadas por tu empresa
          </p>
        </div>
      </div>

      {/* Main */}
      <main className="container mx-auto px-4 py-8 max-w-7xl space-y-6">
        <FiltrosConsultaEmpresa value={filtros} onChange={setFiltros} />

        {isError && (
          <div role="alert" className="rounded-md border border-[#D92D20] bg-[#D92D20]/5 p-3 text-sm text-[#D92D20]">
            No se pudieron cargar las incapacidades. Intente nuevamente.
          </div>
        )}

        <TablaIncapacidades
          items={items}
          isLoading={isLoading}
          onSelect={(id) =>
            setSelected(items.find((i) => i.id === id) ?? null)
          }
        />
      </main>

      {/* Detail drawer */}
      {selected && (
        <DetalleDrawer item={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
