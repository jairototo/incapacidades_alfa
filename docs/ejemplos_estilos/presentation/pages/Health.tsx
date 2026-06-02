import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity,
  Building2,
  ClipboardList,
  FileText,
  RefreshCw,
  Users,
} from 'lucide-react';

import { apiClient } from '@/infrastructure/api/client';
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  PageHeader,
  PageLayout,
  Spinner,
} from '@/presentation/components/ui';

interface HealthResponse {
  ok: boolean;
  name: string;
  version: string;
  time: string;
}

interface NavItem {
  to: string;
  label: string;
  description: string;
  icon: typeof Building2;
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/companies',
    label: 'Empresas',
    description: 'Catálogo de empresas afiliadas',
    icon: Building2,
  },
  {
    to: '/workers',
    label: 'Trabajadores',
    description: 'Listado de trabajadores afiliados',
    icon: Users,
  },
  {
    to: '/worker-novelties',
    label: 'Novedades SGRL',
    description: 'Novedades laborales reportadas a ARL',
    icon: ClipboardList,
  },
  {
    to: '/affiliations',
    label: 'Afiliaciones SGRL',
    description: 'Solicitudes de afiliación y novedades formales',
    icon: FileText,
  },
];

export function HealthPage() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await apiClient.get<HealthResponse>('/api/v2/health');
      return response.data;
    },
  });

  return (
    <PageLayout width="default">
      <PageHeader
        title="PORTAL FAAL IMA"
        description="Panel de salud del backend y accesos rápidos."
      />

      <Card className="mb-8">
        <CardHeader
          title="Estado del backend"
          actions={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => refetch()}
              loading={isFetching}
              leftIcon={<RefreshCw size={14} strokeWidth={1.75} aria-hidden />}
            >
              Refrescar
            </Button>
          }
        />
        <CardBody>
          {isLoading ? (
            <Spinner label="Consultando backend..." />
          ) : isError ? (
            <p className="text-red-600">No se pudo contactar al backend.</p>
          ) : data ? (
            <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
              <Field label="Servicio" value={data.name} />
              <Field label="Versión" value={data.version} />
              <Field
                label="Estado"
                value={
                  <Badge variant={data.ok ? 'success' : 'error'}>
                    <Activity size={12} strokeWidth={1.75} className="mr-1" aria-hidden />
                    {data.ok ? 'OK' : 'ERROR'}
                  </Badge>
                }
              />
              <Field label="Hora" value={<span className="font-mono text-xs">{data.time}</span>} />
            </dl>
          ) : null}
        </CardBody>
      </Card>

      <h2 className="mb-3 text-xl font-bold text-brand-900">Módulos</h2>
      <nav className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {NAV_ITEMS.map(({ to, label, description, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className="group rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-all hover:border-brand-500 hover:shadow-md"
          >
            <div className="flex items-start gap-3">
              <div className="rounded-md bg-brand-50 p-2 text-brand-600 group-hover:bg-brand-100">
                <Icon size={20} strokeWidth={1.5} aria-hidden />
              </div>
              <div className="min-w-0">
                <h3 className="font-medium text-brand-900 group-hover:text-brand-700">{label}</h3>
                <p className="mt-0.5 text-sm text-gray-600">{description}</p>
              </div>
            </div>
          </Link>
        ))}
      </nav>
    </PageLayout>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="text-sm">
      <dt className="text-xs uppercase tracking-wide text-gray-500">{label}</dt>
      <dd className="mt-0.5 font-medium text-gray-900">{value}</dd>
    </div>
  );
}

