import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { TopEmpleadoStats } from '@/types/dashboard';

interface TopEmpleadosTableProps {
  data: TopEmpleadoStats[];
}

export function TopEmpleadosTable({ data }: TopEmpleadosTableProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top Empleados con Más Incapacidades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            No hay datos disponibles
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Empleados con Más Incapacidades</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4 font-medium">#</th>
                <th className="text-left py-3 px-4 font-medium">Documento</th>
                <th className="text-left py-3 px-4 font-medium">Nombre</th>
                <th className="text-right py-3 px-4 font-medium">Incapacidades</th>
                <th className="text-right py-3 px-4 font-medium">Días Totales</th>
                <th className="text-left py-3 px-4 font-medium">Empresa</th>
              </tr>
            </thead>
            <tbody>
              {data.map((empleado, index) => (
                <tr
                  key={empleado.empleado_id}
                  className="border-b hover:bg-muted/50 transition-colors"
                >
                  <td className="py-3 px-4">
                    <Badge variant={index < 3 ? 'default' : 'secondary'}>
                      {index + 1}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs">
                    {empleado.numero_documento}
                  </td>
                  <td className="py-3 px-4">
                    {empleado.nombres} {empleado.apellidos}
                  </td>
                  <td className="py-3 px-4 text-right font-semibold">
                    {empleado.total_incapacidades}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <Badge variant="outline">{empleado.total_dias} días</Badge>
                  </td>
                  <td className="py-3 px-4 text-right text-muted-foreground">
                    {empleado.empresa_razon_social}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
