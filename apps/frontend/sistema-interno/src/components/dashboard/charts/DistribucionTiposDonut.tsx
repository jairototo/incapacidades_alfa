import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { DistribucionTipos } from '@/types/dashboard';

interface DistribucionTiposDonutProps {
  data: DistribucionTipos[];
}

const TIPO_COLORS: Record<string, string> = {
  ARL: '#3b82f6',
  SALUD: '#10b981',
};

export function DistribucionTiposDonut({ data }: DistribucionTiposDonutProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Distribución por Tipo (ARL vs SALUD)</CardTitle>
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
    name: item.tipo,
    value: item.cantidad,
    porcentaje: ((item.cantidad / data.reduce((acc, d) => acc + d.cantidad, 0)) * 100).toFixed(1),
    dias: item.promedio_dias,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Distribución por Tipo (ARL vs SALUD)</CardTitle>
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
              innerRadius={60}
              outerRadius={90}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={TIPO_COLORS[data[index].tipo] || '#6b7280'}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              formatter={(value?: number, name?: string, props?: any) => {
                if (name === 'value') {
                  return [
                    `${value || 0} incapacidades (${props?.payload?.porcentaje || 0}%)`,
                    props?.payload?.name || '',
                  ];
                }
                return [value || 0, name || ''];
              }}
            />
            <Legend
              formatter={(value: string, entry: any) => {
                const item = chartData.find((d) => d.name === entry.payload.name);
                return `${value} - Promedio: ${item?.dias.toFixed(1)} días`;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
