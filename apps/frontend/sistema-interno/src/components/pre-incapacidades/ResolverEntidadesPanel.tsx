import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Building2, User, Check } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import api from '@/lib/api';
import { useDebounce } from '@/hooks/useDebounce';
import type { PreIncapacidadDetalle } from '@/types/preIncapacidad';

interface EmpresaResult {
  id: string;
  nit: string;
  razon_social: string;
  estado: string;
}

interface EmpleadoResult {
  id: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  estado: string;
}

interface Props {
  preInc: PreIncapacidadDetalle;
  onEmpresaSelected: (nit: string, nombre: string) => void;
  onEmpleadoSelected: (tipoDoc: string, numero: string, nombres: string) => void;
}

function EmpresaSearch({
  currentNit,
  onSelected,
}: {
  currentNit: string | null;
  onSelected: (nit: string, nombre: string) => void;
}) {
  const [q, setQ] = useState('');
  const dq = useDebounce(q, 400);

  const { data, isLoading } = useQuery({
    queryKey: ['empresa-search', dq],
    queryFn: async () => {
      const { data } = await api.get<EmpresaResult[]>('/empresas/', {
        params: { search: dq, limit: 10 },
      });
      return data;
    },
    enabled: dq.length >= 2,
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Building2 className="h-4 w-4 text-slate-500" />
        <Label className="font-medium">Empresa</Label>
        {currentNit && (
          <Badge variant="outline" className="text-xs">
            NIT actual: {currentNit}
          </Badge>
        )}
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Buscar por NIT o razón social..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="pl-9"
        />
      </div>
      {isLoading && <p className="text-sm text-slate-500">Buscando...</p>}
      {data && data.length > 0 && (
        <div className="border rounded-md divide-y max-h-40 overflow-y-auto">
          {data.map((emp) => (
            <div
              key={emp.id}
              className="flex items-center justify-between p-2 hover:bg-slate-50 cursor-pointer"
              onClick={() => {
                onSelected(emp.nit, emp.razon_social);
                setQ('');
              }}
            >
              <div>
                <p className="text-sm font-medium">{emp.razon_social}</p>
                <p className="text-xs text-slate-500">NIT: {emp.nit}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant={emp.estado === 'ACTIVA' ? 'default' : 'secondary'}
                  className="text-xs"
                >
                  {emp.estado}
                </Badge>
                <Check className="h-4 w-4 text-green-600" />
              </div>
            </div>
          ))}
        </div>
      )}
      {data && data.length === 0 && dq.length >= 2 && !isLoading && (
        <p className="text-sm text-slate-500 italic">
          No encontrada. Cree la empresa desde el módulo Empresas y luego edite el NIT aquí.
        </p>
      )}
    </div>
  );
}

function EmpleadoSearch({
  currentDoc,
  onSelected,
}: {
  currentDoc: string;
  onSelected: (tipoDoc: string, numero: string, nombres: string) => void;
}) {
  const [q, setQ] = useState('');
  const dq = useDebounce(q, 400);

  const { data, isLoading } = useQuery({
    queryKey: ['empleado-search', dq],
    queryFn: async () => {
      const { data } = await api.get<EmpleadoResult[]>('/empleados/', {
        params: { search: dq, limit: 10 },
      });
      return data;
    },
    enabled: dq.length >= 3,
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <User className="h-4 w-4 text-slate-500" />
        <Label className="font-medium">Empleado</Label>
        {currentDoc && (
          <Badge variant="outline" className="text-xs">
            Doc actual: {currentDoc}
          </Badge>
        )}
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Buscar por documento o nombre..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="pl-9"
        />
      </div>
      {isLoading && <p className="text-sm text-slate-500">Buscando...</p>}
      {data && data.length > 0 && (
        <div className="border rounded-md divide-y max-h-40 overflow-y-auto">
          {data.map((emp) => (
            <div
              key={emp.id}
              className="flex items-center justify-between p-2 hover:bg-slate-50 cursor-pointer"
              onClick={() => {
                onSelected('CC', emp.numero_documento, `${emp.nombres} ${emp.apellidos}`);
                setQ('');
              }}
            >
              <div>
                <p className="text-sm font-medium">
                  {emp.nombres} {emp.apellidos}
                </p>
                <p className="text-xs text-slate-500">Doc: {emp.numero_documento}</p>
              </div>
              <Badge
                variant={emp.estado === 'ACTIVO' ? 'default' : 'secondary'}
                className="text-xs"
              >
                {emp.estado}
              </Badge>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function ResolverEntidadesPanel({ preInc, onEmpresaSelected, onEmpleadoSelected }: Props) {
  const hasEmpresaError = preInc.validation_inconsistencias.some(
    (i) => i.codigo === 'EMPRESA_NOT_FOUND' && i.severidad === 'ERROR'
  );
  const hasEmpleadoError = preInc.validation_inconsistencias.some(
    (i) => i.codigo === 'EMPLEADO_NOT_FOUND' && i.severidad === 'ERROR'
  );

  if (!hasEmpresaError && !hasEmpleadoError) return null;

  return (
    <Card className="p-4 border-orange-200 bg-orange-50 space-y-4">
      <p className="text-sm font-semibold text-orange-800">
        Resolución de entidades requerida
      </p>
      {hasEmpresaError && (
        <EmpresaSearch currentNit={preInc.empresa_nit} onSelected={onEmpresaSelected} />
      )}
      {hasEmpleadoError && (
        <EmpleadoSearch
          currentDoc={preInc.empleado_numero_documento}
          onSelected={onEmpleadoSelected}
        />
      )}
    </Card>
  );
}
