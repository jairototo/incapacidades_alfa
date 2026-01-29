import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TopEmpresaStats } from '@/types/dashboard';

interface TopEmpresasChartProps {
  data: TopEmpresaStats[];
}

export function TopEmpresasChart({ data }: TopEmpresasChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top Empresas por Incapacidades</CardTitle>
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
        <CardTitle>Top Empresas por Incapacidades</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="razon_social"
              angle={-45}
              textAnchor="end"
              height={100}
              className="text-xs"
            />
            <YAxis className="text-xs" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              formatter={(value?: number, name?: string) => {
                const val = value || 0;
                if (name === 'total_incapacidades') return [val, 'Incapacidades'];
                if (name === 'total_dias') return [val, 'Días Totales'];
                if (name === 'total_valor') return [`$${val.toLocaleString('es-CO')}`, 'Valor Total'];
                return [val, name || ''];
              }}
            />
            <Legend />
            <Bar
              dataKey="total_incapacidades"
              fill="hsl(var(--primary))"
              name="Incapacidades"
              radius={[8, 8, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
