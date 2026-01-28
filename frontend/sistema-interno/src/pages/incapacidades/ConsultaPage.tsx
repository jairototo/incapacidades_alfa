/**
 * ConsultaPage - Página de consulta de incapacidades
 * Permite buscar y visualizar incapacidades con filtros múltiples
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Eye, FileDown } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/shared/DataTable';
import { ConsultaFilters, type ConsultaFiltros } from '@/components/incapacidades/ConsultaFilters';
import { DetalleModal } from '@/components/incapacidades/DetalleModal';
import { incapacidadService } from '@/services/incapacidadService';
import type { Incapacidad } from '@/types/incapacidad';
import { formatCurrency, formatDate, formatFullName } from '@/utils/formatters';
import { TipoIncapacidad } from '@/types/enums';

/**
 * Obtener variant del badge según el estado
 */
function getEstadoBadgeVariant(estado: string) {
  switch (estado) {
    case 'APROBADA':
    case 'PAGADA':
      return 'default';
    case 'RECHAZADA':
      return 'destructive';
    case 'OBSERVADA':
      return 'outline';
    case 'EN_PAGO':
      return 'secondary';
    default:
      return 'secondary';
  }
}

/**
 * Componente principal de la página de consulta
 */
export function ConsultaPage() {
  const [filtros, setFiltros] = useState<ConsultaFiltros>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  /**
   * Definición de columnas de la tabla
   */
  const columns: ColumnDef<Incapacidad>[] = [
    {
      accessorKey: 'numero',
      header: 'N° Radicación',
      cell: ({ row }) => (
        <span className="font-mono text-sm">{row.original.numero}</span>
      ),
    },
    {
      accessorKey: 'tipo',
      header: 'Tipo',
      cell: ({ row }) => (
        <Badge variant={row.original.tipo === TipoIncapacidad.ARL ? 'default' : 'secondary'}>
          {row.original.tipo}
        </Badge>
      ),
    },
    {
      accessorKey: 'estado',
      header: 'Estado',
      cell: ({ row }) => (
        <Badge variant={getEstadoBadgeVariant(row.original.estado)}>
          {row.original.estado.replace('_', ' ')}
        </Badge>
      ),
    },
    {
      id: 'solicitante',
      header: 'Solicitante',
      cell: ({ row }) => {
        const incap = row.original;
        if (incap.empleado) {
          return (
            <div>
              <p className="font-medium text-sm">
                {formatFullName(incap.empleado.nombres, incap.empleado.apellidos)}
              </p>
              <p className="text-xs text-slate-500">{incap.empleado.numero_documento}</p>
            </div>
          );
        }
        if (incap.afiliado) {
          return (
            <div>
              <p className="font-medium text-sm">
                {formatFullName(incap.afiliado.nombres, incap.afiliado.apellidos)}
              </p>
              <p className="text-xs text-slate-500">{incap.afiliado.numero_documento}</p>
            </div>
          );
        }
        return '-';
      },
    },
    {
      accessorKey: 'empresa',
      header: 'Empresa',
      cell: ({ row }) => row.original.empresa?.razon_social || '-',
    },
    {
      accessorKey: 'fecha_inicio',
      header: 'Fecha Inicio',
      cell: ({ row }) => formatDate(row.original.fecha_inicio),
    },
    {
      accessorKey: 'dias_totales',
      header: 'Días',
      cell: ({ row }) => (
        <span className="font-medium">{row.original.dias_totales}</span>
      ),
    },
    {
      accessorKey: 'valor_total',
      header: 'Valor',
      cell: ({ row }) => (
        <span className="font-medium">{formatCurrency(row.original.valor_total)}</span>
      ),
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            setSelectedId(row.original.id);
            setModalOpen(true);
          }}
        >
          <Eye className="h-4 w-4 mr-2" />
          Ver
        </Button>
      ),
    },
  ];

  // Query para obtener incapacidades
  const { data: incapacidades, isLoading } = useQuery({
    queryKey: ['incapacidades', 'consulta', filtros],
    queryFn: async () => {
      // Convertir filtros a params del service
      const params: any = {
        skip: 0,
        limit: 100,
      };

      if (filtros.numero) params.numero = filtros.numero;
      if (filtros.tipo && filtros.tipo !== 'ALL') params.tipo = filtros.tipo;
      if (filtros.estado && filtros.estado !== 'ALL') params.estado = filtros.estado;
      if (filtros.empleado_documento) params.empleado_documento = filtros.empleado_documento;
      if (filtros.empresa_nit) params.empresa_nit = filtros.empresa_nit;
      if (filtros.fecha_inicio) params.fecha_inicio = filtros.fecha_inicio;
      if (filtros.fecha_fin) params.fecha_fin = filtros.fecha_fin;

      return incapacidadService.list(params);
    },
  });

  const handleSearch = (nuevosFiltros: ConsultaFiltros) => {
    setFiltros(nuevosFiltros);
  };

  const handleDescargarCSV = () => {
    if (!incapacidades || incapacidades.length === 0) return;

    // Generar CSV simple
    const headers = ['Número', 'Tipo', 'Estado', 'Solicitante', 'Empresa', 'Fecha Inicio', 'Días', 'Valor'];
    const rows = incapacidades.map(inc => [
      inc.numero,
      inc.tipo,
      inc.estado,
      inc.empleado 
        ? formatFullName(inc.empleado.nombres, inc.empleado.apellidos)
        : inc.afiliado
        ? formatFullName(inc.afiliado.nombres, inc.afiliado.apellidos)
        : '-',
      inc.empresa?.razon_social || '-',
      formatDate(inc.fecha_inicio),
      inc.dias_totales.toString(),
      inc.valor_total.toString(),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    // Descargar archivo
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `incapacidades_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Consulta de Incapacidades</h1>
          <p className="text-slate-500 mt-1">
            Busque incapacidades por número, documento, empresa o rango de fechas
          </p>
        </div>
        
        {incapacidades && incapacidades.length > 0 && (
          <Button onClick={handleDescargarCSV} variant="outline">
            <FileDown className="h-4 w-4 mr-2" />
            Descargar CSV
          </Button>
        )}
      </div>

      {/* Filtros */}
      <ConsultaFilters onSearch={handleSearch} isLoading={isLoading} />

      {/* Tabla */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold">
            Resultados ({incapacidades?.length || 0})
          </h2>
        </div>
        <div className="p-6">
          <DataTable
            columns={columns}
            data={incapacidades || []}
            isLoading={isLoading}
            emptyMessage="No se encontraron incapacidades con los filtros aplicados"
          />
        </div>
      </div>

      {/* Modal de Detalle */}
      <DetalleModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setSelectedId(null);
        }}
        incapacidadId={selectedId}
      />
    </div>
  );
}
