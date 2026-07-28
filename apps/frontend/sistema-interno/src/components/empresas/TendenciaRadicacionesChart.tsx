import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TendenciaMensualItem } from '@/types/empresa';

interface TendenciaRadicacionesChartProps {
  data: TendenciaMensualItem[];
}

const MESES: Record<string, string> = {
  '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr', '05': 'May', '06': 'Jun',
  '07': 'Jul', '08': 'Ago', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic',
};

export function TendenciaRadicacionesChart({ data }: TendenciaRadicacionesChartProps) {
  const hasData = data && data.some((d) => d.total > 0);
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Tendencia mensual de radicaciones</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            No hay datos para mostrar
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((item) => {
    const [anio, mes] = item.periodo.split('-');
    return { periodo: `${MESES[mes]} ${anio}`, total: item.total };
  });

  return (
    <Card>
      <CardHeader><CardTitle>Tendencia mensual de radicaciones</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="periodo" className="text-xs" />
            <YAxis className="text-xs" allowDecimals={false} />
            <Tooltip
              contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))', borderRadius: '6px' }}
              formatter={(value?: number) => [(value ?? 0).toLocaleString('es-CO'), 'Radicaciones']}
            />
            <Line type="monotone" dataKey="total" stroke="#9333ea" strokeWidth={2} dot={{ fill: '#9333ea', r: 4 }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
        {!hasData && (
          <p className="text-xs text-muted-foreground text-center mt-2">Sin radicaciones en los últimos 12 meses</p>
        )}
      </CardContent>
    </Card>
  );
}
