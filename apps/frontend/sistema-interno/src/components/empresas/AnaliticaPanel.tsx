import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { empresaService } from '@/services/empresaService';
import { TopEmpresasChart } from './TopEmpresasChart';
import { TendenciaRadicacionesChart } from './TendenciaRadicacionesChart';

const STORAGE_KEY = 'analitica-empresas-collapsed';

export function AnaliticaPanel() {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(STORAGE_KEY) === 'true');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['empresas-analitica'],
    queryFn: () => empresaService.getAnalitica(),
  });

  const toggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem(STORAGE_KEY, String(next));
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <button
        type="button"
        onClick={toggle}
        className="w-full flex items-center justify-between p-4 text-left"
      >
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Analítica de empresas</h2>
          <p className="text-sm text-slate-500">Top 10 y tendencia de los últimos 12 meses</p>
        </div>
        {collapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
      </button>

      {!collapsed && (
        <div className="p-4 pt-0">
          {isLoading && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Skeleton className="h-[300px] w-full" />
              <Skeleton className="h-[300px] w-full" />
            </div>
          )}
          {isError && !isLoading && (
            <div className="flex flex-col items-center justify-center h-[200px] gap-3 text-muted-foreground">
              <p>No se pudo cargar la analítica.</p>
              <Button variant="outline" size="sm" onClick={() => refetch()}>Reintentar</Button>
            </div>
          )}
          {!isLoading && !isError && data && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <TopEmpresasChart data={data.top_empresas} />
              <TendenciaRadicacionesChart data={data.tendencia_mensual} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
