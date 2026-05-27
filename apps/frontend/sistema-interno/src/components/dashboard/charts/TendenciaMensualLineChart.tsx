import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TendenciaMensual } from '@/types/dashboard';

interface TendenciaMensualLineChartProps {
  data: TendenciaMensual[];
}

const MESES: Record<string, string> = {
  '01': 'Ene',
  '02': 'Feb',
  '03': 'Mar',
  '04': 'Abr',
  '05': 'May',
  '06': 'Jun',
  '07': 'Jul',
  '08': 'Ago',
  '09': 'Sep',
  '10': 'Oct',
  '11': 'Nov',
  '12': 'Dic',
};

export function TendenciaMensualLineChart({ data }: TendenciaMensualLineChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card className="col-span-full">
        <CardHeader>
          <CardTitle>Tendencia Mensual de Incapacidades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            No hay datos disponibles
          </div>
        </CardContent>
      </Card>
    );
  }

  console.log('TendenciaMensualLineChart data:', data);

  const chartData = data.map((item) => {
    // El mes viene en formato "2026-01"
    const [anio, mes] = item.mes.split('-');
    return {
      periodo: `${MESES[mes]} ${anio}`,
      radicadas: item.radicadas,
      aprobadas: item.aprobadas,
      rechazadas: item.rechazadas,
    };
  });

  return (
    <Card className="col-span-full">
      <CardHeader>
        <CardTitle>Tendencia Mensual de Incapacidades</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="periodo" className="text-xs" />
            <YAxis className="text-xs" />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              formatter={(value?: number) => [value || 0, '']}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="radicadas"
              stroke="#9333ea"
              name="Radicadas"
              strokeWidth={2}
              dot={{ fill: '#9333ea', r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="aprobadas"
              stroke="#10b981"
              name="Aprobadas"
              strokeWidth={2}
              dot={{ fill: '#10b981', r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="rechazadas"
              stroke="#ef4444"
              name="Rechazadas"
              strokeWidth={2}
              dot={{ fill: '#ef4444', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
