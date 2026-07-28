import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { EmpresaTopItem } from '@/types/empresa';

interface TopEmpresasChartProps {
  data: EmpresaTopItem[];
}

function truncar(nombre: string, max = 22): string {
  return nombre.length > max ? `${nombre.slice(0, max - 1)}…` : nombre;
}

export function TopEmpresasChart({ data }: TopEmpresasChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Top 10 empresas por radicadas</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            No hay datos para mostrar
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map((item) => ({ ...item, nombreCorto: truncar(item.razon_social) }));

  return (
    <Card>
      <CardHeader><CardTitle>Top 10 empresas por radicadas</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis type="number" className="text-xs" tickFormatter={(v) => v.toLocaleString('es-CO')} />
            <YAxis type="category" dataKey="nombreCorto" width={140} className="text-xs" />
            <Tooltip
              contentStyle={{ backgroundColor: 'hsl(var(--background))', border: '1px solid hsl(var(--border))', borderRadius: '6px' }}
              formatter={(value?: number) => [(value ?? 0).toLocaleString('es-CO'), 'Radicadas']}
              labelFormatter={(_, payload) => {
                const item = payload?.[0]?.payload as EmpresaTopItem | undefined;
                return item ? `${item.razon_social} (NIT ${item.nit})` : '';
              }}
            />
            <Bar dataKey="total_radicadas" fill="#9333ea" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
