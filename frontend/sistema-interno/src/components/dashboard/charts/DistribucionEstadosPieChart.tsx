import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { DistribucionEstados } from '@/types/dashboard';

interface DistribucionEstadosPieChartProps {
  data: DistribucionEstados[];
}

const ESTADO_COLORS: Record<string, string> = {
  RADICADA: '#9333ea',
  EN_AUDITORIA: '#f59e0b',
  OBSERVADA: '#ef4444',
  APROBADA: '#10b981',
  RECHAZADA: '#dc2626',
  EN_PAGO: '#3b82f6',
  PAGADA: '#059669',
  ANULADA: '#6b7280',
};

export function DistribucionEstadosPieChart({ data }: DistribucionEstadosPieChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Distribución por Estados</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            No hay datos disponibles
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((item) => ({
    name: item.estado.replace(/_/g, ' '),
    value: item.cantidad,
    porcentaje: item.porcentaje,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Distribución por Estados</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, porcentaje }: any) => `${name}: ${porcentaje}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={ESTADO_COLORS[data[index].estado] || '#6b7280'}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              formatter={(value?: number, name?: string, props?: any) => [
                `${value || 0} (${props?.payload?.porcentaje || 0}%)`,
                name || '',
              ]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
