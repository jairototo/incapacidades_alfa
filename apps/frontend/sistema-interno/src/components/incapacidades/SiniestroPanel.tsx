/**
 * SiniestroPanel — muestra el siniestro vinculado o la lista de candidatos.
 *
 * Lógica:
 * - Si incapacidad.siniestro_id está definido: panel de solo lectura con datos del siniestro.
 * - Si no hay siniestro_id y tipo === 'ARL': carga candidatos via API y muestra selector.
 * - Si tipo !== 'ARL': no renderiza nada.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle, Link, AlertCircle } from 'lucide-react';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';

import { incapacidadService } from '@/services/incapacidadService';
import type { Incapacidad, SiniestroBasic } from '@/types/incapacidad';

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface SiniestroPanelProps {
  incapacidad: Incapacidad;
  onVinculated?: () => void;
}

// ---------------------------------------------------------------------------
// Sub-component: linked siniestro (read-only)
// ---------------------------------------------------------------------------

function SiniestroVinculado({ incapacidad }: { incapacidad: Incapacidad }) {
  const siniestro = incapacidad.siniestro;
  const fechaFormateada = siniestro?.fecha_siniestro
    ? new Date(siniestro.fecha_siniestro + 'T00:00:00').toLocaleDateString('es-CO')
    : '—';
  const descripcionTruncada = siniestro?.descripcion
    ? siniestro.descripcion.length > 100
      ? siniestro.descripcion.slice(0, 100) + '…'
      : siniestro.descripcion
    : '—';

  return (
    <Card className="p-5 bg-green-50 border-green-300" data-testid="siniestro-vinculado">
      <div className="flex items-start gap-3">
        <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <h3 className="font-semibold text-green-900">Siniestro Vinculado</h3>
          <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
            <div>
              <span className="text-green-800 font-medium">Número:</span>{' '}
              <span className="font-mono">{incapacidad.numero_siniestro ?? siniestro?.numero_siniestro ?? '—'}</span>
            </div>
            <div>
              <span className="text-green-800 font-medium">Fecha:</span>{' '}
              {fechaFormateada}
            </div>
            <div>
              <span className="text-green-800 font-medium">Tipo:</span>{' '}
              <Badge variant="secondary" className="text-xs">
                {siniestro?.tipo_siniestro ?? '—'}
              </Badge>
            </div>
            <div>
              <span className="text-green-800 font-medium">Estado:</span>{' '}
              <Badge variant="outline" className="text-xs">
                {siniestro?.estado ?? '—'}
              </Badge>
            </div>
            <div className="col-span-2">
              <span className="text-green-800 font-medium">Descripción:</span>{' '}
              {descripcionTruncada}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Sub-component: candidate list
// ---------------------------------------------------------------------------

function SiniestrosCandidatos({
  incapacidad,
  onVinculated,
}: {
  incapacidad: Incapacidad;
  onVinculated?: () => void;
}) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: candidatos, isLoading } = useQuery({
    queryKey: ['siniestros-candidatos', incapacidad.id],
    queryFn: () => incapacidadService.getSiniestrosCandidatos(incapacidad.id),
    enabled: !!incapacidad.id,
  });

  const vincularMutation = useMutation({
    mutationFn: (siniestroId: string) =>
      incapacidadService.vincularSiniestro(incapacidad.id, siniestroId),
    onSuccess: () => {
      toast({
        title: 'Siniestro vinculado',
        description: 'El siniestro fue vinculado exitosamente a esta incapacidad.',
      });
      queryClient.invalidateQueries({ queryKey: ['incapacidad', incapacidad.id] });
      onVinculated?.();
    },
    onError: (error: any) => {
      toast({
        title: 'Error al vincular',
        description:
          error?.response?.data?.detail ?? 'No se pudo vincular el siniestro.',
        variant: 'destructive',
      });
    },
  });

  // Must be declared before any early returns to satisfy Rules of Hooks
  const iniciarCreacionMutation = useMutation({
    mutationFn: () =>
      incapacidadService.auditarSolicitarCreacionSiniestro(
        incapacidad.id,
        'Auditor solicitó creación de siniestro: no se encontraron candidatos locales'
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', incapacidad.id] });
      toast({
        title: 'Siniestro en creación',
        description:
          'La incapacidad pasó a CREACION_SINIESTRO. Un administrador la completará.',
      });
      onVinculated?.();
    },
    onError: (error: any) => {
      toast({
        title: 'Error al solicitar creación de siniestro',
        description:
          error?.response?.data?.detail ?? 'No se pudo solicitar la creación del siniestro',
        variant: 'destructive',
      });
    },
  });

  if (isLoading) {
    return (
      <Card className="p-5" data-testid="siniestro-loading">
        <div className="flex items-center gap-3 animate-pulse">
          <div className="h-4 w-4 rounded-full bg-slate-200" />
          <div className="h-4 w-48 rounded bg-slate-200" />
        </div>
      </Card>
    );
  }

  if (!candidatos || candidatos.length === 0) {
    return (
      <Card className="p-5 bg-slate-50 border-slate-200" data-testid="siniestro-empty">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-slate-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium text-slate-700">Sin siniestro vinculado</p>
            <p className="text-sm text-slate-500 mt-1">
              No se encontraron siniestros candidatos.
            </p>
            <Button
              variant="outline"
              onClick={() => iniciarCreacionMutation.mutate()}
              disabled={iniciarCreacionMutation.isPending}
              className="mt-3"
            >
              {iniciarCreacionMutation.isPending
                ? 'Solicitando...'
                : 'Ninguno corresponde / Crear siniestro'}
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5" data-testid="siniestro-candidatos">
      <div className="flex items-center gap-2 mb-4">
        <Link className="h-5 w-5 text-blue-600" />
        <h3 className="font-semibold text-slate-800">
          Siniestros candidatos ({candidatos.length})
        </h3>
      </div>

      <div className="space-y-3">
        {candidatos.map((s: SiniestroBasic) => {
          const fechaFormateada = new Date(s.fecha_siniestro + 'T00:00:00').toLocaleDateString('es-CO');
          const descripcionTruncada =
            s.descripcion.length > 100 ? s.descripcion.slice(0, 100) + '…' : s.descripcion;

          return (
            <label
              key={s.id}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedId === s.id
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <input
                type="radio"
                name="siniestro-candidato"
                value={s.id}
                checked={selectedId === s.id}
                onChange={() => setSelectedId(s.id)}
                className="mt-1 accent-blue-600"
                data-testid={`radio-siniestro-${s.id}`}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono font-medium text-sm">{s.numero_siniestro}</span>
                  <Badge variant="secondary" className="text-xs">
                    {s.tipo_siniestro}
                  </Badge>
                  <span className="text-xs text-slate-500">{fechaFormateada}</span>
                </div>
                <p className="text-sm text-slate-600 mt-0.5 truncate">{descripcionTruncada}</p>
              </div>
            </label>
          );
        })}
      </div>

      <div className="mt-4 flex justify-end">
        <Button
          onClick={() => {
            if (selectedId) vincularMutation.mutate(selectedId);
          }}
          disabled={!selectedId || vincularMutation.isPending}
          size="sm"
        >
          {vincularMutation.isPending ? 'Vinculando…' : 'Vincular este siniestro'}
        </Button>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

export function SiniestroPanel({ incapacidad, onVinculated }: SiniestroPanelProps) {
  // Solo aplica a incapacidades ARL
  if (incapacidad.tipo !== 'ARL') {
    return null;
  }

  // Ya tiene siniestro vinculado
  if (incapacidad.siniestro_id) {
    return <SiniestroVinculado incapacidad={incapacidad} />;
  }

  // Sin siniestro: mostrar candidatos
  return (
    <SiniestrosCandidatos incapacidad={incapacidad} onVinculated={onVinculated} />
  );
}
